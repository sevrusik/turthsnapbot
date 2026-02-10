"""
Callback query handlers

Includes:
- PDF report generation (legacy and scenario-based)
- Scenario-specific callbacks handled in dedicated modules
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
import logging
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from database.repositories.analysis_repo import AnalysisRepository
from services.storage import S3Storage
from services.fraudlens_client import FraudLensClient
from bot.keyboards.scenarios import (
    get_adult_blackmail_step1_keyboard,
    get_teenager_step2_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("pdf_report:"))
async def handle_pdf_report(callback: CallbackQuery):
    """
    Handle PDF report generation and download

    Format: pdf_report:ANL-20260113-000001
    """

    analysis_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    logger.info(f"[Callback] PDF report requested: {analysis_id} by user {user_id}")

    # Show "generating" message
    await callback.answer("📄 Generating PDF report...", show_alert=False)

    try:
        # Get analysis from database
        analysis_repo = AnalysisRepository()
        analysis = await analysis_repo.get_analysis(analysis_id)

        if not analysis:
            await callback.answer("❌ Analysis not found", show_alert=True)
            logger.warning(f"[Callback] Analysis not found: {analysis_id}")
            return

        # Check if user owns this analysis
        if analysis['user_id'] != user_id:
            await callback.answer("❌ Unauthorized access", show_alert=True)
            logger.warning(f"[Callback] Unauthorized PDF request: user {user_id} tried to access {analysis_id}")
            return

        # Generate PDF via FraudLens API (uses stored analysis data)
        fraudlens = FraudLensClient()

        try:
            pdf_bytes = await fraudlens.generate_pdf_report(
                analysis_id=analysis_id
            )

            logger.info(f"[Callback] Generated PDF: {len(pdf_bytes)} bytes for {analysis_id}")

        except Exception as e:
            error_msg = str(e)
            # Telegram has 200 char limit for callback answers
            if len(error_msg) > 150:
                error_msg = error_msg[:147] + "..."

            await callback.answer(
                f"❌ PDF generation failed\n\n{error_msg}",
                show_alert=True
            )
            logger.error(f"[Callback] PDF generation failed: {e}")
            return

        # Send PDF to user
        from datetime import datetime
        filename = f"truthsnap_report_{analysis_id}_{datetime.now().strftime('%Y%m%d')}.pdf"

        pdf_file = BufferedInputFile(
            file=pdf_bytes,
            filename=filename
        )

        await callback.message.answer_document(
            document=pdf_file,
            caption=(
                f"📄 <b>Forensic Analysis Report</b>\n\n"
                f"Analysis ID: <code>{analysis_id}</code>\n"
                f"Verdict: <b>{analysis['verdict'].upper()}</b>\n"
                f"Confidence: {analysis['confidence']*100:.1f}%\n\n"
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
            ),
            parse_mode="HTML"
        )

        await callback.answer("✅ PDF report sent!", show_alert=False)

        logger.info(f"[Callback] PDF sent successfully: {analysis_id}")

    except Exception as e:
        logger.error(f"[Callback] Unexpected error generating PDF: {e}", exc_info=True)
        try:
            await callback.answer(
                "❌ Something went wrong\n\nPlease try again later",
                show_alert=True
            )
        except Exception as callback_error:
            logger.error(f"[Callback] Failed to send error notification: {callback_error}")


@router.callback_query(F.data == "adult:forensic_pdf")
async def adult_get_forensic_pdf(callback: CallbackQuery):
    """
    Adult Blackmail - Get Forensic PDF

    Redirects to standard PDF generation
    """

    # Get latest analysis for this user
    user_id = callback.from_user.id
    analysis_repo = AnalysisRepository()

    try:
        # Get user's most recent analysis
        # In production: track analysis_id in FSM state
        # For now: inform user to use PDF button from analysis result

        await callback.answer(
            "📄 Use the 'Get PDF Report' button from your analysis result",
            show_alert=True
        )

    except Exception as e:
        logger.error(f"[Adult Forensic PDF] Error: {e}")
        await callback.answer("❌ Error", show_alert=True)

@router.callback_query(F.data == "general:ai_info")
async def general_ai_info(callback: CallbackQuery):
    """
    General Analysis - What is AI-generated content
    """
    
    await callback.answer()
    
    message = (
        "ℹ️ <b>What is AI-Generated Content?</b>\n\n"
        
        "AI image generators like Midjourney, DALL-E, Stable Diffusion, and others "
        "can create photorealistic images from text descriptions.\n\n"
        
        "<b>Common Uses:</b>\n"
        "• Art and design\n"
        "• Marketing materials\n"
        "• Social media content\n"
        "• Unfortunately: deepfakes and scams\n\n"
        
        "<b>How We Detect It:</b>\n"
        "🔍 Watermark analysis\n"
        "📸 Metadata inspection\n"
        "🤖 AI pattern detection\n"
        "🔬 Pixel-level forensics\n\n"
        
        "<i>Our AI detection models analyze multiple layers "
        "to determine if an image is synthetic or authentic.</i>"
    )
    
    await callback.message.answer(
        message,
        parse_mode="HTML"
    )
    
    logger.info(f"[General] Sent AI info to user {callback.from_user.id}")


@router.callback_query(F.data == "general:spotting_guide")
async def general_spotting_guide(callback: CallbackQuery):
    """
    General Analysis - How to spot fake images
    """
    
    await callback.answer()
    
    message = (
        "🔍 <b>How to Spot Fake Images</b>\n\n"
        
        "<b>🚩 Visual Red Flags:</b>\n"
        "• Unnatural lighting or shadows\n"
        "• Distorted hands or fingers\n"
        "• Blurry or missing text\n"
        "• Warped backgrounds\n"
        "• Asymmetric faces\n"
        "• Impossible physics\n\n"
        
        "<b>📱 Technical Signs:</b>\n"
        "• Missing EXIF metadata\n"
        "• No camera/device info\n"
        "• Suspicious file creation dates\n"
        "• AI software signatures\n\n"
        
        "<b>✅ Authentic Photos Usually Have:</b>\n"
        "• Camera make/model\n"
        "• GPS coordinates\n"
        "• Original timestamp\n"
        "• Realistic imperfections\n\n"
        
        "💡 <b>Pro Tip:</b> Always cross-check multiple sources "
        "and trust your instincts if something feels \"off\"!"
    )
    
    await callback.message.answer(
        message,
        parse_mode="HTML"
    )
    
    logger.info(f"[General] Sent spotting guide to user {callback.from_user.id}")
