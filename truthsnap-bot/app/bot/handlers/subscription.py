"""
Subscription and payment handlers
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from database.repositories.user_repo import UserRepository

router = Router()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """Show subscription options"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💎 Subscribe Pro ($9.99/mo)",
            callback_data="subscribe_pro"
        )],
        [InlineKeyboardButton(
            text="💳 Pay per use ($2.99)",
            callback_data="payperuse"
        )],
        [InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="cancel"
        )]
    ])

    await message.answer(
        "<b>💎 TruthSnap Pro</b>\n\n"
        "<b>Features:</b>\n"
        "✅ Unlimited photo checks\n"
        "✅ Detailed forensic reports\n"
        "✅ PDF downloads with legal disclaimers\n"
        "✅ Priority processing (10-15 sec)\n"
        "✅ Analysis history\n"
        "✅ Email support\n\n"
        "<b>Price:</b> $9.99/month\n"
        "<b>Cancel anytime</b>\n\n"
        "Or pay $2.99 per detailed check",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "subscribe_pro")
async def process_subscription(callback: CallbackQuery):
    """Process Pro subscription"""

    # TODO: Implement actual Stripe checkout
    # For MVP, this is a stub

    await callback.message.edit_text(
        "💎 <b>Subscribe to Pro</b>\n\n"
        "🚧 <b>Payment integration coming soon!</b>\n\n"
        "For now, contact support to upgrade manually:\n"
        "📧 support@truthsnap.ai\n\n"
        "Include your Telegram user ID: <code>{}</code>".format(callback.from_user.id),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "payperuse")
async def process_payperuse(callback: CallbackQuery):
    """Process one-time payment"""

    # TODO: Implement actual Stripe payment
    # For MVP, this is a stub

    await callback.message.edit_text(
        "💳 <b>Pay per Use</b>\n\n"
        "🚧 <b>Payment integration coming soon!</b>\n\n"
        "For now, contact support:\n"
        "📧 support@truthsnap.ai\n\n"
        "Include your Telegram user ID: <code>{}</code>".format(callback.from_user.id),
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel_subscription(message: Message):
    """Cancel subscription"""

    user_id = message.from_user.id
    user_repo = UserRepository()
    user = await user_repo.get_user(user_id)

    if not user or user['subscription_tier'] != 'pro':
        await message.answer("You don't have an active subscription.")
        return

    # Confirm cancellation
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Yes, cancel subscription",
            callback_data="confirm_cancel"
        )],
        [InlineKeyboardButton(
            text="❌ No, keep subscription",
            callback_data="cancel_action"
        )]
    ])

    await message.answer(
        "⚠️ <b>Cancel Subscription?</b>\n\n"
        "Your subscription will remain active until the end of "
        "the current billing period.\n\n"
        "Are you sure?",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "confirm_cancel")
async def confirm_cancel_subscription(callback: CallbackQuery):
    """Confirm subscription cancellation"""

    user_id = callback.from_user.id
    user_repo = UserRepository()

    # Downgrade to free
    await user_repo.downgrade_to_free(user_id)

    await callback.message.edit_text(
        "✅ <b>Subscription Cancelled</b>\n\n"
        "You've been downgraded to the Free tier.\n\n"
        "We're sorry to see you go! 😢\n\n"
        "Feedback: support@truthsnap.ai",
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery):
    """Cancel any action"""

    await callback.message.delete()
    await callback.answer("Cancelled")
