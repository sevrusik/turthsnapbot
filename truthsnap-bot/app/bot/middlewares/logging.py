"""
Logging Middleware

Logs all user interactions
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Dict, Any, Awaitable
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Logs all incoming messages
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Log message and continue processing
        """

        user_id = event.from_user.id
        username = event.from_user.username or "unknown"
        message_type = "photo" if event.photo else "text"

        logger.info(
            f"Message from {user_id} (@{username}): type={message_type}"
        )

        # Continue processing
        return await handler(event, data)
