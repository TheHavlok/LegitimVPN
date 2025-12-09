from datetime import datetime, timedelta
from typing import Optional, List
import asyncpg
from config import DATABASE_URL

pool: Optional[asyncpg.Pool] = None

async def init_db():
    """Инициализация подключения к БД и создание таблиц"""
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    
    async with pool.acquire() as conn:
        # Таблица пользователей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                registration_date TIMESTAMP DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Таблица подписок
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                plan_type VARCHAR(50),
                start_date TIMESTAMP DEFAULT NOW(),
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                vpn_config TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица платежей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                amount DECIMAL(10, 2),
                currency VARCHAR(10),
                plan_type VARCHAR(50),
                status VARCHAR(50),
                payment_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Таблица уведомлений
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                message TEXT,
                sent_at TIMESTAMP DEFAULT NOW(),
                notification_type VARCHAR(50)
            )
        ''')

async def get_user(user_id: int):
    """Получить пользователя по ID"""
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            'SELECT * FROM users WHERE user_id = $1',
            user_id
        )

async def create_user(user_id: int, username: str, first_name: str, last_name: str):
    """Создать нового пользователя"""
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE
            SET username = $2, first_name = $3, last_name = $4
        ''', user_id, username, first_name, last_name)

async def get_active_subscription(user_id: int):
    """Получить активную подписку пользователя"""
    async with pool.acquire() as conn:
        return await conn.fetchrow('''
            SELECT * FROM subscriptions
            WHERE user_id = $1 AND is_active = TRUE
            AND end_date > NOW()
            ORDER BY end_date DESC
            LIMIT 1
        ''', user_id)

async def create_subscription(user_id: int, plan_type: str, duration_days: int, vpn_config: str):
    """Создать новую подписку"""
    end_date = datetime.now() + timedelta(days=duration_days)
    async with pool.acquire() as conn:
        return await conn.fetchrow('''
            INSERT INTO subscriptions (user_id, plan_type, end_date, vpn_config)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        ''', user_id, plan_type, end_date, vpn_config)

async def deactivate_subscription(subscription_id: int):
    """Деактивировать подписку"""
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE subscriptions
            SET is_active = FALSE
            WHERE id = $1
        ''', subscription_id)

async def get_expiring_subscriptions(days: int) -> List:
    """Получить подписки, истекающие через N дней"""
    target_date = datetime.now() + timedelta(days=days)
    async with pool.acquire() as conn:
        return await conn.fetch('''
            SELECT s.*, u.user_id, u.username, u.first_name
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.is_active = TRUE
            AND s.end_date::date = $1::date
        ''', target_date)

async def create_payment(user_id: int, amount: float, currency: str, plan_type: str, payment_id: str):
    """Создать запись о платеже"""
    async with pool.acquire() as conn:
        return await conn.fetchrow('''
            INSERT INTO payments (user_id, amount, currency, plan_type, status, payment_id)
            VALUES ($1, $2, $3, $4, 'pending', $5)
            RETURNING *
        ''', user_id, amount, currency, plan_type, payment_id)

async def update_payment_status(payment_id: str, status: str):
    """Обновить статус платежа"""
    async with pool.acquire() as conn:
        await conn.execute('''
            UPDATE payments
            SET status = $1
            WHERE payment_id = $2
        ''', status, payment_id)

async def get_all_users() -> List:
    """Получить всех пользователей"""
    async with pool.acquire() as conn:
        return await conn.fetch('SELECT * FROM users WHERE is_active = TRUE')

async def get_stats():
    """Получить статистику"""
    async with pool.acquire() as conn:
        total_users = await conn.fetchval('SELECT COUNT(*) FROM users WHERE is_active = TRUE')
        active_subs = await conn.fetchval('''
            SELECT COUNT(*) FROM subscriptions
            WHERE is_active = TRUE AND end_date > NOW()
        ''')
        total_revenue = await conn.fetchval('''
            SELECT COALESCE(SUM(amount), 0) FROM payments
            WHERE status = 'succeeded'
        ''')
        
        return {
            'total_users': total_users,
            'active_subscriptions': active_subs,
            'total_revenue': float(total_revenue) if total_revenue else 0
        }