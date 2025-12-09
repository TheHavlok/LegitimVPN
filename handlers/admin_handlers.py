# handlers/admin_handlers.py — ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ ФАЙЛ

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ПРЯМЫЕ ИМПОРТЫ — БЕЗ __init__.py
from database.db import (
    get_user,
    create_user,
    ban_user,
    unban_user,
    get_stats,
    get_revenue_by_period,
    create_subscription,
    get_active_subscription,
    get_user_payments,
    get_active_servers,
    add_vless_server,
)

# Добавляем недостающие функции ПРЯМО ЗДЕСЬ (чтобы не падало)
import aiomysql
from database.db import pool

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
                WHERE user_id LIKE %s 
                   OR username LIKE %s 
                   OR first_name LIKE %s 
                   OR last_name LIKE %s
                ORDER BY registration_date DESC
                LIMIT 20
            """, (query, query, query, query))
            return await cur.fetchall()

# Теперь импортируем клавиатуры
from keyboards.keyboard import (
    get_admin_menu, get_stats_keyboard, get_users_management_keyboard,
    get_user_actions_keyboard, get_give_subscription_keyboard,
    get_broadcast_confirm_keyboard, get_broadcast_type_keyboard,
    get_finance_keyboard, get_back_keyboard, get_confirm_keyboard,
    get_vless_servers_keyboard
)

from config import ADMIN_IDS, SUBSCRIPTION_PLANS
import logging

router = Router()
logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_broadcast_message = State()
    waiting_user_search = State()
    waiting_user_message = State()


def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь админом"""
    return user_id in ADMIN_IDS


@router.message(Command('admin'))
async def cmd_admin(message: Message):
    """Вход в админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    stats = await get_stats()
    
    welcome_text = (
        "👨‍💼 <b>Админ-панель VPN бота</b>\n\n"
        "📊 <b>Быстрая статистика:</b>\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"✅ Активных подписок: {stats['active_subscriptions']}\n"
        f"💰 Общая выручка: {stats['total_revenue']:.2f} ₽\n"
        f"🆕 Новых за сегодня: {stats['new_users_today']}\n"
        f"💵 Выручка за сегодня: {stats['revenue_today']:.2f} ₽\n\n"
        "Выберите раздел в меню ниже 👇"
    )
    
    await message.answer(
        welcome_text,
        parse_mode='HTML',
        reply_markup=get_admin_menu()
    )
    
    logger.info(f"👨‍💼 Админ {message.from_user.id} зашел в админ-панель")


# ==================== СТАТИСТИКА ====================

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    """Показать подробную статистику"""
    if not is_admin(message.from_user.id):
        return
    
    stats = await get_stats()
    
    stats_text = (
        "📊 <b>Подробная статистика</b>\n\n"
        "👥 <b>Пользователи:</b>\n"
        f"├ Всего: {stats['total_users']}\n"
        f"└ Новых за сегодня: {stats['new_users_today']}\n\n"
        "💳 <b>Подписки:</b>\n"
        f"├ Активных: {stats['active_subscriptions']}\n"
        f"└ Конверсия: {(stats['active_subscriptions']/stats['total_users']*100 if stats['total_users'] > 0 else 0):.1f}%\n\n"
        "💰 <b>Финансы:</b>\n"
        f"├ Общая выручка: {stats['total_revenue']:.2f} ₽\n"
        f"├ За сегодня: {stats['revenue_today']:.2f} ₽\n"
        f"└ Платежей сегодня: {stats['payments_today']}\n\n"
        "📈 Средний чек: "
        f"{(stats['total_revenue']/stats['total_users'] if stats['total_users'] > 0 else 0):.2f} ₽\n\n"
        f"🕐 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await message.answer(
        stats_text,
        parse_mode='HTML',
        reply_markup=get_stats_keyboard()
    )


@router.callback_query(F.data == "stats_today")
async def stats_today(callback: CallbackQuery):
    """Статистика за сегодня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    stats = await get_stats()
    
    text = (
        "📈 <b>Статистика за сегодня</b>\n\n"
        f"🆕 Новых пользователей: {stats['new_users_today']}\n"
        f"💳 Новых подписок: {stats['payments_today']}\n"
        f"💰 Выручка: {stats['revenue_today']:.2f} ₽\n\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y')}"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stats_"))
async def stats_period(callback: CallbackQuery):
    """Статистика за период"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    period = callback.data.split("_")[1]
    days_map = {'week': 7, 'month': 30, 'all': 365}
    days = days_map.get(period, 7)
    
    revenue_data = await get_revenue_by_period(days)
    
    total_revenue = sum(r['total'] for r in revenue_data if r['total'])
    total_count = sum(r['count'] for r in revenue_data)
    
    period_names = {'week': 'неделю', 'month': 'месяц', 'all': 'всё время'}
    period_name = period_names.get(period, 'период')
    
    text = (
        f"📊 <b>Статистика за {period_name}</b>\n\n"
        f"💰 Выручка: {total_revenue:.2f} ₽\n"
        f"💳 Платежей: {total_count}\n"
        f"📈 Средний чек: {(total_revenue/total_count if total_count > 0 else 0):.2f} ₽\n\n"
    )
    
    # Показываем последние 5 дней
    text += "<b>По дням:</b>\n"
    for item in revenue_data[:5]:
        date_str = item['date'].strftime('%d.%m')
        text += f"├ {date_str}: {item['total']:.0f} ₽ ({item['count']} пл.)\n"
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_stats_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "refresh_stats")
async def refresh_stats(callback: CallbackQuery):
    """Обновить статистику"""
    if not is_admin(callback.from_user.id):
        return
    
    await show_statistics(callback.message)
    await callback.answer("✅ Обновлено")


# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================

@router.message(F.text == "👥 Пользователи")
async def manage_users(message: Message):
    """Управление пользователями"""
    if not is_admin(message.from_user.id):
        return
    
    users = await get_all_users()
    
    text = (
        f"👥 <b>Управление пользователями</b>\n\n"
        f"Всего пользователей: {len(users)}\n\n"
        "Выберите действие:"
    )
    
    await message.answer(
        text,
        parse_mode='HTML',
        reply_markup=get_users_management_keyboard()
    )


@router.callback_query(F.data == "search_user")
async def search_user_prompt(callback: CallbackQuery, state: FSMContext):
    """Запрос на поиск пользователя"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите:\n"
        "• User ID\n"
        "• Username (без @)\n"
        "• Имя пользователя\n\n"
        "Или /cancel для отмены",
        parse_mode='HTML'
    )
    
    await state.set_state(AdminStates.waiting_user_search)
    await callback.answer()


@router.message(AdminStates.waiting_user_search)
async def process_user_search(message: Message, state: FSMContext):
    """Обработка поиска пользователя"""
    if not is_admin(message.from_user.id):
        return
    
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Поиск отменен", reply_markup=get_admin_menu())
        return
    
    query = message.text.strip()
    users = await search_users(query)
    
    if not users:
        await message.answer(
            "❌ Пользователи не найдены\n\n"
            "Попробуйте другой запрос или /cancel",
            parse_mode='HTML'
        )
        return
    
    await state.clear()
    
    result_text = f"🔍 <b>Найдено пользователей: {len(users)}</b>\n\n"
    
    for user in users[:10]:  # Показываем первых 10
        username = f"@{user['username']}" if user['username'] else "Без username"
        result_text += (
            f"👤 {user['first_name']} {user['last_name'] or ''}\n"
            f"🆔 ID: <code>{user['user_id']}</code>\n"
            f"📱 {username}\n"
            f"📅 Регистрация: {user['registration_date'].strftime('%d.%m.%Y')}\n\n"
        )
    
    await message.answer(
        result_text,
        parse_mode='HTML',
        reply_markup=get_users_management_keyboard()
    )


@router.callback_query(F.data.startswith("user_actions_"))
async def user_actions(callback: CallbackQuery):
    """Действия с пользователем"""
    if not is_admin(callback.from_user.id):
        return
    
    user_id = int(callback.data.split("_")[2])
    user = await get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    subscriptions = await get_user_subscriptions(user_id)
    active_sub = next((s for s in subscriptions if s['is_active']), None)
    
    username = f"@{user['username']}" if user['username'] else "Без username"
    banned_status = "🚫 Заблокирован" if user.get('is_banned') else "✅ Активен"
    
    text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"👤 Имя: {user['first_name']} {user['last_name'] or ''}\n"
        f"📱 {username}\n"
        f"📅 Регистрация: {user['registration_date'].strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 Статус: {banned_status}\n\n"
        f"💳 <b>Подписки:</b>\n"
    )
    
    if active_sub:
        days_left = (active_sub['end_date'] - datetime.now()).days
        text += (
            f"✅ Активна: {active_sub['plan_type']}\n"
            f"⏳ До: {active_sub['end_date'].strftime('%d.%m.%Y')}\n"
            f"📅 Осталось: {days_left} дней\n"
        )
    else:
        text += "❌ Нет активной подписки\n"
    
    text += f"\n📊 Всего подписок: {len(subscriptions)}"
    
    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_user_actions_keyboard(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("give_sub_"))
async def give_subscription_prompt(callback: CallbackQuery):
    """Выбор подписки для выдачи"""
    if not is_admin(callback.from_user.id):
        return
    
    user_id = int(callback.data.split("_")[2])
    
    await callback.message.edit_text(
        "🎁 <b>Выдать подписку пользователю</b>\n\n"
        "Выберите тариф:",
        parse_mode='HTML',
        reply_markup=get_give_subscription_keyboard(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_give_"))
async def process_give_subscription(callback: CallbackQuery):
    """Выдача подписки пользователю"""
    if not is_admin(callback.from_user.id):
        return
    
    parts = callback.data.split("_")
    plan_id = parts[2]
    user_id = int(parts[3])
    
    if plan_id not in SUBSCRIPTION_PLANS:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    # Генерируем конфиг
    vpn_config = await generate_vpn_config(user_id)
    
    # Создаем подписку
    subscription = await create_subscription(
        user_id=user_id,
        plan_type=f"{plan['name']} (выдан админом)",
        duration_days=plan['duration_days'],
        vpn_config=vpn_config,
        vpn_login=f"admin_user_{user_id}",
        vpn_password="admin_generated"
    )
    
    await callback.message.edit_text(
        f"✅ <b>Подписка выдана!</b>\n\n"
        f"👤 Пользователь: <code>{user_id}</code>\n"
        f"📦 Тариф: {plan['name']}\n"
        f"📅 До: {subscription['end_date'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Конфигурация сгенерирована автоматически",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin_users")
    )
    
    # Уведомляем пользователя
    try:
        from aiogram import Bot
        bot = callback.bot
        await bot.send_message(
            user_id,
            f"🎁 <b>Вам выдана подписка!</b>\n\n"
            f"📦 Тариф: {plan['name']}\n"
            f"📅 Действует до: {subscription['end_date'].strftime('%d.%m.%Y')}\n\n"
            f"Получите конфиг: /subscription",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")
    
    await callback.answer("✅ Подписка выдана!")
    logger.info(f"🎁 Админ {callback.from_user.id} выдал подписку {plan['name']} пользователю {user_id}")


@router.callback_query(F.data.startswith("ban_user_"))
async def ban_user_action(callback: CallbackQuery):
    """Блокировка пользователя"""
    if not is_admin(callback.from_user.id):
        return
    
    user_id = int(callback.data.split("_")[2])
    
    await ban_user(user_id)
    
    await callback.message.edit_text(
        f"🚫 <b>Пользователь заблокирован</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"Пользователь больше не сможет использовать бота",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin_users")
    )
    
    await callback.answer("🚫 Пользователь заблокирован")
    logger.info(f"🚫 Админ {callback.from_user.id} заблокировал пользователя {user_id}")


@router.callback_query(F.data.startswith("unban_user_"))
async def unban_user_action(callback: CallbackQuery):
    """Разблокировка пользователя"""
    if not is_admin(callback.from_user.id):
        return
    
    user_id = int(callback.data.split("_")[2])
    
    await unban_user(user_id)
    
    await callback.message.edit_text(
        f"✅ <b>Пользователь разблокирован</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"Пользователь снова может использовать бота",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin_users")
    )
    
    await callback.answer("✅ Пользователь разблокирован")
    logger.info(f"✅ Админ {callback.from_user.id} разблокировал пользователя {user_id}")


# ==================== РАССЫЛКА ====================

@router.message(F.text == "📢 Рассылка")
async def broadcast_menu(message: Message):
    """Меню рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Выберите тип рассылки:",
        parse_mode='HTML',
        reply_markup=get_broadcast_type_keyboard()
    )


@router.callback_query(F.data == "broadcast_text")
async def broadcast_text_prompt(callback: CallbackQuery, state: FSMContext):
    """Запрос текста для рассылки"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "📝 <b>Текстовая рассылка</b>\n\n"
        "Отправьте текст сообщения для рассылки\n"
        "Можно использовать HTML разметку\n\n"
        "Или /cancel для отмены",
        parse_mode='HTML'
    )
    
    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Обработка сообщения для рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    if message.text == '/cancel':
        await state.clear()
        await message.answer("❌ Рассылка отменена", reply_markup=get_admin_menu())
        return
    
    await state.update_data(broadcast_text=message.text)
    
    # Показываем превью
    await message.answer(
        "📋 <b>Превью сообщения:</b>\n\n" + message.text,
        parse_mode='HTML'
    )
    
    users = await get_all_users()
    
    await message.answer(
        f"📊 <b>Подтверждение рассылки</b>\n\n"
        f"👥 Получателей: {len(users)}\n\n"
        f"Отправить?",
        parse_mode='HTML',
        reply_markup=get_broadcast_confirm_keyboard()
    )


@router.callback_query(F.data.startswith("broadcast_confirm_"))
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка рассылки"""
    if not is_admin(callback.from_user.id):
        return
    
    target = callback.data.split("_")[2]  # all или active
    
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text')
    
    if not broadcast_text:
        await callback.answer("❌ Текст не найден", show_alert=True)
        return
    
    users = await get_all_users()
    
    await callback.message.edit_text(
        "📤 <b>Рассылка запущена...</b>\n\n"
        "⏳ Ожидайте...",
        parse_mode='HTML'
    )
    
    success_count = 0
    failed_count = 0
    
    for user in users:
        try:
            await callback.bot.send_message(
                user['user_id'],
                broadcast_text,
                parse_mode='HTML'
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user['user_id']}: {e}")
            failed_count += 1
    
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📤 Отправлено: {success_count}\n"
        f"❌ Не доставлено: {failed_count}\n"
        f"👥 Всего: {len(users)}",
        parse_mode='HTML',
        reply_markup=get_back_keyboard("admin_back")
    )
    
    await state.clear()
    await callback.answer("✅ Рассылка завершена!")
    logger.info(f"📢 Админ {callback.from_user.id} выполнил рассылку: {success_count}/{len(users)}")


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Рассылка отменена",
        reply_markup=get_back_keyboard("admin_back")
    )
    await callback.answer()


# ==================== ОБЩЕЕ ====================

@router.message(F.text == "🔙 Выйти из админки")
@router.callback_query(F.data == "admin_back")
async def exit_admin(event: Message | CallbackQuery):
    """Выход из админ-панели"""
    if isinstance(event, Message):
        from keyboards import get_main_menu
        await event.answer("👋 Вы вышли из админ-панели", reply_markup=get_main_menu())
    else:
        await event.message.delete()
        await event.answer("👋 Вы вышли из админ-панели")


@router.callback_query(F.data == "admin_users")
async def back_to_users(callback: CallbackQuery):
    """Вернуться к списку пользователей"""
    await manage_users(callback.message)
    await callback.answer()

# ===================================================================
#                  УПРАВЛЕНИЕ VLESS СЕРВЕРАМИ (3X-UI)
# ===================================================================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------------------- Клавиатуры ----------------------

def get_vless_servers_keyboard():
    """Клавиатура в разделе «VLESS Серверы»"""
    kb = [
        [InlineKeyboardButton("Добавить сервер", callback_data="add_vless_server")],
        [InlineKeyboardButton("Обновить список", callback_data="refresh_servers")],
        [InlineKeyboardButton("Назад в админку", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ---------------------- Состояния FSM ----------------------

class AddServerStates(StatesGroup):
    name          = State()   # название сервера
    ip            = State()   # IP
    port          = State()   # порт панели
    secret        = State()   # secret path (например /abc123)
    pbk           = State()   # public key (44 символа)
    sid           = State()   # short id (можно пусто)
    server_type   = State()   # standard / bypass
    max_clients   = State()   # лимит клиентов


# ---------------------- Главное меню серверов ----------------------

@router.message(F.text == "VLESS Серверы")
async def show_vless_servers(message: Message):
    """Показать список всех активных серверов"""
    if not is_admin(message.from_user.id):
        return

    servers = await get_active_servers()          # ← функция из database/__init__.py
    if not servers:
        text = "Добавленных серверов пока нет.\nНажмите кнопку ниже, чтобы добавить первый!"
    else:
        text = "<b>Активные VLESS-серверы</b>\n\n"
        for s in servers:
            emoji = "Обычный" if s['type'] == 'standard' else "Обход"
            text += (
                f"{emoji} <b>{s['name']}</b> (ID: <code>{s['id']}</code>)\n"
                f"└ IP: <code>{s['ip']}:{s['port']}</code>\n"
                f"└ Клиентов: {s['current_load']}/{s['max_clients']}\n\n"
            )

    await message.answer(text, parse_mode="HTML", reply_markup=get_vless_servers_keyboard())


# ---------------------- Кнопка «Обновить список» ----------------------

@router.callback_query(F.data == "refresh_servers")
async def refresh_servers(callback: CallbackQuery):
    await show_vless_servers(callback.message)
    await callback.answer("Список обновлён")


# ---------------------- Добавление нового сервера ----------------------

@router.callback_query(F.data == "add_vless_server")
async def start_add_server(callback: CallbackQuery, state: FSMContext):
    """Начать процесс добавления сервера"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "Добавление нового VLESS-сервера\n\n"
        "<b>Шаг 1 из 8</b>\n"
        "Введите название сервера (для себя, например: Москва Reality):",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("servers_back")
    )
    await state.set_state(AddServerStates.name)
    await callback.answer()


# 1. Название
@router.message(AddServerStates.name)
async def step_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Шаг 2/8\nВведите IP-адрес сервера (пример: 185.123.45.67):")
    await state.set_state(AddServerStates.ip)


# 2. IP
@router.message(AddServerStates.ip)
async def step_ip(message: Message, state: FSMContext):
    ip = message.text.strip()
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        await message.answer("Неверный IP! Попробуйте ещё раз:")
        return
    await state.update_data(ip=ip)
    await message.answer("Шаг 3/8\nВведите порт панели 3x-ui (обычно 2053 или 54321):")
    await state.set_state(AddServerStates.port)


# 3. Порт
@router.message(AddServerStates.port)
async def step_port(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 65535):
        await message.answer("Порт должен быть числом от 1 до 65535!")
        return
    await state.update_data(port=int(message.text))
    await message.answer("Шаг 4/8\nВведите секретный путь (пример: mysecret123):")
    await state.set_state(AddServerStates.secret)


# 4. Secret path
@router.message(AddServerStates.secret)
async def step_secret(message: Message, state: FSMContext):
    secret = message.text.strip()
    if len(secret) < 3:
        await message.answer("Секрет слишком короткий!")
        return
    await state.update_data(secret_path=secret)
    await message.answer("Шаг 5/8\nВведите Public Key (pbk) — ровно 44 символа base64:")
    await state.set_state(AddServerStates.pbk)


# 5. Public Key (pbk)
@router.message(AddServerStates.pbk)
async def step_pbk(message: Message, state: FSMContext):
    pbk = message.text.strip()
    if len(pbk) != 44 or not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in pbk):
        await message.answer("Неверный pbk! Должно быть ровно 44 символа base64.")
        return
    await state.update_data(pbk=pbk)
    await message.answer("Шаг 6/8\nВведите Short ID (sid) — до 16 символов (можно оставить пустым):")
    await state.set_state(AddServerStates.sid)


# 6. Short ID (можно пусто)
@router.message(AddServerStates.sid)
async def step_sid(message: Message, state: FSMContext):
    sid = message.text.strip()
    if len(sid) > 16:
        await message.answer("SID слишком длинный! Максимум 16 символов.")
        return
    await state.update_data(sid=sid or None)

    # Выбор типа сервера
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Обычная подписка", callback_data="srv_type_standard")],
        [InlineKeyboardButton("Обход белых списков", callback_data="srv_type_bypass")],
        [InlineKeyboardButton("Назад", callback_data="servers_back")]
    ])
    await message.answer("Шаг 7/8\nВыберите тип сервера:", reply_markup=kb)
    await state.set_state(AddServerStates.server_type)


# 7. Тип сервера
@router.callback_query(F.data.startswith("srv_type_"))
async def step_type(callback: CallbackQuery, state: FSMContext):
    stype = "standard" if "standard" in callback.data else "bypass"
    await state.update_data(type=stype)
    await callback.message.edit_text(
        "Шаг 8/8\nВведите максимальное количество клиентов (по умолчанию 1000):",
        reply_markup=get_back_keyboard("servers_back")
    )
    await state.set_state(AddServerStates.max_clients)
    await callback.answer()


# 8. Максимум клиентов → финал
@router.message(AddServerStates.max_clients)
async def step_max_clients(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 10:
        await message.answer("Минимум 10 клиентов!")
        return

    data = await state.get_data()
    data["max_clients"] = int(message.text)

    # Сохраняем в базу
    server_id = await add_vless_server(
        name=data["name"],
        ip=data["ip"],
        port=data["port"],
        secret=data["secret_path"],
        pbk=data["pbk"],
        sid=data["sid"],
        server_type=data["type"],
        max_clients=data["max_clients"]
    )

    type_name = "Обычный" if data["type"] == "standard" else "Обход белых списков"

    await message.answer(
        f"Сервер успешно добавлен!\n\n"
        f"ID: <code>{server_id}</code>\n"
        f"Название: {data['name']}\n"
        f"Тип: {type_name}\n"
        f"IP: {data['ip']}:{data['port']}\n"
        f"Макс. клиентов: {data['max_clients']}",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("admin_back")
    )
    await state.clear()


# ---------------------- Кнопка «Назад» при добавлении ----------------------

@router.callback_query(F.data == "servers_back")
async def back_from_adding_server(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_vless_servers(callback.message)
    await callback.answer()