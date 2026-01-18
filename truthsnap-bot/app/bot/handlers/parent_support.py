"""
Parent Communication Helper Module

For Teenager SOS scenario:
- Scripts for talking to parents
- How to show evidence
- What to expect
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from bot.keyboards.scenarios import (
    get_tell_parents_keyboard,
    get_stop_spread_keyboard
)
from database.repositories.analysis_repo import AnalysisRepository

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "teen:tell_parents")
async def show_tell_parents_guide(callback: CallbackQuery):
    """
    Show guide on how to tell parents

    Includes:
    - Conversation script
    - Why it helps
    - What evidence to show
    """

    # Get user's most recent analysis
    user_id = callback.from_user.id
    analysis_repo = AnalysisRepository()

    try:
        # Get latest analysis for this user
        # In production: would be better to track in FSM state
        # For now: query database for latest analysis
        from database.db import db
        query = """
            SELECT analysis_id FROM analyses
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = await db.fetchrow(query, user_id)
        analysis_id = result['analysis_id'] if result else "unknown"
    except Exception as e:
        logger.error(f"[Tell Parents] Failed to get analysis_id: {e}")
        analysis_id = "unknown"

    await callback.message.edit_text(
        "🤝 <b>How to Tell Your Parents</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Why tell them?</b>\n\n"
        "• They can help you report this\n"
        "• They can contact the police if needed\n"
        "• You don't have to handle this alone\n"
        "• It's easier when you have proof\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>What to say:</b>\n\n"
        "\"I need to show you something serious. "
        "Someone sent me a fake photo and is trying to blackmail me with it. "
        "I got it analyzed by TruthSnap, and here's the proof it's AI-generated.\"\n\n"
        "Then show them the PDF report.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>What evidence to show:</b>\n\n"
        "1. <b>PDF Report</b> - This has:\n"
        "   • AI detection score\n"
        "   • Technical analysis\n"
        "   • Official disclaimer\n\n"
        "2. <b>Screenshots</b> of the blackmail messages\n"
        "   (Do NOT send money or nudes!)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>What they'll probably ask:</b>\n\n"
        "❓ \"Are you sure it's fake?\"\n"
        "→ \"Yes, the report shows an AI score of [X]%. "
        "Real cameras don't create these patterns.\"\n\n"
        "❓ \"Did you send anyone photos?\"\n"
        "→ Be honest. Even if you did, blackmail is STILL illegal.\n\n"
        "❓ \"What should we do?\"\n"
        "→ \"TruthSnap gave me links to report this to the FBI and NCMEC.\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Remember:</b>\n"
        "• Your parents will probably be shocked at first\n"
        "• They might be angry at the blackmailer, not you\n"
        "• Having the report makes this conversation much easier\n"
        "• This happens to thousands of people - you're not alone\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📄 Click below to get the PDF report to show them.",
        parse_mode="HTML",
        reply_markup=get_tell_parents_keyboard(analysis_id)
    )

    await callback.answer()


@router.callback_query(F.data == "teen:conversation_script")
async def show_conversation_script(callback: CallbackQuery):
    """
    Detailed conversation script

    Step-by-step guide for talking to parents
    """

    await callback.message.edit_text(
        "💬 <b>Conversation Script</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 1: Choose the right time</b>\n\n"
        "• When they're not busy or stressed\n"
        "• In private (not in front of siblings)\n"
        "• When you feel calm enough to explain\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 2: Opening line</b>\n\n"
        "\"Mom/Dad, I need to talk to you about something serious. "
        "I'm okay, but I need your help with something.\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 3: Explain what happened</b>\n\n"
        "\"Someone online created a fake photo of me and is trying to "
        "blackmail me. I didn't do anything wrong, but I'm scared.\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 4: Show the evidence</b>\n\n"
        "\"I used TruthSnap to analyze the photo. "
        "Here's the report - it proves the photo is AI-generated.\"\n\n"
        "[Show PDF report]\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 5: Point to the key facts</b>\n\n"
        "\"Look at this part - it says 'AI Detection Score: [X]%'. "
        "This means a computer made it, not a real camera.\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 6: Ask for help</b>\n\n"
        "\"Can you help me report this? "
        "TruthSnap gave me links to the FBI and other places.\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>What if they get upset?</b>\n\n"
        "They might be:\n"
        "• Angry at the blackmailer → Normal!\n"
        "• Worried about you → Normal!\n"
        "• Confused about the tech → Show them the report\n\n"
        "Give them time to process it.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>What if they don't believe you?</b>\n\n"
        "• The report has a SHA-256 hash - this is legal evidence\n"
        "• Suggest calling the police together to verify\n"
        "• Show them the TruthSnap bot (this conversation)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 <b>Final tip:</b> If you absolutely can't tell your parents, "
        "talk to another trusted adult:\n"
        "• School counselor\n"
        "• Teacher\n"
        "• Older sibling\n"
        "• Coach or mentor\n\n"
        "You don't have to do this alone.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 Back",
                callback_data="teen:tell_parents"
            )],
            [InlineKeyboardButton(
                text="🏠 Main Menu",
                callback_data="scenario:select"
            )]
        ])
    )

    await callback.answer()


@router.callback_query(F.data == "teen:stop_spread")
async def show_stop_spread(callback: CallbackQuery):
    """
    Emergency protection: Stop the Spread

    Links to:
    - Take It Down (NCMEC)
    - FBI Tips
    - CyberTipline
    """

    await callback.message.edit_text(
        "🚫 <b>Stop the Spread</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>What is Take It Down?</b>\n\n"
        "Take It Down is a FREE service by NCMEC (National Center for Missing & Exploited Children).\n\n"
        "It helps remove intimate images from:\n"
        "• Facebook\n"
        "• Instagram\n"
        "• TikTok\n"
        "• Snapchat\n"
        "• OnlyFans\n"
        "• And 20+ other platforms\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>How does it work?</b>\n\n"
        "1. You create a \"hash\" of the image (a unique fingerprint)\n"
        "2. NCMEC shares that hash with platforms\n"
        "3. Platforms automatically block it from being uploaded\n\n"
        "<b>Important:</b> You DON'T upload the actual photo!\n"
        "The hash is created on YOUR device, privately.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Is it anonymous?</b>\n\n"
        "Yes! You can use it WITHOUT:\n"
        "• Giving your name\n"
        "• Showing your face\n"
        "• Filing a police report\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>How to use it:</b>\n\n"
        "1. Go to takeitdown.ncmec.org\n"
        "2. Follow the instructions\n"
        "3. Create a hash of the fake photo\n"
        "4. Submit to NCMEC\n\n"
        "They'll handle the rest.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Other resources:</b>\n\n"
        "• <b>FBI Tips for Teens:</b> Learn about sextortion\n"
        "• <b>NCMEC CyberTipline:</b> Report the blackmailer\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ <b>Important:</b>\n"
        "• Do NOT pay the blackmailer\n"
        "• Do NOT send more photos\n"
        "• Block them on all platforms\n"
        "• Save screenshots of their messages (evidence)\n\n"
        "You're taking control by using these tools. 💪",
        parse_mode="HTML",
        reply_markup=get_stop_spread_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "teen:education")
async def show_teen_education(callback: CallbackQuery):
    """
    Educational content for teenagers

    What is sextortion?
    How does it work?
    Why you shouldn't feel ashamed
    """

    await callback.message.edit_text(
        "📚 <b>What is Sextortion?</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Definition:</b>\n\n"
        "Sextortion = Sexual + Extortion\n\n"
        "It's when someone threatens to share intimate photos/videos "
        "unless you send them money, more photos, or do what they want.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>How does it usually happen?</b>\n\n"
        "1. Someone contacts you online (Instagram, Snapchat, etc.)\n"
        "2. They seem friendly, attractive, interested in you\n"
        "3. They ask for photos (sometimes you send, sometimes you don't)\n"
        "4. Suddenly they have a \"photo of you\" (often AI-generated!)\n"
        "5. They demand money or more photos, or they'll \"send it to your family\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>The truth about sextortion:</b>\n\n"
        "• <b>89% of blackmail photos are AI-generated fakes</b>\n"
        "• Scammers use this on THOUSANDS of people\n"
        "• They rarely follow through (it's a numbers game)\n"
        "• Paying doesn't stop them - it proves you're a target\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Why you shouldn't feel ashamed:</b>\n\n"
        "1. <b>It's not your fault.</b> Scammers are professionals.\n"
        "2. <b>It happens to everyone.</b> FBI reports 7,000+ cases/year (just reported ones!)\n"
        "3. <b>Adults get scammed too.</b> This isn't about being \"naive\"\n"
        "4. <b>The photo is probably fake.</b> TruthSnap proves this\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>What should you do?</b>\n\n"
        "✅ <b>DO:</b>\n"
        "• Tell a trusted adult\n"
        "• Save screenshots of messages\n"
        "• Block the blackmailer\n"
        "• Report to FBI/NCMEC\n"
        "• Use Take It Down\n\n"
        "❌ <b>DON'T:</b>\n"
        "• Pay money\n"
        "• Send more photos\n"
        "• Keep it secret\n"
        "• Hurt yourself\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Real statistics:</b>\n\n"
        "• 1 in 7 teens experience sextortion (Thorn, 2023)\n"
        "• Only 5% tell their parents (because of shame)\n"
        "• 90% of blackmailers never follow through\n"
        "• The average demand is $500-2000\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>How AI changed sextortion:</b>\n\n"
        "Before: Scammers needed real photos\n"
        "Now: They can make convincing fakes in 30 seconds\n\n"
        "This means:\n"
        "• You might have NEVER sent a photo, and they still have a \"fake you\"\n"
        "• The photo is provably fake (like TruthSnap shows)\n"
        "• It's easier to defend yourself with evidence\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💙 <b>You're going to be okay.</b>\n\n"
        "Thousands of people have been through this.\n"
        "With the right steps (report, block, use Take It Down), "
        "this will be over soon.\n\n"
        "And TruthSnap gave you the proof you need to fight back.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 Back",
                callback_data="teen:back_to_analysis"
            )],
            [InlineKeyboardButton(
                text="🏠 Main Menu",
                callback_data="scenario:select"
            )]
        ])
    )

    await callback.answer()


@router.callback_query(F.data == "teen:back_to_analysis")
async def back_to_teen_analysis(callback: CallbackQuery):
    """Return to teenager analysis results"""

    from bot.keyboards.scenarios import get_teenager_step2_keyboard

    await callback.message.edit_text(
        "🆘 <b>Analysis Complete</b>\n\n"
        "Choose next action:",
        parse_mode="HTML",
        reply_markup=get_teenager_step2_keyboard()
    )
    await callback.answer()
