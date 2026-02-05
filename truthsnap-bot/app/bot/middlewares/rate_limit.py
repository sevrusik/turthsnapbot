"""
Rate Limiting Middleware

Prevents spam and abuse using Redis-based sliding window
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Dict, Any, Awaitable, Optional
import time
import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware with Redis-based sliding window

    Limits: 5 messages per minute per user (configurable)
    Uses Redis sorted sets for distributed rate limiting
    """

    def __init__(
        self,
        rate_limit: int = 5,
        window: int = 60,
        redis: Optional[Redis] = None
    ):
        """
        Args:
            rate_limit: Max messages per window
            window: Time window in seconds
            redis: Redis client for distributed rate limiting
                   If None, falls back to in-memory storage (not recommended for production)
        """
        super().__init__()
        self.rate_limit = rate_limit
        self.window = window
        self.redis = redis

        # Fallback to in-memory storage if Redis not provided
        # WARNING: In-memory storage doesn't work with multiple bot instances
        self.user_requests: Dict[int, list] = {}

        if not redis:
            logger.warning(
                "⚠️  Rate limiting using in-memory storage. "
                "For production with multiple instances, pass Redis client."
            )

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

        # Use Redis if available, otherwise fallback to in-memory
        if self.redis:
            is_allowed = await self._check_rate_limit_redis(user_id, now)
        else:
            is_allowed = await self._check_rate_limit_memory(user_id, now)

        if not is_allowed:
            logger.warning(f"⚠️  Rate limit exceeded for user {user_id}")

            await event.answer(
                "⚠️ <b>Too many requests</b>\n\n"
                "Please slow down. Wait a minute and try again.",
                parse_mode="HTML"
            )

            return  # Don't process this message

        # Continue processing
        return await handler(event, data)

    async def _check_rate_limit_redis(self, user_id: int, now: float) -> bool:
        """
        Check rate limit using Redis sorted set (sliding window)

        Args:
            user_id: Telegram user ID
            now: Current timestamp

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        key = f"ratelimit:user:{user_id}"
        window_start = now - self.window

        try:
            # Remove old entries outside the window
            await self.redis.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            count = await self.redis.zcount(key, window_start, now)

            # Check if rate limit exceeded
            if count >= self.rate_limit:
                return False

            # Add current request
            await self.redis.zadd(key, {str(now): now})

            # Set expiration to cleanup old keys
            await self.redis.expire(key, self.window * 2)

            return True

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}", exc_info=True)
            # On Redis error, allow request (fail-open)
            return True

    async def _check_rate_limit_memory(self, user_id: int, now: float) -> bool:
        """
        Fallback in-memory rate limiting (not suitable for production)

        Args:
            user_id: Telegram user ID
            now: Current timestamp

        Returns:
            True if request allowed, False if rate limit exceeded
        """
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
            return False

        # Add current request
        self.user_requests[user_id].append(now)

        return True
