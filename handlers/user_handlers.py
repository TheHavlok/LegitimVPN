# handlers/user_handlers.py — НОВЫЙ ПРЕМИУМ ДИЗАЙН
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from database.db import (
    get_user, create_user, get_active_subscription, is_user_banned
)
from keyboards.keyboard import (
    get_main_menu, get_subscription_plans_keyboard, get_plan_details_keyboard,
    get_subscription_info_keyboard, get_support_keyboard, get_faq_keyboard,
    get_back_keyboard
)
from config import SUBSCRIPTION_PLANS
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Стартовое сообщение с премиум дизайном"""
    user = message.from_user
    
    if await is_user_banned(user.id):
        await message.answer("🚫 Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return
    
    await create_user(
        user_id=user.id,
        username=user.username or '',
        first_name=user.first_name or '',
        last_name=user.last_name or ''
    )
    
    subscription = await get_active_subscription(user.id)
    is_subscribed = subscription is not None
    
    logger.info(f"👤 {user.id} (@{user.username}) запустил бота")
    
    welcome_text = (
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🔐 <b>LegitimVPN</b> — Твоя анонимность под защитой\n"
        "━━━━━━━━━━━━━━━\n\n"
        "<b>✨ Почему выбирают нас:</b>\n"
        "🚀 Скорость до 1 Гбит/с\n"
        "🌍 30+ стран и 200+ серверов\n"
        "🛡️ Военное шифрование (AES-256)\n"
        "🔒 Строгая политика No-Logs\n"
        "⚡ Моментальная активация\n"
        "💎 Поддержка 24/7\n\n"
    )
    
    if is_subscribed:
        days_left = (subscription['end_date'] - datetime.now()).days
        plan_emoji = "⚡" if "STANDARD" in subscription['plan_type'] else "🚀" if "PRO" in subscription['plan_type'] and "MAX" not in subscription['plan_type'] else "💎"
        welcome_text += (
            f"{plan_emoji} <b>Ваша подписка активна</b>\n"
            f"⏳ Осталось: <b>{days_left} дней</b>\n\n"
        )
    else:
        welcome_text += "💡 <i>Начни с выбора тарифа!</i>\n\n"
    
    welcome_text += "Выбери действие в меню ниже 👇"
    
    await message.answer(
        welcome_text,
        parse_mode='HTML',
        reply_markup=get_main_menu(is_subscribed)
    )


# ==================== НАВИГАЦИЯ ====================

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    subscription = await get_active_subscription(callback.from_user.id)
    is_subscribed = subscription is not None
    
    welcome_text = (
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=get_main_menu(is_subscribed)
    )
    await callback.answer()


# ==================== ПОКУПКА VPN ====================

@router.callback_query(F.data == "buy_vpn")
@router.callback_query(F.data == "change_plan")
@router.callback_query(F.data == "renew_subscription")
async def show_plans(callback: CallbackQuery):
    """Показать тарифные планы"""
    plans_text = (
        "💰 <b>Выберите тарифный план</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🥉 <b>STANDARD</b> — для начинающих\n"
        "🥈 <b>PRO</b> — для продвинутых 🔥\n"
        "🥇 <b>PRO MAX</b> — максимум возможностей\n"
        "━━━━━━━━━━━━━━━\n\n"
        "<i>💡 Чем дольше срок — тем больше экономия!</i>"
    )
    
    await callback.message.edit_text(
        plans_text,
        parse_mode='HTML',
        reply_markup=get_subscription_plans_keyboard("1m")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("period_"))
async def change_period(callback: CallbackQuery):
    """Переключение между периодами"""
    period = callback.data.split("_")[1]
    
    period_names = {"1m": "1 месяц", "3m": "3 месяца", "12m": "1 год"}
    
    plans_text = (
        f"💰 <b>Тарифы на {period_names[period]}</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🥉 <b>STANDARD</b> — для начинающих\n"
        "🥈 <b>PRO</b> — для продвинутых 🔥\n"
        "🥇 <b>PRO MAX</b> — максимум возможностей\n"
        "━━━━━━━━━━━━━━━\n\n"
    )
    
    if period in ["3m", "12m"]:
        plans_text += "<b>🔥 Экономия до 30%!</b>\n\n"
    
    await callback.message.edit_text(
        plans_text,
        parse_mode='HTML',
        reply_markup=get_subscription_plans_keyboard(period)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("plan_"))
async def show_plan_details(callback: CallbackQuery):
    """Детали выбранного тарифа"""
    plan_id = callback.data.split("_", 1)[1]
    
    if plan_id not in SUBSCRIPTION_PLANS:
        await callback.answer("Ошибка: тариф не найден", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    # Формируем красивое описание
    details = (
        f"{plan['emoji']} <b>{plan['name']}</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        f"💰 <b>Цена:</b> {plan['price']} ₽"
    )
    
    if 'old_price' in plan:
        discount = plan['old_price'] - plan['price']
        details += f" <s>{plan['old_price']} ₽</s>\n💎 <b>Экономия: {discount} ₽</b>\n"
    else:
        details += "\n"
    
    details += (
        f"📅 <b>Период:</b> {plan['duration_days']} дней\n"
        "━━━━━━━━━━━━━━━\n\n"
        "<b>✨ Что входит:</b>\n"
        f"🚀 {plan['speed']}\n"
        f"📱 {plan['devices']}\n"
        f"🌍 {plan['locations']}\n"
        f"💬 {plan['support']}\n\n"
    )
    
    if plan.get('popular'):
        details += "🔥 <b>ПОПУЛЯРНЫЙ ВЫБОР</b>\n\n"
    elif plan.get('premium'):
        details += "⭐ <b>ПРЕМИУМ ТАРИФ</b>\n\n"
    
    details += f"<i>{plan.get('description', '')}</i>"
    
    await callback.message.edit_text(
        details,
        parse_mode='HTML',
        reply_markup=get_plan_details_keyboard(plan_id)
    )
    await callback.answer()


# ==================== МОЯ ПОДПИСКА ====================

@router.callback_query(F.data == "my_subscription")
async def show_subscription(callback: CallbackQuery):
    """Информация о текущей подписке"""
    subscription = await get_active_subscription(callback.from_user.id)
    
    if not subscription:
        await callback.message.edit_text(
            "❌ <b>У вас нет активной подписки</b>\n\n"
            "Выберите тарифный план!",
            parse_mode='HTML',
            reply_markup=get_subscription_plans_keyboard("1m")
        )
        await callback.answer()
        return
    
    days_left = (subscription['end_date'] - datetime.now()).days
    hours_left = (subscription['end_date'] - datetime.now()).seconds // 3600
    
    # Определяем статус и эмодзи
    if days_left > 7:
        status_emoji = "✅"
        status_text = "Активна"
        status_color = "🟢"
    elif days_left > 3:
        status_emoji = "⚠️"
        status_text = "Скоро истечёт"
        status_color = "🟡"
    else:
        status_emoji = "🔴"
        status_text = "Истекает!"
        status_color = "🔴"
    
    # Определяем тип подписки
    plan_emoji = "⚡" if "STANDARD" in subscription['plan_type'] else "🚀" if "PRO" in subscription['plan_type'] and "MAX" not in subscription['plan_type'] else "💎"
    
    end_date_str = subscription['end_date'].strftime('%d.%m.%Y %H:%M')
    
    sub_text = (
        f"{status_emoji} <b>Статус: {status_text}</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        f"{plan_emoji} <b>Тариф:</b> {subscription['plan_type']}\n"
        f"{status_color} <b>До:</b> {end_date_str}\n"
        f"⏳ <b>Осталось:</b> {days_left} дн. {hours_left} ч.\n"
        f"🆔 <b>ID:</b> <code>{subscription['id']}</code>\n"
        "━━━━━━━━━━━━━━━\n\n"
    )
    
    if days_left <= 3:
        sub_text += "⚠️ <b>Не забудьте продлить подписку!</b>\n\n"
    
    sub_text += "Выберите действие:"
    
    await callback.message.edit_text(
        sub_text,
        parse_mode='HTML',
        reply_markup=get_subscription_info_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "get_config")
async def send_config(callback: CallbackQuery):
    """Отправка конфигурационного файла"""
    subscription = await get_active_subscription(callback.from_user.id)
    
    if not subscription:
        await callback.answer("❌ У вас нет активной подписки", show_alert=True)
        return
    
    config_content = subscription.get('vpn_config', '')
    
    if not config_content:
        await callback.answer("❌ Конфигурация не найдена. Обратитесь в поддержку.", show_alert=True)
        return
    
    # Создаём файл
    config_file = BufferedInputFile(
        config_content.encode('utf-8'),
        filename=f"legitimvpn_{callback.from_user.id}.txt"
    )
    
    caption = (
        "⚙️ <b>Ваш конфигурационный файл</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📱 <b>Инструкция:</b>\n\n"
        "<b>Android:</b>\n"
        "1️⃣ Скачайте Nekobox или v2rayNG\n"
        "2️⃣ Импортируйте этот файл\n"
        "3️⃣ Подключайтесь!\n\n"
        "<b>iOS:</b>\n"
        "1️⃣ Скачайте Streisand\n"
        "2️⃣ Импортируйте конфиг\n"
        "3️⃣ Наслаждайтесь!\n\n"
        "❓ Нужна помощь? /support"
    )
    
    await callback.message.answer_document(
        document=config_file,
        caption=caption,
        parse_mode='HTML'
    )
    await callback.answer("✅ Конфиг отправлен!")


# ==================== О СЕРВИСЕ ====================

@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery):
    """Информация о сервисе"""
    about_text = (
        "ℹ️ <b>О LegitimVPN</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🔐 <b>Безопасность</b>\n"
        "• Шифрование AES-256\n"
        "• Протокол VLESS Reality\n"
        "• Политика No-Logs\n"
        "• DNS leak защита\n\n"
        "🌍 <b>География</b>\n"
        "• 30+ стран\n"
        "• 200+ серверов\n"
        "• Пинг от 5ms\n"
        "• 99.9% uptime\n\n"
        "💎 <b>Преимущества</b>\n"
        "• Безлимитный трафик\n"
        "• До 1 Гбит/с скорость\n"
        "• Работает везде\n"
        "• Поддержка 24/7\n\n"
        "🎯 <b>Для чего:</b>\n"
        "✅ Обход блокировок\n"
        "✅ Защита в WiFi\n"
        "✅ Анонимность\n"
        "✅ Зарубежные сервисы\n"
        "━━━━━━━━━━━━━━━\n\n"
        "Готовы начать? 🚀"
    )
    
    await callback.message.edit_text(
        about_text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_main")
    )
    await callback.answer()


# ==================== ПОДДЕРЖКА ====================

@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    """Контакты поддержки"""
    support_text = (
        "💬 <b>Служба поддержки</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "Мы всегда готовы помочь!\n\n"
        "<b>Способы связи:</b>\n"
        "📧 Email: support@legitimvpn.com\n"
        "💬 Telegram: @legitimvpn_support\n"
        "⏰ Работаем: 24/7\n"
        "⚡ Ответ: до 15 минут\n"
        "━━━━━━━━━━━━━━━\n\n"
        "Выберите удобный способ связи 👇"
    )
    
    await callback.message.edit_text(
        support_text,
        parse_mode='HTML',
        reply_markup=get_support_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "show_faq")
async def show_faq(callback: CallbackQuery):
    """FAQ"""
    await callback.message.edit_text(
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "Выберите интересующий раздел:",
        parse_mode='HTML',
        reply_markup=get_faq_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    """Ответы на FAQ"""
    faq_type = callback.data.split("_")[1]
    
    answers = {
        "setup": (
            "🔧 <b>Как настроить VPN?</b>\n\n"
            "1. Купите подписку\n"
            "2. Получите конфиг-файл\n"
            "3. Скачайте приложение (Nekobox/v2rayNG)\n"
            "4. Импортируйте конфиг\n"
            "5. Подключайтесь!\n\n"
            "Подробная инструкция: /instructions"
        ),
        "devices": (
            "📱 <b>Поддерживаемые устройства</b>\n\n"
            "✅ Android 5.0+\n"
            "✅ iOS 12.0+\n"
            "✅ Windows 10+\n"
            "✅ macOS 10.14+\n"
            "✅ Linux\n\n"
            "Количество зависит от тарифа:\n"
            "⚡ STANDARD: 2 устройства\n"
            "🚀 PRO: 5 устройств\n"
            "💎 PRO MAX: 10 устройств"
        ),
        "locations": (
            "🌍 <b>Доступные страны</b>\n\n"
            "⚡ STANDARD (3 страны):\n"
            "🇩🇪 Германия, 🇳🇱 Нидерланды, 🇺🇸 США\n\n"
            "🚀 PRO (10 стран):\n"
            "+ 🇬🇧 UK, 🇫🇷 Франция, 🇸🇪 Швеция,\n"
            "🇨🇭 Швейцария, 🇯🇵 Япония,\n"
            "🇸🇬 Сингапур, 🇨🇦 Канада\n\n"
            "💎 PRO MAX (30+ стран):\n"
            "Весь мир! 🌎"
        ),
        "refund": (
            "💰 <b>Возврат средств</b>\n\n"
            "✅ Гарантия возврата 7 дней\n\n"
            "Условия:\n"
            "• Не более 1 ГБ использовано\n"
            "• В течение 7 дней с покупки\n"
            "• При технических проблемах\n\n"
            "Для возврата напишите в поддержку."
        )
    }
    
    await callback.message.edit_text(
        answers.get(faq_type, "Информация не найдена"),
        parse_mode='HTML',
        reply_markup=get_faq_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "instructions")
async def show_instructions(callback: CallbackQuery):
    """Подробные инструкции"""
    instructions = (
        "📖 <b>Инструкция по подключению</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "<b>🤖 Android:</b>\n"
        "1. Play Market → Nekobox\n"
        "2. Открыть приложение\n"
        "3. '+' → 'Import from file'\n"
        "4. Выбрать .txt файл\n"
        "5. Подключиться\n\n"
        "<b>🍎 iOS:</b>\n"
        "1. App Store → Streisand\n"
        "2. Открыть приложение\n"
        "3. '+' → Import\n"
        "4. Выбрать конфиг\n"
        "5. Активировать\n\n"
        "<b>💻 Windows:</b>\n"
        "1. Скачать v2rayN\n"
        "2. Импорт конфига\n"
        "3. Подключение\n"
        "━━━━━━━━━━━━━━━\n\n"
        "❓ Проблемы? Напишите в поддержку!"
    )
    
    await callback.message.edit_text(
        instructions,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_main")
    )
    await callback.answer()


# ==================== СТАТИСТИКА ПОДПИСКИ ====================

@router.callback_query(F.data == "sub_stats")
async def show_sub_stats(callback: CallbackQuery):
    """Статистика использования (заглушка для будущего)"""
    stats_text = (
        "📊 <b>Статистика использования</b>\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📈 Трафик: ∞ (безлимит)\n"
        "⏱ Время подключения: 247 ч.\n"
        "🌍 Серверов использовано: 5\n"
        "📱 Устройств: 3 из 5\n"
        "━━━━━━━━━━━━━━━\n\n"
        "<i>Данные обновляются раз в час</i>"
    )
    
    await callback.message.edit_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=get_subscription_info_keyboard()
    )
    await callback.answer()


# ==================== КОМАНДЫ ====================

@router.message(Command('help'))
async def cmd_help(message: Message):
    """Справка"""
    help_text = (
        "📖 <b>Справка по боту</b>\n\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/support - Поддержка\n\n"
        "Используйте кнопки для навигации!"
    )
    await message.answer(help_text, parse_mode='HTML')


@router.message(Command('support'))
async def cmd_support(message: Message):
    """Команда поддержки"""
    await message.answer(
        "💬 Напишите нам: @legitimvpn_support\n"
        "Или используйте кнопки в меню!"
    )