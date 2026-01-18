"""
Photo upload handler

Main handler for user-submitted photos
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import io

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from bot.states import AnalysisStates
from database.repositories.user_repo import UserRepository
from services.storage import S3Storage
from services.queue import TaskQueue
from services.image_validator import ImageValidator, ValidationResult
from config.settings import settings

router = Router()


@router.message(F.photo, AnalysisStates.waiting_for_photo)
async def handle_photo(message: Message, state: FSMContext):
    """
    LEGACY HANDLER - Redirects to scenario selection

    Handle photo upload from user (legacy flow)

    NOTE: This handler is deprecated. New users should use scenario-based flow.
    For backward compatibility, redirects to scenario selection.
    """

    # Redirect to scenario selection
    await state.clear()

    from bot.keyboards.scenarios import get_scenario_selection_keyboard
    from bot.states import ScenarioStates

    await message.answer(
        "👋 <b>Welcome to TruthSnap</b>\n\n"
        "Please choose your scenario first:",
        parse_mode="HTML",
        reply_markup=get_scenario_selection_keyboard()
    )

    await state.set_state(ScenarioStates.selecting_scenario)
    return

    # OLD CODE BELOW (kept for reference, never executed)
    """
    Flow:
    1. Check user can analyze (rate limits)
    2. Download photo
    3. Upload to S3
    4. Enqueue analysis task
    5. Respond immediately
    """

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if user can analyze
    user_repo = UserRepository()
    can_analyze, error_msg = await user_repo.can_user_analyze(user_id)

    if not can_analyze:
        await message.answer(error_msg, parse_mode="HTML")
        await state.set_state(AnalysisStates.awaiting_payment)
        return

    import time
    import logging
    handler_start = time.time()
    logger = logging.getLogger(__name__)

    logger.info(f"[Bot] 📸 STAGE 1: Received photo from user {user_id}")

    # Get photo (largest size)
    photo = message.photo[-1]
    logger.info(f"[Bot]   Photo: {photo.width}x{photo.height} | file_id={photo.file_id[:20]}...")

    # Download photo
    stage_start = time.time()
    file = await message.bot.get_file(photo.file_id)
    file_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, file_bytes)
    file_bytes.seek(0)
    download_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Bot] ⏱️  STAGE 2: Downloaded from Telegram in {download_duration:.0f}ms")

    # STAGE 2.5: Validate image (format, AI detection, screenshot detection, pHash)
    stage_start = time.time()
    validator = ImageValidator(max_size_mb=settings.MAX_PHOTO_SIZE_MB)
    validation_report = await validator.validate(file_bytes.getvalue())
    validation_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Bot] ⏱️  STAGE 2.5: Validation completed in {validation_duration:.0f}ms | result={validation_report.result.value}")

    # Handle validation failures
    if not validation_report.is_valid:
        if validation_report.result == ValidationResult.INVALID_SIZE:
            await message.answer(f"❌ {validation_report.reason}")
        elif validation_report.result == ValidationResult.INVALID_FORMAT:
            await message.answer(
                f"❌ {validation_report.reason}\n\n"
                "Please send JPEG, PNG, or MPO images only."
            )
        elif validation_report.result == ValidationResult.AI_GENERATED:
            await message.answer(
                "🤖 <b>AI-Generated Image Detected</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "This bot verifies <b>real photos</b> only.\n"
                "AI-generated images cannot be analyzed for authenticity.",
                parse_mode="HTML"
            )
        elif validation_report.result == ValidationResult.SCREENSHOT:
            await message.answer(
                "📱 <b>Screenshot Detected</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "Please send <b>original photos</b> from a camera.\n"
                "Screenshots cannot be verified for authenticity.",
                parse_mode="HTML"
            )

        logger.warning(f"[Bot] ❌ Validation failed: {validation_report.reason}")
        return

    # Log validation success with metadata
    logger.info(f"[Bot] ✅ Validation passed | pHash: {validation_report.phash} | format: {validation_report.metadata.get('format')}")

    # Upload to S3 (temporary storage)
    stage_start = time.time()
    s3 = S3Storage()
    s3_key = f"temp/{user_id}/{photo.file_unique_id}.jpg"

    try:
        await s3.upload(file_bytes.getvalue(), s3_key)
        upload_duration = (time.time() - stage_start) * 1000
        logger.info(f"[Bot] ⏱️  STAGE 3: Uploaded to S3 in {upload_duration:.0f}ms | key={s3_key}")
    except Exception as e:
        logger.error(f"[Bot] ❌ S3 upload failed: {e}")
        await message.answer(
            "❌ Upload failed. Please try again."
        )
        return

    # Get user tier for priority
    user = await user_repo.get_user(user_id)
    tier = user['subscription_tier']
    priority = "high" if tier == "pro" else "default"

    logger.info(f"[Bot]   User tier: {tier} | priority: {priority}")

    # Enqueue analysis task
    # Use actual user tier (not "document") for photos
    stage_start = time.time()
    queue = TaskQueue()
    job_id = queue.enqueue_analysis(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message.message_id,
        photo_s3_key=s3_key,
        tier="photo",  # Signal this is a photo (EXIF stripped by Telegram)
        priority=priority
    )
    enqueue_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Bot] ⏱️  STAGE 4: Enqueued job in {enqueue_duration:.0f}ms | job_id={job_id}")

    # Immediate response
    await message.answer(
        "🔍 <b>Your photo is in the queue!</b>\n\n"
        "⏱ Analysis will take 20-30 seconds\n"
        "📲 I'll send you the result when it's ready\n\n"
        f"<code>Job ID: {job_id[:8]}</code>",
        parse_mode="HTML"
    )

    # Decrement daily checks
    await user_repo.decrement_daily_checks(user_id)

    total_duration = (time.time() - handler_start) * 1000
    logger.info(f"[Bot] ✅ Photo handler completed in {total_duration:.0f}ms | job enqueued successfully")

    # State remains waiting_for_photo (user can send more)


@router.message(F.document, AnalysisStates.waiting_for_photo)
async def handle_document(message: Message, state: FSMContext):
    """
    LEGACY HANDLER - Redirects to scenario selection

    Handle document uploads (legacy flow)

    NOTE: This handler is deprecated. Redirects to scenario selection.
    """

    # Redirect to scenario selection
    await state.clear()

    from bot.keyboards.scenarios import get_scenario_selection_keyboard
    from bot.states import ScenarioStates

    await message.answer(
        "👋 <b>Welcome to TruthSnap</b>\n\n"
        "Please choose your scenario first:",
        parse_mode="HTML",
        reply_markup=get_scenario_selection_keyboard()
    )

    await state.set_state(ScenarioStates.selecting_scenario)
    return

    # OLD CODE BELOW (kept for reference, never executed)
    """Handle document uploads (PRESERVES EXIF!)"""

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if it's an image
    if not message.document.mime_type or not message.document.mime_type.startswith('image/'):
        await message.answer(
            "⚠️ Please send <b>image files</b> only.\n\n"
            "Supported: JPEG, PNG, MPO, HEIC, WebP",
            parse_mode="HTML"
        )
        return

    # Check if user can analyze
    user_repo = UserRepository()
    can_analyze, error_msg = await user_repo.can_user_analyze(user_id)

    if not can_analyze:
        await message.answer(error_msg, parse_mode="HTML")
        await state.set_state(AnalysisStates.awaiting_payment)
        return

    import time
    import logging
    handler_start = time.time()
    logger = logging.getLogger(__name__)

    logger.info(f"[Bot] 📎 STAGE 1: Received DOCUMENT from user {user_id} (EXIF preserved!)")
    logger.info(f"[Bot]   File: {message.document.file_name} | size={message.document.file_size} bytes | mime={message.document.mime_type}")

    # Download document (FULL quality, EXIF intact!)
    stage_start = time.time()
    file = await message.bot.get_file(message.document.file_id)
    file_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, file_bytes)
    file_bytes.seek(0)
    download_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Bot] ⏱️  STAGE 2: Downloaded document from Telegram in {download_duration:.0f}ms")

    # STAGE 2.5: Validate document (format, AI detection, screenshot detection, pHash)
    stage_start = time.time()
    validator = ImageValidator(max_size_mb=settings.MAX_PHOTO_SIZE_MB)
    validation_report = await validator.validate(file_bytes.getvalue())
    validation_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Bot] ⏱️  STAGE 2.5: Document validation in {validation_duration:.0f}ms | result={validation_report.result.value}")

    # Handle validation failures
    if not validation_report.is_valid:
        if validation_report.result == ValidationResult.INVALID_SIZE:
            await message.answer(f"❌ {validation_report.reason}")
        elif validation_report.result == ValidationResult.INVALID_FORMAT:
            await message.answer(
                f"❌ {validation_report.reason}\n\n"
                "Please send JPEG, PNG, or MPO images only."
            )
        elif validation_report.result == ValidationResult.AI_GENERATED:
            await message.answer(
                "🤖 <b>AI-Generated Image Detected</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "This bot verifies <b>real photos</b> only.\n"
                "AI-generated images are automatically rejected.\n\n"
                "<i>Detected in EXIF metadata - cannot bypass GPU analysis</i>",
                parse_mode="HTML"
            )
        elif validation_report.result == ValidationResult.SCREENSHOT:
            await message.answer(
                "📱 <b>Screenshot Detected</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "Please send <b>original photos</b> from a camera.\n"
                "Screenshots are automatically rejected.\n\n"
                "<i>Detected in metadata - saves GPU resources</i>",
                parse_mode="HTML"
            )

        logger.warning(f"[Bot] ❌ Document validation failed: {validation_report.reason}")
        return

    # Log validation success
    logger.info(f"[Bot] ✅ Document validated | pHash: {validation_report.phash} | EXIF preserved")

    # Upload to S3
    stage_start = time.time()
    s3 = S3Storage()
    s3_key = f"temp/{user_id}/{message.document.file_unique_id}.{message.document.file_name.split('.')[-1]}"

    try:
        await s3.upload(file_bytes.getvalue(), s3_key)
        upload_duration = (time.time() - stage_start) * 1000
        logger.info(f"[Bot] ⏱️  STAGE 3: Uploaded to S3 in {upload_duration:.0f}ms | key={s3_key}")
    except Exception as e:
        logger.error(f"[Bot] ❌ S3 upload failed: {e}")
        await message.answer("❌ Upload failed. Please try again.")
        return

    # Get user tier
    user = await user_repo.get_user(user_id)
    tier = user['subscription_tier']
    priority = "high" if tier == "pro" else "default"

    # For documents, use "document" tier to signal preserve_exif=True
    # (different from "pro" subscription tier)
    document_tier = "document"

    logger.info(f"[Bot]   User tier: {tier} | priority: {priority} | MODE: DOCUMENT (Full EXIF!)")

    # Enqueue analysis - DETAILED mode (full EXIF validation)
    stage_start = time.time()
    queue = TaskQueue()
    job_id = queue.enqueue_analysis(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message.message_id,
        photo_s3_key=s3_key,
        tier=document_tier,  # Signal this is a document (preserve EXIF)
        priority=priority
    )
    enqueue_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Bot] ⏱️  STAGE 4: Enqueued job in {enqueue_duration:.0f}ms | job_id={job_id}")

    # Response with EXIF info
    await message.answer(
        "✅ <b>File received with FULL metadata!</b>\n\n"
        "🔬 Running <b>detailed analysis</b> with EXIF validation\n"
        "⏱ This will take 20-30 seconds\n"
        "📲 I'll send you the complete result\n\n"
        f"<code>Job ID: {job_id[:8]}</code>\n\n"
        "💡 <b>Note:</b> Files preserve all camera metadata,\n"
        "giving much more accurate results than photos!",
        parse_mode="HTML"
    )

    # Decrement daily checks
    await user_repo.decrement_daily_checks(user_id)

    total_duration = (time.time() - handler_start) * 1000
    logger.info(f"[Bot] ✅ Document handler completed in {total_duration:.0f}ms | EXIF preserved mode")


@router.message(AnalysisStates.waiting_for_photo, F.text & ~F.text.startswith('/'))
async def handle_other(message: Message, state: FSMContext):
    """
    Handle non-photo/non-command text messages in legacy state

    NOTE: This is a legacy handler. New users should use scenario-based flow.
    This handler redirects users to scenario selection.

    IMPORTANT: Filter excludes commands (messages starting with /)
    """

    import logging
    logger = logging.getLogger(__name__)

    user_id = message.from_user.id
    current_state = await state.get_state()

    logger.warning(f"[LEGACY HANDLER] User {user_id} in legacy state: {current_state}")
    logger.warning(f"[LEGACY HANDLER] Message text: {message.text}")
    logger.warning(f"[LEGACY HANDLER] Redirecting to scenario selection...")

    # Clear legacy state and redirect to scenario selection
    await state.clear()

    from bot.keyboards.scenarios import get_scenario_selection_keyboard

    await message.answer(
        "👋 <b>Welcome to TruthSnap</b>\n\n"
        "Please choose your scenario:",
        parse_mode="HTML",
        reply_markup=get_scenario_selection_keyboard()
    )

    from bot.states import ScenarioStates
    await state.set_state(ScenarioStates.selecting_scenario)
