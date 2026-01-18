"""
Counter-measures module

For Adult Blackmail scenario:
- Safe Response Generator (AI-generated responses to blackmailer)
- Links to StopNCII, FBI IC3
- Educational resources
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from bot.keyboards.scenarios import get_counter_measures_keyboard
from database.repositories.analysis_repo import AnalysisRepository

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "adult:counter_measures")
async def show_counter_measures(callback: CallbackQuery):
    """
    Show Counter-Measures menu

    Options:
    - Safe Response Generator
    - Report to StopNCII
    - Report to FBI IC3
    - Download Forensic PDF
    """

    # Get latest analysis for this user (to link PDF)
    user_id = callback.from_user.id
    analysis_repo = AnalysisRepository()

    # Get user's most recent analysis
    try:
        # Get latest analysis from database
        from database.db import db
        query = """
            SELECT analysis_id FROM analyses
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = await db.fetchrow(query, user_id)
        analysis_id = result['analysis_id'] if result else "unknown"

        await callback.message.edit_text(
            "🛡️ <b>Counter-Measures</b>\n\n"
            "<b>Available strategies:</b>\n\n"
            "💬 <b>Safe Response Generator</b>\n"
            "   → AI-crafted responses that cite your forensic evidence\n"
            "   → Example: \"My expert analysis confirmed this is AI-generated...\"\n\n"
            "🚫 <b>StopNCII</b>\n"
            "   → Report intimate images to prevent online spread\n"
            "   → Works with major platforms (Facebook, Instagram, etc.)\n\n"
            "🚨 <b>FBI IC3</b>\n"
            "   → Official Internet Crime Complaint Center\n"
            "   → For US-based incidents\n\n"
            "📄 <b>Forensic PDF</b>\n"
            "   → Legal-grade report with SHA-256 hash\n"
            "   → Acceptable as supporting evidence in court\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>Important:</b> Never pay a blackmailer.\n"
            "Payment increases demands and funds criminal networks.",
            parse_mode="HTML",
            reply_markup=get_counter_measures_keyboard(analysis_id)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"[Counter-Measures] Error: {e}")
        await callback.answer("❌ Error loading counter-measures", show_alert=True)


@router.callback_query(F.data == "counter:safe_response")
async def generate_safe_response(callback: CallbackQuery):
    """
    Generate safe response templates

    AI-crafted responses that:
    1. Assert you have forensic proof
    2. Reference legal consequences
    3. Do NOT engage emotionally
    """

    templates = [
        {
            "name": "Professional - Forensic Evidence",
            "text": (
                "I have submitted your image to professional forensic analysis. "
                "The report confirms it is AI-generated with a confidence score of [X]%. "
                "I have documented this incident with:\n\n"
                "• SHA-256 hash: [HASH]\n"
                "• Report ID: [ID]\n"
                "• Timestamp: [TIME]\n\n"
                "This has been reported to cybercrime authorities. "
                "Any further contact will be forwarded to law enforcement."
            )
        },
        {
            "name": "Legal Notice",
            "text": (
                "This constitutes formal notice:\n\n"
                "1. I have forensic proof this image is fabricated\n"
                "2. All communications have been logged and preserved\n"
                "3. This incident has been reported to:\n"
                "   - FBI Internet Crime Complaint Center (IC3)\n"
                "   - National Center for Missing & Exploited Children\n\n"
                "Extortion is a federal crime under 18 U.S.C. § 875.\n"
                "Cease all contact immediately."
            )
        },
        {
            "name": "Technical - AI Detection",
            "text": (
                "Your image has been analyzed using:\n"
                "• Face-swap detection algorithms\n"
                "• EXIF metadata validation\n"
                "• Frequency domain analysis\n"
                "• AI watermark identification\n\n"
                "Result: AI-generated fabrication.\n\n"
                "I have legal documentation of this forgery. "
                "Distribution of this material constitutes criminal harassment."
            )
        },
        {
            "name": "Brief - No Negotiation",
            "text": (
                "I have proof this is AI-generated.\n"
                "Forensic report filed with authorities.\n"
                "Do not contact me again."
            )
        }
    ]

    response_text = "<b>💬 Safe Response Templates</b>\n\n"
    response_text += "Copy and customize these responses:\n\n"
    response_text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, template in enumerate(templates, 1):
        response_text += f"<b>{i}. {template['name']}</b>\n\n"
        response_text += f"<code>{template['text']}</code>\n\n"
        response_text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    response_text += (
        "⚠️ <b>Usage notes:</b>\n"
        "• Replace [X], [HASH], [ID], [TIME] with actual data from your report\n"
        "• Send ONCE, then block the blackmailer\n"
        "• Do not engage in conversation\n"
        "• Save all communications as evidence\n\n"
        "💡 <b>Reminder:</b> These templates work because they:\n"
        "1. Show you have evidence\n"
        "2. Reference legal consequences\n"
        "3. Demonstrate you're not a victim who will pay"
    )

    await callback.message.edit_text(
        response_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 Back to Counter-measures",
                callback_data="adult:counter_measures"
            )],
            [InlineKeyboardButton(
                text="🏠 Main Menu",
                callback_data="scenario:select"
            )]
        ])
    )

    await callback.answer("✅ Templates generated", show_alert=False)


@router.callback_query(F.data == "adult:back_to_analysis")
async def back_to_analysis(callback: CallbackQuery):
    """Return to analysis results"""

    from bot.keyboards.scenarios import get_adult_blackmail_step1_keyboard

    await callback.message.edit_text(
        "👤 <b>Analysis Complete</b>\n\n"
        "Choose next action:",
        parse_mode="HTML",
        reply_markup=get_adult_blackmail_step1_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "scenario:knowledge_base")
async def show_knowledge_base(callback: CallbackQuery):
    """
    Educational resources

    Topics:
    - How AI deepfakes work
    - Why professional photo editing affects results
    - Legal rights
    - Reporting procedures
    """

    await callback.message.edit_text(
        "📚 <b>Knowledge Base</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🤖 How AI Deepfakes Work</b>\n\n"
        "Deepfakes use neural networks to:\n"
        "• Swap faces in photos/videos\n"
        "• Generate realistic but fake images\n"
        "• Mimic voices and writing styles\n\n"
        "Common techniques:\n"
        "- GAN (Generative Adversarial Networks)\n"
        "- Face-swap models (DeepFaceLab, FaceSwap)\n"
        "- Stable Diffusion / Midjourney for full synthesis\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🔍 Detection Methods</b>\n\n"
        "Our analysis uses:\n"
        "1. <b>EXIF metadata</b> - Camera fingerprints\n"
        "2. <b>FFT analysis</b> - Frequency patterns\n"
        "3. <b>Face-swap detection</b> - Geometric inconsistencies\n"
        "4. <b>AI watermarks</b> - Hidden signatures\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>⚖️ Your Legal Rights</b>\n\n"
        "• Blackmail is illegal in all 50 US states\n"
        "• Federal law: 18 U.S.C. § 875 (extortion)\n"
        "• Deepfake laws: Many states now criminalize malicious deepfakes\n"
        "• You have right to report without shame\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>⚠️ Why Professional Editing Matters</b>\n\n"
        "Edited photos may show false positives because:\n"
        "• Filters alter frequency patterns\n"
        "• Cropping removes EXIF data\n"
        "• Compression changes artifacts\n\n"
        "This is why our disclaimer states:\n"
        "\"<i>This analysis is probabilistic, not definitive proof</i>\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🚨 Where to Report</b>\n\n"
        "• <b>FBI IC3:</b> ic3.gov\n"
        "• <b>StopNCII:</b> stopncii.org\n"
        "• <b>NCMEC (under 18):</b> cybertip.org\n"
        "• <b>Local police:</b> Bring forensic report\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📄 All reports include the disclaimer to protect you legally.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🏠 Main Menu",
                callback_data="scenario:select"
            )]
        ])
    )

    await callback.answer()
