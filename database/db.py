# database/db.py — ИСПРАВЛЕННАЯ ВЕРСИЯ
import aiomysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)
pool = None

async def init_db():
    global pool
    pool = await aiomysql.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        autocommit=True,
        minsize=1,
        maxsize=10
    )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_banned BOOLEAN DEFAULT FALSE
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    plan_type VARCHAR(100),
                    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_date DATETIME NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    vpn_config TEXT,
                    vpn_login VARCHAR(100),
                    vpn_password VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    amount DECIMAL(10,2),
                    currency VARCHAR(10) DEFAULT 'RUB',
                    plan_type VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'pending',
                    payment_id VARCHAR(255) UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS vless_servers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    ip VARCHAR(45) NOT NULL,
                    port INT NOT NULL,
                    secret_path VARCHAR(100) NOT NULL,
                    pbk VARCHAR(44) NOT NULL,
                    sid VARCHAR(16),
                    type ENUM('standard', 'bypass') DEFAULT 'standard',
                    is_active BOOLEAN DEFAULT TRUE,
                    current_load INT DEFAULT 0,
                    max_clients INT DEFAULT 1000,
                    remark VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

async def close_db():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()

# ========== ПОЛЬЗОВАТЕЛИ ==========
async def get_user(user_id: int) -> Optional[Dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            return await cur.fetchone()

async def create_user(user_id: int, username=None, first_name=None, last_name=None):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    username=VALUES(username),
                    first_name=VALUES(first_name),
                    last_name=VALUES(last_name)
            ''', (user_id, username, first_name, last_name))

async def is_user_banned(user_id: int) -> bool:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT is_banned FROM users WHERE user_id = %s", (user_id,))
            result = await cur.fetchone()
            return bool(result[0]) if result else False

async def ban_user(user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET is_banned = TRUE WHERE user_id = %s", (user_id,))

async def unban_user(user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET is_banned = FALSE WHERE user_id = %s", (user_id,))

# ========== ПОДПИСКИ ==========
async def get_active_subscription(user_id: int) -> Optional[Dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('''
                SELECT * FROM subscriptions
                WHERE user_id = %s AND is_active = TRUE AND end_date > NOW()
                ORDER BY end_date DESC LIMIT 1
            ''', (user_id,))
            return await cur.fetchone()

async def create_subscription(user_id: int, plan_type: str, duration_days: int, vpn_config: str,
                            vpn_login: str = None, vpn_password: str = None) -> Dict:
    end_date = datetime.now() + timedelta(days=duration_days)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("UPDATE subscriptions SET is_active = FALSE WHERE user_id = %s AND is_active = TRUE", (user_id,))
            await cur.execute('''
                INSERT INTO subscriptions 
                (user_id, plan_type, end_date, vpn_config, vpn_login, vpn_password)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, plan_type, end_date, vpn_config, vpn_login, vpn_password))
            await cur.execute("SELECT * FROM subscriptions WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
            return await cur.fetchone()

# ========== ПЛАТЕЖИ ==========
async def create_payment(user_id: int, amount: float, currency: str, plan_type: str, payment_id: str):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                INSERT IGNORE INTO payments 
                (user_id, amount, currency, plan_type, payment_id, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            ''', (user_id, amount, currency, plan_type, payment_id))

async def update_payment_status(payment_id: str, status: str):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE payments SET status = %s WHERE payment_id = %s", (status, payment_id))

async def get_payment_by_id(payment_id: str) -> Optional[Dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM payments WHERE payment_id = %s", (payment_id,))
            return await cur.fetchone()

async def get_user_payments(user_id: int) -> List[Dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT * FROM payments 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 20
            """, (user_id,))
            return await cur.fetchall()

# ========== СТАТИСТИКА (ИСПРАВЛЕНО!) ==========
async def get_stats() -> Dict[str, Any]:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Правильный способ получения значений
            await cur.execute("SELECT COUNT(*) FROM users")
            total_users = (await cur.fetchone())[0]
            
            await cur.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = TRUE AND end_date > NOW()")
            active_subs = (await cur.fetchone())[0]
            
            await cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'succeeded'")
            total_revenue = (await cur.fetchone())[0]
            
            today = date.today()
            await cur.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM payments 
                WHERE status = 'succeeded' AND DATE(created_at) = %s
            ''', (today,))
            revenue_today = (await cur.fetchone())[0]
            
            await cur.execute("SELECT COUNT(*) FROM users WHERE DATE(registration_date) = %s", (today,))
            new_today = (await cur.fetchone())[0]
            
            await cur.execute("SELECT COUNT(*) FROM payments WHERE status='succeeded' AND DATE(created_at)=%s", (today,))
            payments_today = (await cur.fetchone())[0]

            return {
                "total_users": total_users or 0,
                "active_subscriptions": active_subs or 0,
                "total_revenue": float(total_revenue or 0),
                "revenue_today": float(revenue_today or 0),
                "new_users_today": new_today or 0,
                "payments_today": payments_today or 0,
            }

async def get_revenue_by_period(days: int) -> List[Dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('''
                SELECT DATE(created_at) as date, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
                FROM payments
                WHERE status = 'succeeded' AND created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''', (days,))
            return await cur.fetchall()

# ========== VLESS СЕРВЕРА ==========
async def get_active_servers(server_type: str = None) -> List[Dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if server_type:
                await cur.execute("SELECT * FROM vless_servers WHERE is_active = TRUE AND type = %s ORDER BY current_load ASC", (server_type,))
            else:
                await cur.execute("SELECT * FROM vless_servers WHERE is_active = TRUE ORDER BY current_load ASC")
            return await cur.fetchall()

async def get_server_by_id(server_id: int) -> Optional[Dict]:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM vless_servers WHERE id = %s", (server_id,))
            return await cur.fetchone()

async def add_vless_server(name: str, ip: str, port: int, secret: str, pbk: str, sid: str | None, server_type: str, max_clients: int = 1000) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO vless_servers (name, ip, port, secret_path, pbk, sid, type, max_clients)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, ip, port, secret, pbk, sid, server_type, max_clients))
            return cur.lastrowid

# ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==========
async def get_user_subscriptions(user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT * FROM subscriptions 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            return await cur.fetchall()

async def get_all_users():
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE NOT is_banned ORDER BY registration_date DESC")
            return await cur.fetchall()

async def search_users(query: str):
    query = f"%{query.strip()}%"
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT * FROM users 
                WHERE CAST(user_id AS CHAR) LIKE %s 
                   OR username LIKE %s 
                   OR first_name LIKE %s 
                   OR last_name LIKE %s
                ORDER BY registration_date DESC
                LIMIT 20
            """, (query, query, query, query))
            return await cur.fetchall()