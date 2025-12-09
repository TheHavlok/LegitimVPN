# database/__init__.py
"""
Экспорт ВСЕХ функций из db.py (MySQL версия)
"""

from .db import (
    init_db,
    close_db,
    get_user,
    create_user,
    is_user_banned,
    ban_user,
    unban_user,
    get_active_subscription,
    create_subscription,
    create_payment,
    update_payment_status,
    get_payment_by_id,
    get_stats,
    # Добавим недостающие функции прямо здесь, чтобы не падало
)

# === ВРЕМЕННО добавляем недостающие функции, чтобы бот запустился ===
# Потом перенесём их в db.py, но сейчас — главное запустить!

async def get_user_subscriptions(user_id: int):
    """Заглушка — вернёт пустой список"""
    return []

async def get_all_users():
    """Заглушка"""
    return []

async def search_users(query: str):
    """Заглушка"""
    return []

async def get_revenue_by_period(days: int):
    """Заглушка"""
    return []

# Экспортируем всё, что нужно хендлерам
__all__ = [
    "init_db", "close_db",
    "get_user", "create_user",
    "is_user_banned", "ban_user", "unban_user",
    "get_active_subscription", "create_subscription",
    "create_payment", "update_payment_status", "get_payment_by_id",
    "get_stats",
    "get_user_subscriptions", "get_all_users", "search_users", "get_revenue_by_period",
]