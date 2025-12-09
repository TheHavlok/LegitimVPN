# utils/vless_manager.py
import aiohttp
import uuid
import logging
import os
from dotenv import load_dotenv
from database.db import get_active_servers, get_server_by_id
from typing import Optional, Dict

load_dotenv()
logger = logging.getLogger(__name__)

ADMIN_USER = os.getenv("VLESS_ADMIN_USERNAME")
ADMIN_PASS = os.getenv("VLESS_ADMIN_PASSWORD")

async def login(session: aiohttp.ClientSession, server: Dict) -> Optional[str]:
    url = f"http://{server['ip']}:{server['port']}/{server['secret_path']}/login"
    data = {"username": ADMIN_USER, "password": ADMIN_PASS}
    try:
        async with session.post(url, data=data, timeout=10) as resp:
            text = await resp.text()
            if "success" in text.lower():
                cookie = resp.headers.get("Set-Cookie")
                if cookie:
                    return cookie.split(";")[0].split("=")[1]
    except Exception as e:
        logger.error(f"Login failed for {server['name']}: {e}")
    return None

async def create_vless_user(server_type: str = "standard") -> Optional[Dict]:
    servers = await get_active_servers(server_type)
    if not servers:
        return None

    # Выбираем наименее загруженный
    server = min(servers, key=lambda x: x['current_load'])

    async with aiohttp.ClientSession() as session:
        cookie = await login(session, server)
        if not cookie:
            return None

        user_uuid = str(uuid.uuid4())
        email = f"user_{user_uuid[:8]}"

        url = f"http://{server['ip']}:{server['port']}/{server['secret_path']}/panel/api/inbounds/addClient"
        headers = {
            "Cookie": f"session={cookie}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "id": 1,
            "settings": json.dumps({
                "clients": [{
                    "id": user_uuid,
                    "flow": "xtls-rprx-vision",
                    "email": email,
                    "limitIp": 5,
                    "totalGB": 0,
                    "expiryTime": 0,
                    "enable": True,
                    "tgId": "",
                    "subId": "",
                    "reset": 0
                }]
            })
        }

        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    # Обновляем нагрузку
                    from database.db import pool
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("UPDATE vless_servers SET current_load = current_load + 1 WHERE id = %s", (server['id'],))
                            await conn.commit()

                    config = f"vless://{user_uuid}@{server['ip']}:{server['port']}?security=reality&encryption=none&pbk={server['pbk']}&headerType=none&fp=randomized&type=tcp&flow=xtls-rprx-vision&sni=yahoo.com&sid={server['sid'] or ''}#VPNBot-{email}"

                    return {
                        "config": config,
                        "uuid": user_uuid,
                        "email": email,
                        "server_id": server['id'],
                        "server_name": server['name']
                    }
        except Exception as e:
            logger.error(f"Failed to create user on {server['name']}: {e}")
    return None

async def delete_vless_user(uuid: str, server_id: int):
    server = await get_server_by_id(server_id)
    if not server:
        return False

    async with aiohttp.ClientSession() as session:
        cookie = await login(session, server)
        if not cookie:
            return False

        url = f"http://{server['ip']}:{server['port']}/{server['secret_path']}/panel/api/inbounds/1/delClient/{uuid}"
        headers = {"Cookie": f"session={cookie}"}

        try:
            async with session.post(url, headers=headers) as resp:
                if resp.status == 200:
                    # Уменьшаем нагрузку
                    from database.db import pool
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("UPDATE vless_servers SET current_load = GREATEST(current_load - 1, 0) WHERE id = %s", (server_id,))
                            await conn.commit()
                    return True
        except:
            pass
    return False