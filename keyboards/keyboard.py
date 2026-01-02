# keyboards/keyboard.py — ПОЛНОСТЬЮ INLINE ДИЗАЙН
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUBSCRIPTION_PLANS


# ==================== ГЛАВНОЕ МЕНЮ (INLINE) ====================

def get_main_menu(is_subscribed: bool = False):
    """Главное меню с красивыми иконками"""
    buttons = []
    
    if is_subscribed:
        buttons.append([InlineKeyboardButton(text="📱 Моя подписка", callback_data="my_subscription")])
        buttons.append([InlineKeyboardButton(text="⚙️ Получить конфиг", callback_data="get_config")])
    else:
        buttons.append([InlineKeyboardButton(text="🔥 Купить VPN", callback_data="buy_vpn")])
    
    buttons.extend([
        [
            InlineKeyboardButton(text="ℹ️ О сервисе", callback_data="about"),
            InlineKeyboardButton(text="💬 Поддержка", callback_data="support")
        ],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instructions")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== ТАРИФНЫЕ ПЛАНЫ (ПРЕМИУМ ДИЗАЙН) ====================

def get_subscription_plans_keyboard(period: str = "1m"):
    """
    Выбор тарифа по периодам
    period: "1m", "3m", "12m"
    """
    buttons = []
    
    # Переключатели периодов
    period_buttons = []
    for p, label in [("1m", "1 месяц"), ("3m", "3 месяца"), ("12m", "1 год")]:
        text = f"{'✅' if p == period else '⚪'} {label}"
        period_buttons.append(InlineKeyboardButton(text=text, callback_data=f"period_{p}"))
    buttons.append(period_buttons)
    
    buttons.append([InlineKeyboardButton(text="━━━━━━━━━━━━━━━", callback_data="separator")])
    
    # Отображаем тарифы для выбранного периода
    for plan_id, plan_data in SUBSCRIPTION_PLANS.items():
        if not plan_id.endswith(period):
            continue
        
        # Формируем красивое название
        name = plan_data['name']
        price = plan_data['price']
        
        # Значки для тарифов
        badge = ""
        if plan_data.get('popular'):
            badge = " 🔥"
        elif plan_data.get('premium'):
            badge = " ⭐"
        
        # Экономия для длительных подписок
        if 'old_price' in plan_data:
            discount = plan_data['old_price'] - price
            text = f"{name} — {price} ₽ (−{discount} ₽){badge}"
        else:
            text = f"{name} — {price} ₽{badge}"
        
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"plan_{plan_id}")])
    
    buttons.append([InlineKeyboardButton(text="━━━━━━━━━━━━━━━", callback_data="separator")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_plan_details_keyboard(plan_id: str):
    """Детальная информация о тарифе"""
    buttons = [
        [InlineKeyboardButton(text="💳 Купить сейчас", callback_data=f"buy_{plan_id}")],
        [InlineKeyboardButton(text="🔄 Выбрать другой тариф", callback_data="change_plan")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== ОПЛАТА ====================

def get_payment_keyboard(payment_url: str, payment_id: str):
    """Кнопки для оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить онлайн", url=payment_url)],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
        ]
    )
    return keyboard


# ==================== МОЯ ПОДПИСКА ====================

def get_subscription_info_keyboard():
    """Управление активной подпиской"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Скачать конфиг", callback_data="get_config")],
            [InlineKeyboardButton(text="🔄 Продлить", callback_data="renew_subscription")],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="sub_stats"),
                InlineKeyboardButton(text="📖 Помощь", callback_data="instructions")
            ],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
        ]
    )
    return keyboard


# ==================== ПОДДЕРЖКА ====================

def get_support_keyboard():
    """Контакты поддержки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать в Telegram", url="https://t.me/your_support")],
            [InlineKeyboardButton(text="📧 Email: support@vpn.com", callback_data="email_support")],
            [InlineKeyboardButton(text="❓ FAQ", callback_data="show_faq")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )
    return keyboard


def get_faq_keyboard():
    """Часто задаваемые вопросы"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔧 Как настроить?", callback_data="faq_setup")],
            [InlineKeyboardButton(text="📱 Какие устройства?", callback_data="faq_devices")],
            [InlineKeyboardButton(text="🌍 Какие страны?", callback_data="faq_locations")],
            [InlineKeyboardButton(text="💰 Возврат средств", callback_data="faq_refund")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="support")]
        ]
    )
    return keyboard


# ==================== АДМИН ПАНЕЛЬ ====================

def get_admin_menu():
    """Админ-панель inline"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton(text="🖥 VLESS Серверы", callback_data="admin_servers"),
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="💰 Финансы", callback_data="admin_finance"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
            ],
            [InlineKeyboardButton(text="🔙 Выйти", callback_data="exit_admin")]
        ]
    )
    return keyboard


def get_stats_keyboard():
    """Статистика админ"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Сегодня", callback_data="stats_today"),
                InlineKeyboardButton(text="📅 Неделя", callback_data="stats_week")
            ],
            [
                InlineKeyboardButton(text="📆 Месяц", callback_data="stats_month"),
                InlineKeyboardButton(text="📊 Всё время", callback_data="stats_all")
            ],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ]
    )
    return keyboard


def get_users_management_keyboard(page: int = 0):
    """Управление пользователями"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Найти", callback_data="search_user")],
            [
                InlineKeyboardButton(text="✅ Активные", callback_data="users_active"),
                InlineKeyboardButton(text="🚫 Забанены", callback_data="users_banned")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ]
    )
    return keyboard


def get_user_actions_keyboard(user_id: int):
    """Действия с пользователем"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Инфо", callback_data=f"user_info_{user_id}")],
            [InlineKeyboardButton(text="🎁 Дать подписку", callback_data=f"give_sub_{user_id}")],
            [
                InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_user_{user_id}"),
                InlineKeyboardButton(text="✅ Разбан", callback_data=f"unban_user_{user_id}")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
        ]
    )
    return keyboard


def get_give_subscription_keyboard(user_id: int):
    """Выбор подписки для выдачи админом"""
    buttons = []
    
    # Показываем только месячные тарифы для выдачи
    for plan_id in ['standard_1m', 'pro_1m', 'pro_max_1m']:
        plan = SUBSCRIPTION_PLANS[plan_id]
        buttons.append([InlineKeyboardButton(
            text=f"{plan['name']} (30 дней)",
            callback_data=f"admin_give_{plan_id}_{user_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"user_info_{user_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_type_keyboard():
    """Тип рассылки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Текст", callback_data="broadcast_text")],
            [InlineKeyboardButton(text="🖼 С фото", callback_data="broadcast_photo")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ]
    )
    return keyboard


def get_broadcast_confirm_keyboard():
    """Подтверждение рассылки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить всем", callback_data="broadcast_confirm_all")],
            [InlineKeyboardButton(text="👥 Только активным", callback_data="broadcast_confirm_active")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
        ]
    )
    return keyboard


def get_vless_servers_keyboard():
    """Управление VLESS серверами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить сервер", callback_data="add_vless_server")],
            [InlineKeyboardButton(text="📋 Список серверов", callback_data="list_servers")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_servers")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ]
    )
    return keyboard


def get_finance_keyboard():
    """Финансы"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Все", callback_data="payments_all"),
                InlineKeyboardButton(text="✅ Успешные", callback_data="payments_success")
            ],
            [
                InlineKeyboardButton(text="⏳ Ожидают", callback_data="payments_pending"),
                InlineKeyboardButton(text="❌ Отменённые", callback_data="payments_failed")
            ],
            [InlineKeyboardButton(text="📊 Экспорт", callback_data="export_payments")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ]
    )
    return keyboard


def get_back_keyboard(callback_data: str = "back_to_main"):
    """Универсальная кнопка назад"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
        ]
    )
    return keyboard


def get_confirm_keyboard(action: str, data: str = ""):
    """Подтверждение действия"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{data}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
            ]
        ]
    )
    return keyboard