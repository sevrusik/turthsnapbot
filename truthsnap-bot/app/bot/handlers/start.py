"""
Start and help command handlers
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from bot.states import ScenarioStates
from database.repositories.user_repo import UserRepository
from bot.keyboards.scenarios import get_scenario_selection_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Handle /start command

    New scenario-based flow:
    - Adult Blackmail (👤 I'm being blackmailed)
    - Teenager SOS (🆘 I need help)
    """

    import logging
    logger = logging.getLogger(__name__)

    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # DEBUG: Check current state
    current_state = await state.get_state()
    logger.info(f"[START] User {user_id} current state: {current_state}")

    # Register or update user
    user_repo = UserRepository()
    await user_repo.create_or_update_user(
        telegram_id=user_id,
        username=username,
        first_name=first_name
    )

    # Clear any existing state first
    await state.clear()
    logger.info(f"[START] State cleared for user {user_id}")

    # Welcome message with scenario selection
    await message.answer(
        "👋 <b>Welcome to TruthSnap</b>\n\n"
        "🛡️ <b>AI Deepfake Detection & Blackmail Protection</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚨 <b>If you're being blackmailed:</b>\n"
        "• Get instant photo verification\n"
        "• Generate forensic proof for authorities\n"
        "• Access counter-measure strategies\n\n"
        "✅ 127,453 photos verified this month\n"
        "✅ 89% detected as AI-generated\n"
        "✅ Trusted by victims in 47 countries\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Choose your scenario:</b>",
        parse_mode="HTML",
        reply_markup=get_scenario_selection_keyboard()
    )

    # Set scenario selection state
    await state.set_state(ScenarioStates.selecting_scenario)
    logger.info(f"[START] Set state to ScenarioStates.selecting_scenario for user {user_id}")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""

    await message.answer(
        "<b>📖 How to use TruthSnap:</b>\n\n"
        "1. Send any photo to verify\n"
        "2. Wait 20-30 seconds for analysis\n"
        "3. Receive verdict + confidence score\n\n"
        "<b>Commands:</b>\n"
        "/start - Start bot\n"
        "/help - Show this help\n"
        "/subscribe - Upgrade to Pro\n"
        "/status - Check your plan\n"
        "/cancel - Cancel subscription\n\n"
        "<b>Free Tier:</b>\n"
        "• 3 checks per day\n"
        "• Basic verdict\n\n"
        "<b>Pro Tier ($9.99/mo):</b>\n"
        "• Unlimited checks\n"
        "• Detailed forensic reports\n"
        "• PDF downloads\n"
        "• Priority processing\n\n"
        "Need help? Contact: /support",
        parse_mode="HTML"
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Show user status and usage"""

    user_id = message.from_user.id
    user_repo = UserRepository()
    user = await user_repo.get_user(user_id)

    if not user:
        await message.answer("User not found. Send /start to register.")
        return

    tier = user['subscription_tier'].upper()
    checks_remaining = user['daily_checks_remaining']
    total_checks = user['total_checks']

    status_text = f"<b>📊 Your Status</b>\n\n"
    status_text += f"<b>Plan:</b> {tier}\n"

    if tier == "FREE":
        status_text += f"<b>Checks today:</b> {checks_remaining}/3\n"
    else:
        status_text += f"<b>Checks today:</b> Unlimited ✅\n"
        if user['subscription_expires_at']:
            status_text += f"<b>Expires:</b> {user['subscription_expires_at'].strftime('%Y-%m-%d')}\n"

    status_text += f"<b>Total checks:</b> {total_checks}\n\n"

    if tier == "FREE":
        status_text += "💎 Upgrade to Pro: /subscribe"

    await message.answer(status_text, parse_mode="HTML")


@router.message(Command("support"))
async def cmd_support(message: Message):
    """Support information"""

    await message.answer(
        "<b>🆘 Support</b>\n\n"
        "Need help? Contact us:\n\n"
        "📧 Email: support@truthsnap.ai\n"
        "🐦 Twitter: @TruthSnapBot\n"
        "💬 Telegram: @TruthSnapSupport\n\n"
        "Response time: < 24 hours",
        parse_mode="HTML"
    )
