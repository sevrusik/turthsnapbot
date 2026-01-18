"""
Rate Limiting Middleware

Prevents spam and abuse
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Dict, Any, Awaitable
import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware

    Limits: 5 messages per minute per user
    """

    def __init__(self, rate_limit: int = 5, window: int = 60):
        """
        Args:
            rate_limit: Max messages per window
            window: Time window in seconds
        """
        super().__init__()
        self.rate_limit = rate_limit
        self.window = window
        self.user_requests: Dict[int, list] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Check rate limit before processing message
        """

        user_id = event.from_user.id
        now = time.time()

        # Initialize user's request history
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        # Remove old requests outside window
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < self.window
        ]

        # Check if rate limit exceeded
        if len(self.user_requests[user_id]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")

            await event.answer(
                "⚠️ <b>Too many requests</b>\n\n"
                "Please slow down. Wait a minute and try again.",
                parse_mode="HTML"
            )

            return  # Don't process this message

        # Add current request
        self.user_requests[user_id].append(now)

        # Continue processing
        return await handler(event, data)
