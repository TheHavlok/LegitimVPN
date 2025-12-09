# config.py
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

# Планы подписки
SUBSCRIPTION_PLANS = {
    "1_month": {"name": "1 месяц", "price": 299, "duration_days": 30},
    "3_months": {"name": "3 месяца", "price": 749, "duration_days": 90},
    "6_months": {"name": "6 месяцев", "price": 1299, "duration_days": 180},
    "12_months": {"name": "12 месяцев", "price": 2199, "duration_days": 365},
}