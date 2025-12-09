import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))

# Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_NAME = os.getenv('DB_NAME', 'vpn_bot')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

DATABASE_URL = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# VPN Settings
VPN_API_URL = os.getenv('VPN_API_URL', 'http://localhost:8080')
VPN_API_KEY = os.getenv('VPN_API_KEY', '')

# Payment Settings
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN', '')
CURRENCY = 'RUB'

# Subscription Plans
SUBSCRIPTION_PLANS = {
    '1_month': {
        'name': '1 месяц',
        'price': 299,
        'duration_days': 30
    },
    '3_months': {
        'name': '3 месяца',
        'price': 799,
        'duration_days': 90
    },
    '6_months': {
        'name': '6 месяцев',
        'price': 1499,
        'duration_days': 180
    },
    '12_months': {
        'name': '12 месяцев',
        'price': 2499,
        'duration_days': 365
    }
}

# Scheduler Settings
CHECK_SUBSCRIPTIONS_INTERVAL = 3600  # Проверка подписок каждый час
NOTIFICATION_DAYS_BEFORE = [7, 3, 1]  # Уведомления за N дней до окончания