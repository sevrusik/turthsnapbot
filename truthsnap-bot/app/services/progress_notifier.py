"""
Progress Notification Service

Updates users with real-time analysis progress to improve UX
Prevents "bot is frozen" perception during long-running analysis
"""

from aiogram import Bot
import logging
from typing import Optional
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings

logger = logging.getLogger(__name__)


class ProgressNotifier:
    """
    Sends progressive status updates during analysis

    Timeline (0-25 seconds):
    0-2s:   "📥 Downloading from cloud..."
    2-5s:   "🔍 EXIF metadata extraction..."
    5-15s:  "🤖 AI detectors analyzing..."
    15-20s: "🔬 Frequency analysis..."
    20-25s: "📊 Final scoring..."
    """

    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    async def update_progress(
        self,
        chat_id: int,
        message_id: int,
        stage: str,
        emoji: str = "⏳",
        details: Optional[str] = None
    ):
        """
        Update progress message with current analysis stage

        Args:
            chat_id: Telegram chat ID
            message_id: Message ID to edit
            stage: Stage description (e.g., "AI detectors analyzing")
            emoji: Progress emoji
            details: Optional additional details
        """

        # Build progress message
        message = f"{emoji} <b>{stage}</b>\n\n"

        if details:
            message += f"{details}\n\n"

        # Progress bar visual
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += "<i>Analysis in progress...</i>"

        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message,
                parse_mode="HTML"
            )

            logger.info(f"Progress update: {stage} | chat={chat_id}, msg={message_id}")

        except Exception as e:
            # Log but don't fail the analysis if progress update fails
            logger.warning(f"Failed to update progress message: {e}")

    async def stage_downloading(self, chat_id: int, message_id: int):
        """Stage 1: Downloading from S3"""
        await self.update_progress(
            chat_id=chat_id,
            message_id=message_id,
            stage="Retrieving image from cloud",
            emoji="📥",
            details="⏱ ETA: ~20 seconds"
        )

    async def stage_exif_extraction(self, chat_id: int, message_id: int):
        """Stage 2: EXIF metadata extraction"""
        await self.update_progress(
            chat_id=chat_id,
            message_id=message_id,
            stage="Extracting metadata",
            emoji="🔍",
            details=(
                "Analyzing:\n"
                "• Camera fingerprint\n"
                "• GPS coordinates\n"
                "• Edit history\n"
                "• Timestamps"
            )
        )

    async def stage_ai_detection(self, chat_id: int, message_id: int):
        """Stage 3: AI/ML detection (longest stage)"""
        await self.update_progress(
            chat_id=chat_id,
            message_id=message_id,
            stage="AI detectors running",
            emoji="🤖",
            details=(
                "Deep analysis:\n"
                "• GAN pattern detection\n"
                "• Diffusion model signatures\n"
                "• Face-swap artifacts\n"
                "• Watermark detection"
            )
        )

    async def stage_frequency_analysis(self, chat_id: int, message_id: int):
        """Stage 4: Frequency domain analysis"""
        await self.update_progress(
            chat_id=chat_id,
            message_id=message_id,
            stage="Frequency domain analysis",
            emoji="🔬",
            details=(
                "Running forensic tests:\n"
                "• FFT pattern analysis\n"
                "• Compression artifacts\n"
                "• Smoothing detection"
            )
        )

    async def stage_final_scoring(self, chat_id: int, message_id: int):
        """Stage 5: Final scoring"""
        await self.update_progress(
            chat_id=chat_id,
            message_id=message_id,
            stage="Generating final report",
            emoji="📊",
            details="Almost done..."
        )

    async def close(self):
        """Close bot session"""
        await self.bot.session.close()


def sync_update_progress(chat_id: int, message_id: int, stage: str):
    """
    Synchronous wrapper for progress updates (for use in non-async contexts)

    Args:
        chat_id: Chat ID
        message_id: Message ID
        stage: Stage name (downloading/exif/ai/frequency/scoring)
    """

    async def _update():
        notifier = ProgressNotifier()
        try:
            if stage == "downloading":
                await notifier.stage_downloading(chat_id, message_id)
            elif stage == "exif":
                await notifier.stage_exif_extraction(chat_id, message_id)
            elif stage == "ai":
                await notifier.stage_ai_detection(chat_id, message_id)
            elif stage == "frequency":
                await notifier.stage_frequency_analysis(chat_id, message_id)
            elif stage == "scoring":
                await notifier.stage_final_scoring(chat_id, message_id)
            else:
                logger.warning(f"Unknown progress stage: {stage}")
        finally:
            await notifier.close()

    try:
        asyncio.run(_update())
    except Exception as e:
        logger.error(f"Progress update failed: {e}")
