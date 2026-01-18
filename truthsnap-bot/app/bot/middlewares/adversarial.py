"""
Adversarial Protection Middleware

Detects adversarial attacks (e.g., pixel-shifted photos)
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Dict, Any, Awaitable
import logging
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AdversarialProtectionMiddleware(BaseMiddleware):
    """
    Detects adversarial attacks

    Strategy:
    - Track perceptual hashes of uploaded photos
    - Flag if user uploads many similar photos
    """

    def __init__(
        self,
        similarity_threshold: int = 5,  # Hamming distance
        max_similar: int = 10,  # Max similar uploads
        window_hours: int = 1
    ):
        super().__init__()
        self.similarity_threshold = similarity_threshold
        self.max_similar = max_similar
        self.window_hours = window_hours

        # Store photo hashes per user
        self.user_photo_hashes: Dict[int, list] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Check for adversarial patterns
        """

        # Only check photo messages
        if not event.photo:
            return await handler(event, data)

        user_id = event.from_user.id
        photo = event.photo[-1]

        # Compute simple hash (in production, use perceptual hash)
        photo_hash = photo.file_unique_id

        # Initialize user's photo history
        if user_id not in self.user_photo_hashes:
            self.user_photo_hashes[user_id] = []

        # Remove old hashes outside window
        cutoff_time = datetime.now() - timedelta(hours=self.window_hours)
        self.user_photo_hashes[user_id] = [
            (h, t) for h, t in self.user_photo_hashes[user_id]
            if t > cutoff_time
        ]

        # Count similar photos (simple exact match for MVP)
        # In production, use perceptual hashing (pHash, dHash)
        similar_count = sum(
            1 for h, _ in self.user_photo_hashes[user_id]
            if h == photo_hash
        )

        # Check if adversarial attack
        if similar_count >= self.max_similar:
            logger.warning(
                f"Adversarial attack detected: user {user_id} uploaded "
                f"{similar_count} similar photos in {self.window_hours}h"
            )

            await event.answer(
                "🚨 <b>Suspicious Activity Detected</b>\n\n"
                "You've uploaded many similar photos.\n"
                "This looks like an adversarial attack attempt.\n\n"
                "Your account has been flagged for review.\n"
                "Contact support if this is a mistake: /support",
                parse_mode="HTML"
            )

            # TODO: Log to security_events table
            # TODO: Temporarily ban user

            return  # Block this request

        # Add current photo hash
        self.user_photo_hashes[user_id].append((photo_hash, datetime.now()))

        # Continue processing
        return await handler(event, data)
