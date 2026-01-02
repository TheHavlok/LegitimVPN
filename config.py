# config.py — НОВАЯ КОНФИГУРАЦИЯ С 3 ТАРИФАМИ
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Платежи
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
CURRENCY = os.getenv("CURRENCY", "RUB")

# VPN Manager (3X-UI)
VLESS_ADMIN_USERNAME = os.getenv("VLESS_ADMIN_USERNAME", "admin")
VLESS_ADMIN_PASSWORD = os.getenv("VLESS_ADMIN_PASSWORD", "admin")

# ==================== 3 ТАРИФНЫХ ПЛАНА ====================
SUBSCRIPTION_PLANS = {
    "standard_1m": {
        "name": "⚡ STANDARD",
        "emoji": "🥉",
        "price": 299,
        "duration_days": 30,
        "speed": "До 100 Мбит/с",
        "devices": "2 устройства",
        "locations": "3 страны",
        "support": "Email поддержка",
        "description": "Отличный выбор для начала"
    },
    "pro_1m": {
        "name": "🚀 PRO",
        "emoji": "🥈",
        "price": 499,
        "duration_days": 30,
        "speed": "До 500 Мбит/с",
        "devices": "5 устройств",
        "locations": "10 стран",
        "support": "Приоритетная поддержка",
        "description": "Для требовательных пользователей",
        "popular": True  # Значок "Популярно"
    },
    "pro_max_1m": {
        "name": "💎 PRO MAX",
        "emoji": "🥇",
        "price": 899,
        "duration_days": 30,
        "speed": "Безлимитная скорость",
        "devices": "10 устройств",
        "locations": "30+ стран",
        "support": "VIP поддержка 24/7",
        "description": "Максимальная производительность",
        "premium": True
    },
    
    # 3-месячные планы (скидка)
    "standard_3m": {
        "name": "⚡ STANDARD",
        "emoji": "🥉",
        "price": 799,
        "old_price": 897,  # Показываем экономию
        "duration_days": 90,
        "speed": "До 100 Мбит/с",
        "devices": "2 устройства",
        "locations": "3 страны",
        "support": "Email поддержка"
    },
    "pro_3m": {
        "name": "🚀 PRO",
        "emoji": "🥈",
        "price": 1299,
        "old_price": 1497,
        "duration_days": 90,
        "speed": "До 500 Мбит/с",
        "devices": "5 устройств",
        "locations": "10 стран",
        "support": "Приоритетная поддержка",
        "popular": True
    },
    "pro_max_3m": {
        "name": "💎 PRO MAX",
        "emoji": "🥇",
        "price": 2399,
        "old_price": 2697,
        "duration_days": 90,
        "speed": "Безлимитная скорость",
        "devices": "10 устройств",
        "locations": "30+ стран",
        "support": "VIP поддержка 24/7",
        "premium": True
    },
    
    # 12-месячные планы (максимальная скидка)
    "standard_12m": {
        "name": "⚡ STANDARD",
        "emoji": "🥉",
        "price": 2699,
        "old_price": 3588,
        "duration_days": 365,
        "speed": "До 100 Мбит/с",
        "devices": "2 устройства",
        "locations": "3 страны",
        "support": "Email поддержка"
    },
    "pro_12m": {
        "name": "🚀 PRO",
        "emoji": "🥈",
        "price": 4499,
        "old_price": 5988,
        "duration_days": 365,
        "speed": "До 500 Мбит/с",
        "devices": "5 устройств",
        "locations": "10 стран",
        "support": "Приоритетная поддержка",
        "popular": True
    },
    "pro_max_12m": {
        "name": "💎 PRO MAX",
        "emoji": "🥇",
        "price": 7999,
        "old_price": 10788,
        "duration_days": 365,
        "speed": "Безлимитная скорость",
        "devices": "10 устройств",
        "locations": "30+ стран",
        "support": "VIP поддержка 24/7",
        "premium": True
    }
}