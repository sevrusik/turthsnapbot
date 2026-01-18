"""
User Repository (PostgreSQL)

Database operations for users
"""

import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, date
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from config.settings import settings
from database.db import db

logger = logging.getLogger(__name__)


class UserRepository:
    """
    User data access layer using PostgreSQL
    """

    async def create_or_update_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> Dict:
        """
        Create or update user

        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name

        Returns:
            User dict
        """

        now = datetime.now()

        # Check if user exists
        existing_user = await db.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            telegram_id
        )

        if existing_user:
            # Update existing user
            await db.execute(
                """
                UPDATE users
                SET username = $1, first_name = $2, updated_at = $3
                WHERE id = $4
                """,
                username, first_name, now, telegram_id
            )

            user = await self.get_user(telegram_id)
        else:
            # Create new user
            await db.execute(
                """
                INSERT INTO users (
                    id, username, first_name, subscription_tier,
                    total_checks, daily_checks_remaining, last_check_reset_at,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                telegram_id, username, first_name, 'free',
                0, 3, date.today(), now, now
            )

            user = await self.get_user(telegram_id)

        logger.debug(f"User created/updated: {telegram_id}")

        return user

    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """
        Get user by Telegram ID

        Args:
            telegram_id: Telegram user ID

        Returns:
            User dict or None
        """
        row = await db.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            telegram_id
        )

        if row:
            return dict(row)

        return None

    async def can_user_analyze(self, telegram_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user can perform analysis

        Args:
            telegram_id: Telegram user ID

        Returns:
            (can_analyze, error_message)
        """

        # TEMPORARILY DISABLED: No subscription checks
        return True, None

        # # Admin users have unlimited checks
        # if settings.is_admin(telegram_id):
        #     logger.debug(f"Admin user {telegram_id} - unlimited checks")
        #     return True, None

        # user = await self.get_user(telegram_id)

        # if not user:
        #     return False, "User not found. Send /start to register."

        # # Reset daily checks if needed
        # today = date.today()
        # if user['last_check_reset_at'] < today:
        #     await db.execute(
        #         """
        #         UPDATE users
        #         SET daily_checks_remaining = 3, last_check_reset_at = $1
        #         WHERE id = $2
        #         """,
        #         today, telegram_id
        #     )
        #     user['daily_checks_remaining'] = 3
        #     logger.debug(f"Reset daily checks for user {telegram_id}")

        # # Pro users have unlimited checks
        # if user['subscription_tier'] == 'pro':
        #     return True, None

        # # Free users have daily limit
        # if user['daily_checks_remaining'] <= 0:
        #     return False, (
        #         "❌ <b>Daily limit reached</b>\n\n"
        #         "Free tier: 3 checks per day\n\n"
        #         "💎 Upgrade to Pro for unlimited checks: /subscribe"
        #     )

        # return True, None

    async def decrement_daily_checks(self, telegram_id: int):
        """
        Decrement daily checks for user

        Args:
            telegram_id: Telegram user ID
        """

        # Don't decrement for admins
        if settings.is_admin(telegram_id):
            logger.debug(f"Admin user {telegram_id} - checks not decremented")
            return

        user = await self.get_user(telegram_id)

        if user and user['subscription_tier'] == 'free':
            await db.execute(
                """
                UPDATE users
                SET daily_checks_remaining = GREATEST(0, daily_checks_remaining - 1),
                    total_checks = total_checks + 1
                WHERE id = $1
                """,
                telegram_id
            )

            logger.debug(
                f"User {telegram_id} checks decremented. Remaining: {user['daily_checks_remaining'] - 1}"
            )

    async def upgrade_to_pro(
        self,
        telegram_id: int,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        expires_at: datetime
    ):
        """
        Upgrade user to Pro

        Args:
            telegram_id: Telegram user ID
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            expires_at: Subscription expiration date
        """

        await db.execute(
            """
            UPDATE users
            SET subscription_tier = 'pro',
                stripe_customer_id = $1,
                stripe_subscription_id = $2,
                subscription_expires_at = $3,
                updated_at = $4
            WHERE id = $5
            """,
            stripe_customer_id, stripe_subscription_id, expires_at,
            datetime.now(), telegram_id
        )

        logger.info(f"User {telegram_id} upgraded to Pro")

    async def downgrade_to_free(self, telegram_id: int):
        """
        Downgrade user to Free

        Args:
            telegram_id: Telegram user ID
        """

        await db.execute(
            """
            UPDATE users
            SET subscription_tier = 'free',
                subscription_expires_at = NULL,
                daily_checks_remaining = 3,
                updated_at = $1
            WHERE id = $2
            """,
            datetime.now(), telegram_id
        )

        logger.info(f"User {telegram_id} downgraded to Free")
