"""
TruthSnap Bot - Main Entry Point

Telegram bot using aiogram 3.x for deepfake detection
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings
from bot.handlers import (
    start,
    photo,
    subscription,
    callbacks,
    scenarios,
    counter_measures,
    parent_support
)
from bot.middlewares import (
    LoggingMiddleware,
    RateLimitMiddleware,
    AdversarialProtectionMiddleware
)
from database.db import db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """
    Main bot startup function
    """

    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    # Initialize database connection
    await db.connect()
    logger.info("PostgreSQL connection established")

    # Initialize bot
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # Initialize Redis storage for FSM
    redis = Redis.from_url(settings.REDIS_URL)
    storage = RedisStorage(redis)

    # Initialize dispatcher
    dp = Dispatcher(storage=storage)

    # Register middlewares
    # ORDER MATTERS: Logging first, then rate limiting, then adversarial protection
    dp.message.middleware(LoggingMiddleware())
    logger.info("✅ Logging middleware registered")

    dp.message.middleware(
        RateLimitMiddleware(
            rate_limit=settings.RATE_LIMIT_PER_MINUTE,
            window=60,
            redis=redis  # Pass Redis client for distributed rate limiting
        )
    )
    logger.info(f"✅ Rate limiting enabled: {settings.RATE_LIMIT_PER_MINUTE} messages per minute per user (Redis-backed)")

    dp.message.middleware(AdversarialProtectionMiddleware(max_similar=10, window_hours=1))
    logger.info("✅ Adversarial protection enabled")

    # Register handlers
    # ORDER MATTERS: Commands first, then specific states, then general handlers
    dp.include_router(start.router)              # /start command (MUST BE FIRST!)
    dp.include_router(subscription.router)       # Subscription management (commands)
    dp.include_router(scenarios.router)          # Scenario-based flows (new)
    dp.include_router(counter_measures.router)   # Adult blackmail counter-measures
    dp.include_router(parent_support.router)     # Teenager parent communication
    dp.include_router(callbacks.router)          # PDF reports and other callbacks
    dp.include_router(photo.router)              # Photo/document uploads (legacy + scenario - LAST!)

    logger.info("Handlers registered (scenario-based flow enabled)")

    # Start bot
    try:
        logger.info("Bot started successfully!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await redis.close()
        await db.disconnect()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
