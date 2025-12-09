# handlers/subscription_handlers.py

import uuid
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Прямые импорты — без __init__.py
from database.db import (
    create_payment, update_payment_status, get_payment_by_id,
    create_subscription, get_active_subscription, get_user_payments
)
from keyboards.keyboard import get_payment_keyboard, get_main_menu
from config import SUBSCRIPTION_PLANS, PAYMENT_PROVIDER_TOKEN, CURRENCY

# VLESS вместо старого WireGuard
from utils.vpn_manager import create_vless_user

import logging
from io import BytesIO

router = Router()
logger = logging.getLogger(__name__)


class PaymentStates(StatesGroup):
    waiting_payment = State()


@router.callback_query(F.data.startswith("plan_"))
async def process_plan_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора тарифного плана"""
    plan_id = callback.data.split("_", 1)[1]
    
    if plan_id not in SUBSCRIPTION_PLANS:
        await callback.answer("Неверный тариф", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    user_id = callback.from_user.id
    
    # Проверяем активную подписку
    active_sub = await get_active_subscription(user_id)
    if active_sub:
        days_left = (active_sub['end_date'] - datetime.now()).days
        await callback.answer(
            f"У вас уже есть активная подписка!\nОсталось дней: {days_left}",
            show_alert=True
        )
        return
    
    # Генерируем уникальный ID платежа
    payment_id = f"pay_{user_id}_{int(datetime.now().timestamp())}"
    
    # Сохраняем в state
    await state.update_data(
        plan_id=plan_id,
        plan_type=plan['name'],
        amount=plan['price'],
        duration_days=plan['duration_days'],
        payment_id=payment_id
    )
    
    # Создаём запись о платеже
    await create_payment(
        user_id=user_id,
        amount=plan['price'],
        currency=CURRENCY,
        plan_type=plan['name'],
        payment_id=payment_id
    )
    
    order_info = (
        f"<b>Ваш заказ</b>\n\n"
        f"Тариф: {plan['name']}\n"
        f"Срок: {plan['duration_days']} дней\n"
        f"Стоимость: {plan['price']} {CURRENCY}\n\n"
        f"ID заказа: <code>{payment_id}</code>\n\n"
        f"<b>Что входит:</b>\n"
        f"Безлимитный трафик\n"
        f"Максимальная скорость\n"
        f"До 5 устройств\n"
        f"Поддержка 24/7\n\n"
        f"Нажмите кнопку ниже для оплаты"
    )
    
    payment_url = f"https://payment.example.com/pay/{payment_id}"  # Замени на реальный URL при интеграции
    
    await callback.message.edit_text(
        order_info,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard(payment_url, payment_id)
    )
    
    await state.set_state(PaymentStates.waiting_payment)
    await callback.answer()
    logger.info(f"Пользователь {user_id} выбрал тариф {plan['name']}")


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery, state: FSMContext):
    """Проверка статуса платежа (фиктивная — в реальности подключи YooKassa/Stripe)"""
    payment_id = callback.data.replace("check_payment_", "")
    user_id = callback.from_user.id
    
    payment = await get_payment_by_id(payment_id)
    if not payment or payment['user_id'] != user_id:
        await callback.answer("Платёж не найден", show_alert=True)
        return
    
    if payment['status'] == 'succeeded':
        await callback.answer("Платёж уже обработан!", show_alert=True)
        return
    
    # === Имитация успешной оплаты ===
    payment_status = 'succeeded'  # В реальности — запрос к платёжной системе
    
    if payment_status == 'succeeded':
        await update_payment_status(payment_id, 'succeeded')
        data = await state.get_data()
        plan_type = data.get('plan_type', 'Подписка')
        duration_days = data.get('duration_days', 30)
        
        # Генерируем VLESS конфиг
        vless_result = await create_vless_user(server_type="standard")
        if not vless_result:
            await callback.message.answer("Серверы временно недоступны. Попробуйте позже.")
            await callback.answer()
            return
        
        vpn_config = vless_result["config"]
        email = vless_result["email"]
        
        # Создаём подписку
        subscription = await create_subscription(
            user_id=user_id,
            plan_type=plan_type,
            duration_days=duration_days,
            vpn_config=vpn_config,
            vpn_login=email,
            vpn_password=vless_result["uuid"][:16]
        )
        
        # Отправляем конфиг
        config_file = BytesIO(vpn_config.encode('utf-8'))
        config_file.name = f"vless_config_{user_id}.txt"
        
        success_text = (
            f"<b>Оплата прошла успешно!</b>\n\n"
            f"Подписка активирована\n"
            f"Тариф: {plan_type}\n"
            f"Действует до: {subscription['end_date'].strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Ваш VLESS конфиг прикреплён ниже\n\n"
            f"Инструкция по подключению: /help"
        )
        
        await callback.message.delete()
        await callback.message.answer(
            success_text,
            parse_mode='HTML',
            reply_markup=get_main_menu(is_subscribed=True)
        )
        await callback.message.answer_document(
            document=config_file,
            caption="Ваш VLESS конфиг (импортируйте в Nekobox, v2rayNG, Streisand и т.д.)"
        )
        
        await state.clear()
        await callback.answer("Подписка активирована!", show_alert=True)
        logger.info(f"Подписка создана для {user_id} — {plan_type}")
        
    else:
        await callback.answer("Платёж ещё не поступил. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get('payment_id')
    if payment_id:
        await update_payment_status(payment_id, 'cancelled')
    
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Оплата отменена\n\nВы можете выбрать тариф снова",
        reply_markup=get_main_menu(is_subscribed=False)
    )
    await callback.answer()


# ==================== Telegram Payments (опционально) ====================

@router.callback_query(F.data.startswith("plan_telegram_"))
async def process_telegram_payment(callback: CallbackQuery):
    plan_id = callback.data.replace("plan_telegram_", "")
    if plan_id not in SUBSCRIPTION_PLANS:
        await callback.answer("Неверный тариф", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    prices = [LabeledPrice(label=plan['name'], amount=plan['price'] * 100)]
    
    await callback.message.answer_invoice(
        title=f"VPN — {plan['name']}",
        description=f"Подписка на {plan['duration_days']} дней\nБезлимит | VLESS Reality",
        payload=f"vless_{plan_id}_{callback.from_user.id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=prices,
        start_parameter="vless-sub"
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    plan_id = parts[1]
    user_id = int(parts[2])
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    # Создаём платёж
    await create_payment(
        user_id=user_id,
        amount=message.successful_payment.total_amount / 100,
        currency=message.successful_payment.currency,
        plan_type=plan['name'],
        payment_id=message.successful_payment.telegram_payment_charge_id
    )
    await update_payment_status(message.successful_payment.telegram_payment_charge_id, 'succeeded')
    
    # Генерируем VLESS
    vless = await create_vless_user(server_type="standard")
    if not vless:
        await message.answer("Ошибка создания конфигурации. Обратитесь в поддержку.")
        return
    
    subscription = await create_subscription(
        user_id=user_id,
        plan_type=plan['name'],
        duration_days=plan['duration_days'],
        vpn_config=vless["config"],
        vpn_login=vless["email"],
        vpn_password=vless["uuid"][:16]
    )
    
    config_file = BytesIO(vless["config"].encode('utf-8'))
    config_file.name = f"vless_{user_id}.txt"
    
    await message.answer(
        f"<b>Спасибо за покупку!</b>\n\n"
        f"Подписка активирована до {subscription['end_date'].strftime('%d.%m.%Y')}\n\n"
        f"Конфиг ниже",
        parse_mode='HTML',
        reply_markup=get_main_menu(is_subscribed=True)
    )
    await message.answer_document(config_file, caption="VLESS Reality конфиг")


# История платежей
@router.message(F.text == "История платежей")
async def payment_history(message: Message):
    payments = await get_user_payments(message.from_user.id)
    if not payments:
        await message.answer("У вас пока нет платежей")
        return
    
    text = "<b>История платежей</b>\n\n"
    for p in payments[:10]:
        status = {"succeeded": "Успешно", "pending": "Ожидает", "cancelled": "Отменён"}.get(p['status'], p['status'])
        text += f"{status} {p['plan_type']} — {p['amount']} ₽\n"
        text += f"{p['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await message.answer(text, parse_mode='HTML')