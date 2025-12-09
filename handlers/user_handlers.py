from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from database.db import (
    get_user, create_user, get_active_subscription, 
    is_user_banned
)
from keyboards import (
    get_main_menu, get_subscription_plans_keyboard,
    get_subscription_info_keyboard, get_support_keyboard
)
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
    # Проверка на бан
    if await is_user_banned(user.id):
        await message.answer("🚫 Ваш аккаунт заблокирован. Обратитесь в поддержку.")
        return
    
    # Создаем или обновляем пользователя в БД
    await create_user(
        user_id=user.id,
        username=user.username or '',
        first_name=user.first_name or '',
        last_name=user.last_name or ''
    )
    
    # Проверяем наличие активной подписки
    subscription = await get_active_subscription(user.id)
    is_subscribed = subscription is not None
    
    logger.info(f"👤 Пользователь {user.id} (@{user.username}) запустил бота")
    
    welcome_text = (
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        "🔐 Добро пожаловать в VPN бот!\n\n"
        "<b>Что умеет наш бот:</b>\n"
        "✅ Купить VPN подписку любого тарифа\n"
        "✅ Моментальная активация после оплаты\n"
        "✅ Получить конфигурационные файлы\n"
        "✅ Высокая скорость и безопасность\n"
        "✅ Поддержка 24/7\n\n"
    )
    
    if is_subscribed:
        days_left = (subscription['end_date'] - datetime.now()).days
        welcome_text += f"📱 У вас есть активная подписка!\n⏳ Осталось дней: {days_left}\n\n"
    else:
        welcome_text += "💡 <i>Начните с покупки подписки!</i>\n\n"
    
    welcome_text += "Выберите действие в меню ниже 👇"
    
    await message.answer(
        welcome_text,
        parse_mode='HTML',
        reply_markup=get_main_menu(is_subscribed)
    )


@router.message(Command('help'))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 <b>Помощь по использованию бота</b>\n\n"
        "<b>📋 Доступные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/subscription - Информация о подписке\n"
        "/support - Связаться с поддержкой\n\n"
        "<b>🛒 Как купить VPN:</b>\n"
        "1️⃣ Нажмите '💳 Купить подписку'\n"
        "2️⃣ Выберите подходящий тариф\n"
        "3️⃣ Оплатите любым способом\n"
        "4️⃣ Получите конфигурацию сразу после оплаты\n\n"
        "<b>⚙️ Настройка VPN:</b>\n"
        "• Скачайте приложение WireGuard\n"
        "• Импортируйте полученный конфиг\n"
        "• Включите VPN одной кнопкой\n\n"
        "<b>❓ Нужна помощь?</b>\n"
        "Нажмите '💬 Поддержка' в меню или используйте /support"
    )
    
    await message.answer(help_text, parse_mode='HTML')


@router.message(Command('subscription'))
@router.message(F.text == "📱 Моя подписка")
async def cmd_subscription(message: Message):
    """Показать информацию о подписке"""
    subscription = await get_active_subscription(message.from_user.id)
    
    if not subscription:
        await message.answer(
            "❌ <b>У вас нет активной подписки</b>\n\n"
            "Выберите тарифный план и оформите подписку, чтобы начать пользоваться VPN!",
            parse_mode='HTML',
            reply_markup=get_subscription_plans_keyboard()
        )
        return
    
    # Рассчитываем оставшиеся дни
    days_left = (subscription['end_date'] - datetime.now()).days
    hours_left = (subscription['end_date'] - datetime.now()).seconds // 3600
    
    # Определяем эмодзи статуса
    if days_left > 7:
        status_emoji = "✅"
        status_text = "Активна"
    elif days_left > 3:
        status_emoji = "⚠️"
        status_text = "Скоро истечёт"
    else:
        status_emoji = "🔴"
        status_text = "Истекает"
    
    end_date_str = subscription['end_date'].strftime('%d.%m.%Y %H:%M')
    
    subscription_text = (
        f"{status_emoji} <b>Ваша подписка: {status_text}</b>\n\n"
        f"📦 <b>Тариф:</b> {subscription['plan_type']}\n"
        f"📅 <b>Действует до:</b> {end_date_str}\n"
        f"⏳ <b>Осталось:</b> {days_left} дней {hours_left} часов\n"
        f"🆔 <b>ID подписки:</b> <code>{subscription['id']}</code>\n\n"
    )
    
    if days_left <= 3:
        subscription_text += "⚠️ <i>Не забудьте продлить подписку!</i>\n\n"
    
    subscription_text += "Выберите действие:"
    
    await message.answer(
        subscription_text,
        parse_mode='HTML',
        reply_markup=get_subscription_info_keyboard()
    )


@router.message(F.text == "💳 Купить подписку")
@router.callback_query(F.data == "renew_subscription")
async def buy_subscription(event: Message | CallbackQuery):
    """Показать доступные тарифы"""
    plans_text = (
        "💰 <b>Выберите тарифный план VPN</b>\n\n"
        "<b>Все планы включают:</b>\n"
        "✅ Безлимитный трафик\n"
        "✅ Максимальная скорость\n"
        "✅ Защита данных (AES-256)\n"
        "✅ Без логов\n"
        "✅ Поддержка 24/7\n"
        "✅ Серверы в разных странах\n"
        "✅ До 5 устройств одновременно\n\n"
        "🔥 <i>Чем больше срок - тем выгоднее!</i>"
    )
    
    if isinstance(event, Message):
        await event.answer(
            plans_text,
            parse_mode='HTML',
            reply_markup=get_subscription_plans_keyboard()
        )
    else:
        await event.message.edit_text(
            plans_text,
            parse_mode='HTML',
            reply_markup=get_subscription_plans_keyboard()
        )
        await event.answer()


@router.message(F.text == "⚙️ Получить конфиг")
@router.callback_query(F.data == "get_config")
async def get_config(event: Message | CallbackQuery):
    """Отправить конфигурационный файл"""
    user_id = event.from_user.id if isinstance(event, Message) else event.from_user.id
    subscription = await get_active_subscription(user_id)
    
    if not subscription:
        text = "❌ У вас нет активной подписки"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return
    
    # Создаем файл из текста конфигурации
    from io import BytesIO
    config_content = subscription.get('vpn_config', '')
    
    if not config_content:
        text = "❌ Конфигурация не найдена. Обратитесь в поддержку."
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return
    
    config_file = BytesIO(config_content.encode('utf-8'))
    config_file.name = f"vpn_config_{user_id}.conf"
    
    caption = (
        "⚙️ <b>Ваш конфигурационный файл VPN</b>\n\n"
        "📱 <b>Инструкция по подключению:</b>\n\n"
        "1️⃣ Скачайте приложение WireGuard:\n"
        "   • Android: Play Market\n"
        "   • iOS: App Store\n"
        "   • Windows/Mac: wireguard.com\n\n"
        "2️⃣ Откройте приложение\n"
        "3️⃣ Нажмите '+' или 'Импорт'\n"
        "4️⃣ Выберите этот файл\n"
        "5️⃣ Активируйте подключение\n\n"
        "✅ Готово! Вы под защитой VPN\n\n"
        "❓ Проблемы с подключением? /support"
    )
    
    if isinstance(event, Message):
        await event.answer_document(
            document=config_file,
            caption=caption,
            parse_mode='HTML'
        )
    else:
        await event.message.answer_document(
            document=config_file,
            caption=caption,
            parse_mode='HTML'
        )
        await event.answer()


@router.message(F.text == "💬 Поддержка")
@router.message(Command('support'))
async def support(message: Message):
    """Связаться с поддержкой"""
    support_text = (
        "💬 <b>Служба поддержки</b>\n\n"
        "Мы всегда готовы помочь вам!\n\n"
        "<b>Способы связи:</b>\n"
        "📧 Email: support@vpnbot.com\n"
        "💬 Telegram: @vpn_support\n"
        "⏰ Telegram чат: @vpn_chat\n\n"
        "<b>Часы работы:</b>\n"
        "🕐 Круглосуточно, 7 дней в неделю\n"
        "⚡ Средее время ответа: 15 минут\n\n"
        "<b>Частые вопросы:</b>\n"
        "• Как настроить VPN?\n"
        "• Проблемы с подключением\n"
        "• Возврат средств\n"
        "• Смена тарифа\n\n"
        "Нажмите кнопку ниже для связи 👇"
    )
    
    await message.answer(
        support_text,
        parse_mode='HTML',
        reply_markup=get_support_keyboard()
    )


@router.callback_query(F.data == "show_faq")
async def show_faq(callback: CallbackQuery):
    """Показать FAQ"""
    faq_text = (
        "❓ <b>Частые вопросы (FAQ)</b>\n\n"
        "<b>Q: Как настроить VPN?</b>\n"
        "A: Получите конфиг файл и импортируйте его в приложение WireGuard\n\n"
        "<b>Q: На скольких устройствах можно использовать?</b>\n"
        "A: До 5 устройств одновременно\n\n"
        "<b>Q: Какие страны доступны?</b>\n"
        "A: США, Германия, Нидерланды, Сингапур и др.\n\n"
        "<b>Q: Есть ли ограничения скорости?</b>\n"
        "A: Нет, скорость не ограничена\n\n"
        "<b>Q: Можно ли вернуть деньги?</b>\n"
        "A: Да, в течение 7 дней\n\n"
        "<b>Q: Сохраняются ли логи?</b>\n"
        "A: Нет, мы не храним логи активности"
    )
    
    await callback.message.edit_text(
        faq_text,
        parse_mode='HTML',
        reply_markup=get_support_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "show_instructions")
async def show_instructions(callback: CallbackQuery):
    """Показать инструкцию по настройке"""
    instructions = (
        "📖 <b>Подробная инструкция</b>\n\n"
        "<b>🤖 Android:</b>\n"
        "1. Установите WireGuard из Play Market\n"
        "2. Откройте приложение\n"
        "3. Нажмите '+' внизу справа\n"
        "4. Выберите 'Импорт из файла'\n"
        "5. Выберите скачанный .conf файл\n"
        "6. Включите VPN тумблером\n\n"
        "<b>🍎 iOS:</b>\n"
        "1. Установите WireGuard из App Store\n"
        "2. Откройте приложение\n"
        "3. Нажмите '+' вверху справа\n"
        "4. Выберите 'Создать из файла'\n"
        "5. Выберите .conf файл из Telegram\n"
        "6. Активируйте подключение\n\n"
        "<b>💻 Windows/Mac:</b>\n"
        "1. Скачайте WireGuard с wireguard.com\n"
        "2. Установите программу\n"
        "3. Нажмите 'Импортировать'\n"
        "4. Выберите .conf файл\n"
        "5. Нажмите 'Активировать'\n\n"
        "✅ Готово!"
    )
    
    await callback.message.edit_text(
        instructions,
        parse_mode='HTML',
        reply_markup=get_subscription_info_keyboard()
    )
    await callback.answer()


@router.message(F.text == "ℹ️ Информация")
async def info(message: Message):
    """Информация о сервисе"""
    info_text = (
        "ℹ️ <b>О нашем VPN сервисе</b>\n\n"
        "🔒 <b>Безопасность и конфиденциальность</b>\n"
        "• Шифрование AES-256 (военный стандарт)\n"
        "• Протокол WireGuard (самый быстрый)\n"
        "• Строгая политика No-Logs\n"
        "• Kill Switch защита\n"
        "• DNS leak protection\n\n"
        "🌍 <b>География серверов</b>\n"
        "• 50+ стран по всему миру\n"
        "• 1000+ высокоскоростных серверов\n"
        "• Автовыбор лучшего сервера\n"
        "• Пинг от 5ms\n\n"
        "💎 <b>Преимущества</b>\n"
        "• Безлимитный трафик\n"
        "• Неограниченная скорость\n"
        "• До 5 устройств одновременно\n"
        "• Работает со всеми приложениями\n"
        "• Поддержка P2P и торрентов\n"
        "• 99.9% uptime\n\n"
        "🎯 <b>Для чего подходит</b>\n"
        "✅ Обход блокировок сайтов\n"
        "✅ Защита в публичном WiFi\n"
        "✅ Анонимный серфинг\n"
        "✅ Доступ к зарубежным сервисам\n"
        "✅ Безопасные онлайн-платежи\n\n"
        "💰 <b>Гарантии</b>\n"
        "• Возврат средств в течение 7 дней\n"
        "• Техподдержка 24/7\n"
        "• Стабильная работа\n\n"
        "Готовы начать? Нажмите '💳 Купить подписку'"
    )
    
    await message.answer(info_text, parse_mode='HTML')


@router.callback_query(F.data == "cancel")
@router.callback_query(F.data == "back_to_menu")
async def cancel_action(callback: CallbackQuery):
    """Отмена действия"""
    subscription = await get_active_subscription(callback.from_user.id)
    is_subscribed = subscription is not None
    
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu(is_subscribed)
    )
    await callback.answer()