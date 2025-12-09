import uuid
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    create_payment, update_payment_status, get_payment_by_id,
    create_subscription, get_active_subscription
)
from keyboards import get_payment_keyboard, get_main_menu
from config import SUBSCRIPTION_PLANS, PAYMENT_PROVIDER_TOKEN, CURRENCY
from utils.vpn_manager import generate_vpn_config
import logging

router = Router()
logger = logging.getLogger(__name__)


class PaymentStates(StatesGroup):
    waiting_payment = State()


@router.callback_query(F.data.startswith("plan_"))
async def process_plan_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора тарифного плана"""
    plan_id = callback.data.split("_", 1)[1]
    
    if plan_id not in SUBSCRIPTION_PLANS:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    user_id = callback.from_user.id
    
    # Проверяем активную подписку
    active_sub = await get_active_subscription(user_id)
    if active_sub:
        days_left = (active_sub['end_date'] - datetime.now()).days
        await callback.answer(
            f"⚠️ У вас уже есть активная подписка!\nОсталось дней: {days_left}",
            show_alert=True
        )
        return
    
    # Генерируем уникальный ID платежа
    payment_id = f"pay_{user_id}_{int(datetime.now().timestamp())}"
    
    # Сохраняем информацию о платеже
    await state.update_data(
        plan_id=plan_id,
        plan_type=plan['name'],
        amount=plan['price'],
        duration_days=plan['duration_days'],
        payment_id=payment_id
    )
    
    # Создаем запись о платеже в БД
    await create_payment(
        user_id=user_id,
        amount=plan['price'],
        currency=CURRENCY,
        plan_type=plan['name'],
        payment_id=payment_id
    )
    
    # Формируем информацию о заказе
    order_info = (
        f"📦 <b>Ваш заказ</b>\n\n"
        f"🎯 Тариф: {plan['name']}\n"
        f"📅 Срок: {plan['duration_days']} дней\n"
        f"💰 Стоимость: {plan['price']} {CURRENCY}\n\n"
        f"🆔 ID заказа: <code>{payment_id}</code>\n\n"
        f"<b>Что входит:</b>\n"
        f"✅ Безлимитный трафик\n"
        f"✅ Высокая скорость\n"
        f"✅ Защита данных\n"
        f"✅ До 5 устройств\n"
        f"✅ Серверы в разных странах\n\n"
        f"Нажмите кнопку ниже для оплаты 👇"
    )
    
    # В реальном боте здесь должна быть интеграция с платежной системой
    # Например, YooKassa, Stripe и т.д.
    # Для примера создаем фиктивную ссылку на оплату
    payment_url = f"https://payment.example.com/pay/{payment_id}"
    
    await callback.message.edit_text(
        order_info,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(payment_url, payment_id)
    )
    
    await state.set_state(PaymentStates.waiting_payment)
    await callback.answer()
    
    logger.info(f"💳 Пользователь {user_id} выбрал план {plan['name']}, создан платеж {payment_id}")


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery, state: FSMContext):
    """Проверка статуса платежа"""
    payment_id = callback.data.replace("check_payment_", "")
    user_id = callback.from_user.id
    
    # Получаем информацию о платеже
    payment = await get_payment_by_id(payment_id)
    
    if not payment:
        await callback.answer("❌ Платеж не найден", show_alert=True)
        return
    
    if payment['user_id'] != user_id:
        await callback.answer("❌ Это не ваш платеж", show_alert=True)
        return
    
    # Проверяем статус платежа
    # В реальном боте здесь должна быть проверка через API платежной системы
    # Для примера имитируем успешную оплату
    
    if payment['status'] == 'succeeded':
        await callback.answer("✅ Платеж уже обработан!", show_alert=True)
        return
    
    # Имитация проверки оплаты (в реальности здесь API запрос)
    # payment_status = await check_payment_status_api(payment_id)
    
    # Для демонстрации считаем платеж успешным
    payment_status = 'succeeded'
    
    if payment_status == 'succeeded':
        # Обновляем статус платежа
        await update_payment_status(payment_id, 'succeeded')
        
        # Получаем данные из state
        data = await state.get_data()
        duration_days = data.get('duration_days', 30)
        plan_type = data.get('plan_type', '1 месяц')
        
        # Генерируем VPN конфигурацию
        vpn_config = await generate_vpn_config(user_id)
        
        # Создаем подписку
        subscription = await create_subscription(
            user_id=user_id,
            plan_type=plan_type,
            duration_days=duration_days,
            vpn_config=vpn_config,
            vpn_login=f"user_{user_id}",
            vpn_password=str(uuid.uuid4())[:16]
        )
        
        # Отправляем конфигурацию
        from io import BytesIO
        config_file = BytesIO(vpn_config.encode('utf-8'))
        config_file.name = f"vpn_config_{user_id}.conf"
        
        success_text = (
            "🎉 <b>Оплата прошла успешно!</b>\n\n"
            "✅ Подписка активирована\n"
            f"📅 Действует до: {subscription['end_date'].strftime('%d.%m.%Y %H:%M')}\n\n"
            "📎 Ваш конфигурационный файл прикреплен ниже\n\n"
            "📱 <b>Следующий шаг:</b>\n"
            "1. Скачайте WireGuard\n"
            "2. Импортируйте конфиг файл\n"
            "3. Включите VPN\n\n"
            "Подробная инструкция: /help"
        )
        
        await callback.message.delete()
        await callback.message.answer(
            success_text,
            parse_mode='HTML',
            reply_markup=get_main_menu(is_subscribed=True)
        )
        
        await callback.message.answer_document(
            document=config_file,
            caption="⚙️ Ваш VPN конфиг файл"
        )
        
        await state.clear()
        await callback.answer("✅ Подписка активирована!", show_alert=True)
        
        logger.info(f"✅ Платеж {payment_id} успешно обработан, подписка создана для {user_id}")
        
    elif payment_status == 'pending':
        await callback.answer(
            "⏳ Платеж в обработке\nПопробуйте проверить через минуту",
            show_alert=True
        )
    else:
        await callback.answer(
            "❌ Платеж не найден или отклонен\nСвяжитесь с поддержкой",
            show_alert=True
        )


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отмена платежа"""
    data = await state.get_data()
    payment_id = data.get('payment_id')
    
    if payment_id:
        await update_payment_status(payment_id, 'cancelled')
        logger.info(f"❌ Платеж {payment_id} отменен пользователем")
    
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Оплата отменена\n\nВы можете выбрать тариф снова в любое время",
        reply_markup=get_main_menu(is_subscribed=False)
    )
    await callback.answer()


# ==================== TELEGRAM PAYMENTS (альтернативный вариант) ====================

@router.callback_query(F.data.startswith("plan_telegram_"))
async def process_telegram_payment(callback: CallbackQuery):
    """Обработка оплаты через Telegram Payments"""
    plan_id = callback.data.replace("plan_telegram_", "")
    
    if plan_id not in SUBSCRIPTION_PLANS:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    # Создаем инвойс для Telegram Payments
    prices = [LabeledPrice(label=plan['name'], amount=plan['price'] * 100)]  # Цена в копейках
    
    await callback.message.answer_invoice(
        title=f"VPN подписка - {plan['name']}",
        description=f"Подписка на {plan['duration_days']} дней\n"
                   f"✅ Безлимитный трафик\n"
                   f"✅ Высокая скорость\n"
                   f"✅ До 5 устройств",
        payload=f"vpn_sub_{plan_id}_{callback.from_user.id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=prices,
        start_parameter="vpn-subscription",
        photo_url="https://example.com/vpn-logo.png",
        photo_size=512,
        photo_width=512,
        photo_height=512,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )
    
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обработка pre-checkout запроса"""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Обработка успешного платежа через Telegram Payments"""
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    
    # Парсим payload
    parts = payload.split("_")
    plan_id = parts[2]
    user_id = int(parts[3])
    
    if plan_id not in SUBSCRIPTION_PLANS:
        await message.answer("❌ Ошибка обработки платежа")
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    # Создаем запись о платеже
    payment_id = payment_info.telegram_payment_charge_id
    await create_payment(
        user_id=user_id,
        amount=payment_info.total_amount / 100,
        currency=payment_info.currency,
        plan_type=plan['name'],
        payment_id=payment_id
    )
    
    await update_payment_status(payment_id, 'succeeded')
    
    # Генерируем VPN конфигурацию
    vpn_config = await generate_vpn_config(user_id)
    
    # Создаем подписку
    subscription = await create_subscription(
        user_id=user_id,
        plan_type=plan['name'],
        duration_days=plan['duration_days'],
        vpn_config=vpn_config,
        vpn_login=f"user_{user_id}",
        vpn_password=str(uuid.uuid4())[:16]
    )
    
    # Отправляем конфигурацию
    from io import BytesIO
    config_file = BytesIO(vpn_config.encode('utf-8'))
    config_file.name = f"vpn_config_{user_id}.conf"
    
    success_text = (
        "🎉 <b>Спасибо за покупку!</b>\n\n"
        "✅ Ваша подписка активирована\n"
        f"📦 Тариф: {plan['name']}\n"
        f"📅 Действует до: {subscription['end_date'].strftime('%d.%m.%Y %H:%M')}\n\n"
        "📎 Конфигурационный файл прикреплен ниже\n\n"
        "Инструкция по настройке: /help"
    )
    
    await message.answer(
        success_text,
        parse_mode='HTML',
        reply_markup=get_main_menu(is_subscribed=True)
    )
    
    await message.answer_document(
        document=config_file,
        caption="⚙️ Ваш VPN конфиг файл"
    )
    
    logger.info(f"✅ Telegram Payment успешно обработан для пользователя {user_id}")


@router.message(F.text == "💰 История платежей")
async def payment_history(message: Message):
    """История платежей пользователя"""
    from database.db import get_user_payments
    
    payments = await get_user_payments(message.from_user.id)
    
    if not payments:
        await message.answer("📝 У вас пока нет платежей")
        return
    
    history_text = "💰 <b>История ваших платежей</b>\n\n"
    
    for payment in payments[:10]:  # Показываем последние 10
        status_emoji = {
            'succeeded': '✅',
            'pending': '⏳',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(payment['status'], '❓')
        
        date_str = payment['created_at'].strftime('%d.%m.%Y %H:%M')
        
        history_text += (
            f"{status_emoji} {payment['plan_type']}\n"
            f"💵 {payment['amount']} {payment['currency']}\n"
            f"📅 {date_str}\n"
            f"🆔 <code>{payment['payment_id']}</code>\n\n"
        )
    
    await message.answer(history_text, parse_mode='HTML')