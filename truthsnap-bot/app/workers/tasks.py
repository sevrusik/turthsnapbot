"""
Background task definitions for RQ (Redis Queue)

Tasks run in separate worker processes
"""

import asyncio
import logging
from datetime import datetime
import hashlib

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.fraudlens_client import FraudLensClient
from services.storage import S3Storage
from services.notifications import BotNotifier
from database.repositories.analysis_repo import AnalysisRepository
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def analyze_photo_task(
    user_id: int,
    chat_id: int,
    message_id: int,
    photo_s3_key: str,
    tier: str,
    scenario: str = None,
    progress_message_id: int = None
):
    """
    Background task: Analyze photo

    This runs in a separate worker process

    Args:
        user_id: Telegram user ID
        chat_id: Chat ID for sending result
        message_id: Message ID for reply
        photo_s3_key: S3 key where photo is stored
        tier: User tier (free/pro)
        scenario: Scenario context (adult_blackmail/teenager_sos/None)
        progress_message_id: Message ID for progress updates (UX improvement)

    Returns:
        {
            "status": "success",
            "analysis_id": "..."
        }
    """

    import time
    start_time = time.time()

    try:
        logger.info(f"[Worker] ⏱️  STAGE 1/6: Starting analysis for user {user_id}")

        # STAGE 2: Download photo from S3
        stage_start = time.time()

        # Progress update: Downloading
        if progress_message_id:
            from services.progress_notifier import sync_update_progress
            sync_update_progress(chat_id, progress_message_id, "downloading")

        s3 = S3Storage()
        photo_bytes = asyncio.run(s3.download(photo_s3_key))
        stage_duration = (time.time() - stage_start) * 1000

        logger.info(f"[Worker] ⏱️  STAGE 2/6: Downloaded {len(photo_bytes)} bytes from S3 in {stage_duration:.0f}ms")

        # Progress update: EXIF extraction (happens inside API but we show it here)
        if progress_message_id:
            from services.progress_notifier import sync_update_progress
            sync_update_progress(chat_id, progress_message_id, "exif")

        # Small delay to let users see the EXIF stage
        time.sleep(1)

        # STAGE 3: Call FraudLens API
        stage_start = time.time()

        # Progress update: AI Detection (main stage)
        if progress_message_id:
            from services.progress_notifier import sync_update_progress
            sync_update_progress(chat_id, progress_message_id, "ai")

        # Determine mode based on tier parameter
        # tier can be: "photo", "document", "free", "pro"
        is_document = (tier == "document")
        is_photo = (tier == "photo")

        # For documents: detailed analysis with EXIF
        # For photos: basic analysis without EXIF
        # For subscription tiers (free/pro): treat as photos
        if is_document:
            detail_level = "detailed"
            preserve_exif = True
        else:
            # Photos or subscription tiers
            detail_level = "basic"
            preserve_exif = False

        # Use async context manager to properly close HTTP client
        async def call_fraudlens_api():
            async with FraudLensClient() as fraudlens:
                return await fraudlens.verify_photo(photo_bytes, detail_level, preserve_exif=preserve_exif)

        result = asyncio.run(call_fraudlens_api())
        stage_duration = (time.time() - stage_start) * 1000

        mode_label = "DOCUMENT (EXIF preserved)" if preserve_exif else "PHOTO (EXIF stripped)"
        logger.info(f"[Worker] ⏱️  STAGE 3/6: FraudLens API analysis completed in {stage_duration:.0f}ms | mode={mode_label} | verdict={result['verdict']} | confidence={result['confidence']:.2f}")

        # Progress update: Frequency analysis (post-API visual feedback)
        if progress_message_id:
            from services.progress_notifier import sync_update_progress
            sync_update_progress(chat_id, progress_message_id, "frequency")

        # Small delay for UX
        time.sleep(0.5)

        # Progress update: Final scoring
        if progress_message_id:
            from services.progress_notifier import sync_update_progress
            sync_update_progress(chat_id, progress_message_id, "scoring")

        # STAGE 4: Save to database + get user tier (combined async operation)
        stage_start = time.time()

        # Run both DB operations in a single async context to avoid event loop conflicts
        async def save_and_get_tier():
            from database.repositories.user_repo import UserRepository

            # Create analysis
            analysis_repo = AnalysisRepository()
            analysis_id = await analysis_repo.create_analysis(
                user_id=user_id,
                photo_hash=compute_hash(photo_bytes),
                verdict=result["verdict"],
                confidence=result["confidence"],
                full_result=result,
                photo_s3_key=photo_s3_key,
                preserve_exif=preserve_exif
            )

            # Get user tier
            user_repo = UserRepository()
            user = await user_repo.get_user(user_id)
            user_tier = user.get('subscription_tier', 'free') if user else 'free'

            return analysis_id, user_tier

        analysis_id, user_tier = asyncio.run(save_and_get_tier())
        stage_duration = (time.time() - stage_start) * 1000

        logger.info(f"[Worker] ⏱️  STAGE 4/6: Saved analysis to DB in {stage_duration:.0f}ms | analysis_id={analysis_id} | user_tier={user_tier}")

        # STAGE 5: Send result back to user via Telegram
        stage_start = time.time()

        # Use async context manager to properly close bot session
        async def send_telegram_notification():
            async with BotNotifier() as notifier:
                await notifier.send_analysis_result(
                    chat_id=chat_id,
                    message_id=message_id,
                    result=result,
                    tier=user_tier,  # Use actual subscription tier (free/pro), not upload mode
                    analysis_id=analysis_id,
                    scenario=scenario  # Pass scenario context for proper keyboard
                )

        asyncio.run(send_telegram_notification())
        stage_duration = (time.time() - stage_start) * 1000

        logger.info(f"[Worker] ⏱️  STAGE 5/6: Sent result to Telegram in {stage_duration:.0f}ms")

        # STAGE 6: Keep photo in S3 for PDF generation (DON'T delete immediately)
        # Photo will be automatically cleaned up by S3 lifecycle policy (e.g., 24 hours)
        logger.info(f"[Worker] ⏱️  STAGE 6/6: Photo kept in S3 for PDF generation: {photo_s3_key}")

        total_duration = (time.time() - start_time) * 1000
        logger.info(f"[Worker] ✅ COMPLETED: Total analysis time {total_duration:.0f}ms ({total_duration/1000:.1f}s) for user {user_id}")

        return {
            "status": "success",
            "analysis_id": analysis_id
        }

    except Exception as e:
        logger.error(f"[Worker] Analysis failed for user {user_id}: {e}", exc_info=True)

        # Notify user about error
        try:
            async def send_error_notification():
                async with BotNotifier() as notifier:
                    await notifier.send_error_message(
                        chat_id=chat_id,
                        message_id=message_id,
                        error=str(e)
                    )

            asyncio.run(send_error_notification())
        except Exception as notify_error:
            logger.error(f"[Worker] Failed to notify user: {notify_error}")

        # Re-raise for RQ to mark as failed
        raise


def compute_hash(data: bytes) -> str:
    """Compute SHA-256 hash"""
    return hashlib.sha256(data).hexdigest()
