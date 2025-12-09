# keyboards/__init__.py
"""
Экспорт всех клавиатур, чтобы можно было писать:
from keyboards import get_main_menu, get_payment_keyboard и т.д.
"""

from .keyboard import (
    get_main_menu,
    get_subscription_plans_keyboard,
    get_payment_keyboard,
    get_subscription_info_keyboard,
    get_support_keyboard,
    get_admin_menu,
    get_stats_keyboard,
    get_users_management_keyboard,
    get_user_actions_keyboard,
    get_give_subscription_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_type_keyboard,
    get_finance_keyboard,
    get_settings_keyboard,
    get_confirm_keyboard,
    get_back_keyboard,
)

__all__ = [
    "get_main_menu",
    "get_subscription_plans_keyboard",
    "get_payment_keyboard",
    "get_subscription_info_keyboard",
    "get_support_keyboard",
    "get_admin_menu",
    "get_stats_keyboard",
    "get_users_management_keyboard",
    "get_user_actions_keyboard",
    "get_give_subscription_keyboard",
    "get_broadcast_confirm_keyboard",
    "get_broadcast_type_keyboard",
    "get_finance_keyboard",
    "get_settings_keyboard",
    "get_confirm_keyboard",
    "get_back_keyboard",
]