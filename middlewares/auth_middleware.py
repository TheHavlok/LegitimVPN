from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.db import is_user_banned
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки прав доступа и статуса пользователя
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        
        # Проверяем, заблокирован ли пользователь
        if await is_user_banned(user.id):
            if isinstance(event, Message):
                await event.answer(
                    "🚫 <b>Ваш аккаунт заблокирован</b>\n\n"
                    "Если вы считаете это ошибкой, обратитесь в поддержку:\n"
                    "📧 support@vpnbot.com\n"
                    "💬 @vpn_support",
                    parse_mode='HTML'
                )
            else:
                await event.answer(
                    "🚫 Ваш аккаунт заблокирован",
                    show_alert=True
                )
            
            logger.warning(f"🚫 Заблокированный пользователь {user.id} попытался использовать бота")
            return
        
        # Логируем активность
        if isinstance(event, Message):
            logger.debug(f"📝 Сообщение от {user.id} (@{user.username}): {event.text[:50] if event.text else 'Не текст'}")
        elif isinstance(event, CallbackQuery):
            logger.debug(f"🔘 Callback от {user.id} (@{user.username}): {event.data}")
        
        # Передаем управление следующему обработчику
        return await handler(event, data)