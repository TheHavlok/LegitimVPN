from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from config import SUBSCRIPTION_PLANS


# ==================== ПОЛЬЗОВАТЕЛЬСКИЕ КЛАВИАТУРЫ ====================

def get_main_menu(is_subscribed: bool = False):
    """Главное меню пользователя"""
    buttons = [
        [KeyboardButton(text="📱 Моя подписка")],
    ]
    
    if is_subscribed:
        buttons.append([KeyboardButton(text="⚙️ Получить конфиг")])
    else:
        buttons.append([KeyboardButton(text="💳 Купить подписку")])
    
    buttons.extend([
        [
            KeyboardButton(text="💬 Поддержка"),
            KeyboardButton(text="ℹ️ Информация")
        ]
    ])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def get_subscription_plans_keyboard():
    """Клавиатура с тарифными планами"""
    buttons = []
    
    for plan_id, plan_data in SUBSCRIPTION_PLANS.items():
        discount_text = ""
        if plan_id in ['6_months', '12_months']:
            discount_text = " 🔥"
        
        button = InlineKeyboardButton(
            text=f"{plan_data['name']} - {plan_data['price']} ₽{discount_text}",
            callback_data=f"plan_{plan_id}"
        )
        buttons.append([button])
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_keyboard(payment_url: str, payment_id: str):
    """Клавиатура с кнопкой оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
        ]
    )
    return keyboard


def get_subscription_info_keyboard():
    """Клавиатура управления подпиской"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Получить конфиг", callback_data="get_config")],
            [InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="renew_subscription")],
            [InlineKeyboardButton(text="📖 Инструкция", callback_data="show_instructions")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )
    return keyboard


def get_support_keyboard():
    """Клавиатура поддержки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать в поддержку", url="https://t.me/support")],
            [InlineKeyboardButton(text="❓ FAQ", callback_data="show_faq")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )
    return keyboard


# ==================== АДМИНСКИЕ КЛАВИАТУРЫ ====================

def get_admin_menu():
    """Главное меню администратора"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                [KeyboardButton(text="VLESS Серверы")],
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="👥 Пользователи")
            ],
            [
                KeyboardButton(text="📢 Рассылка"),
                KeyboardButton(text="💰 Финансы")
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
                KeyboardButton(text="🔙 Выйти из админки")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_stats_keyboard():
    """Клавиатура статистики"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 За сегодня", callback_data="stats_today"),
                InlineKeyboardButton(text="📅 За неделю", callback_data="stats_week")
            ],
            [
                InlineKeyboardButton(text="📆 За месяц", callback_data="stats_month"),
                InlineKeyboardButton(text="📊 За всё время", callback_data="stats_all")
            ],
            [InlineKeyboardButton(text="💰 График доходов", callback_data="revenue_chart")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_users_management_keyboard(page: int = 0):
    """Клавиатура управления пользователями"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="search_user")],
            [
                InlineKeyboardButton(text="📋 Список активных", callback_data="users_active"),
                InlineKeyboardButton(text="🚫 Заблокированные", callback_data="users_banned")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"users_page_{max(0, page-1)}"),
                InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"users_page_{page+1}")
            ],
            [InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_user_actions_keyboard(user_id: int):
    """Клавиатура действий с пользователем"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data=f"user_stats_{user_id}")],
            [InlineKeyboardButton(text="🎁 Дать подписку", callback_data=f"give_sub_{user_id}")],
            [
                InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"ban_user_{user_id}"),
                InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"unban_user_{user_id}")
            ],
            [InlineKeyboardButton(text="💌 Отправить сообщение", callback_data=f"send_msg_{user_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
        ]
    )
    return keyboard


def get_give_subscription_keyboard(user_id: int):
    """Клавиатура выбора подписки для выдачи"""
    buttons = []
    
    for plan_id, plan_data in SUBSCRIPTION_PLANS.items():
        button = InlineKeyboardButton(
            text=f"{plan_data['name']} ({plan_data['duration_days']} дней)",
            callback_data=f"admin_give_{plan_id}_{user_id}"
        )
        buttons.append([button])
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"user_actions_{user_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_confirm_keyboard():
    """Клавиатура подтверждения рассылки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить всем", callback_data="broadcast_confirm_all"),
                InlineKeyboardButton(text="👥 Только активным", callback_data="broadcast_confirm_active")
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
        ]
    )
    return keyboard


def get_broadcast_type_keyboard():
    """Клавиатура выбора типа рассылки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Текстовое сообщение", callback_data="broadcast_text")],
            [InlineKeyboardButton(text="🖼 С изображением", callback_data="broadcast_photo")],
            [InlineKeyboardButton(text="🎬 С видео", callback_data="broadcast_video")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_finance_keyboard():
    """Клавиатура финансов"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Все платежи", callback_data="payments_all"),
                InlineKeyboardButton(text="✅ Успешные", callback_data="payments_success")
            ],
            [
                InlineKeyboardButton(text="⏳ Ожидают оплаты", callback_data="payments_pending"),
                InlineKeyboardButton(text="❌ Отклоненные", callback_data="payments_failed")
            ],
            [InlineKeyboardButton(text="📊 Экспорт в Excel", callback_data="export_payments")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_settings_keyboard():
    """Клавиатура настроек"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Настройки платежей", callback_data="settings_payment")],
            [InlineKeyboardButton(text="🔐 Настройки VPN", callback_data="settings_vpn")],
            [InlineKeyboardButton(text="📢 Настройки рассылок", callback_data="settings_broadcast")],
            [InlineKeyboardButton(text="🎨 Тексты и кнопки", callback_data="settings_texts")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_confirm_keyboard(action: str, data: str = ""):
    """Универсальная клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{data}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
            ]
        ]
    )
    return keyboard


def get_back_keyboard(callback_data: str = "admin_back"):
    """Клавиатура с кнопкой назад"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
        ]
    )
    return keyboard

# === Добавь это в конец файла keyboards/keyboard.py ===

def get_vless_servers_keyboard():
    """Клавиатура для раздела VLESS Серверы"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("Добавить сервер", callback_data="add_vless_server"),
        ],
        [
            InlineKeyboardButton("Обновить список", callback_data="refresh_servers"),
            InlineKeyboardButton("Назад", callback_data="admin_back")
        ]
    ])
    return keyboard