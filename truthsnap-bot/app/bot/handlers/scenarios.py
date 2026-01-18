"""
Scenario-based handlers

Two main flows:
1. Adult Blackmail (👤 I'm being blackmailed)
2. Teenager SOS (🆘 I need help)
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import io
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from bot.states import AdultBlackmailStates, TeenagerSOSStates, ScenarioStates
from bot.keyboards.scenarios import (
    get_scenario_selection_keyboard,
    get_adult_blackmail_step1_keyboard,
    get_teenager_step2_keyboard
)
from database.repositories.user_repo import UserRepository
from services.storage import S3Storage
from services.queue import TaskQueue
from services.image_validator import ImageValidator, ValidationResult
from config.settings import settings

router = Router()
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCENARIO SELECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.callback_query(F.data == "scenario:adult_blackmail")
async def scenario_adult_blackmail(callback: CallbackQuery, state: FSMContext):
    """
    Adult Blackmail Scenario Entry Point

    Flow:
    Step 1: Анализ улики (Upload photo)
    Step 2: Генерация доказательства (Forensic PDF)
    Step 3: Контр-атака (Counter-measures)
    """

    await callback.message.edit_text(
        "👤 <b>Digital Blackmail - Adult/General</b>\n\n"
        "🎯 <b>Objective:</b> Legal evidence & blackmailer blocking\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Step 1: Evidence Analysis</b>\n\n"
        "📸 Please send the blackmail photo NOW\n\n"
        "You will receive:\n"
        "• AI Detection Score (0-100%)\n"
        "• Manipulation Status (AUTHENTIC/MANIPULATED)\n"
        "• SHA-256 Hash for legal proof\n"
        "• Report ID for authorities\n\n"
        "💡 <b>Best accuracy:</b> Send as FILE (not photo)\n"
        "   → Preserves all metadata for forensic analysis",
        parse_mode="HTML"
    )

    await state.set_state(AdultBlackmailStates.waiting_for_evidence)
    await callback.answer()


@router.callback_query(F.data == "scenario:teenager_sos")
async def scenario_teenager_sos(callback: CallbackQuery, state: FSMContext):
    """
    Teenager SOS Scenario Entry Point

    Flow:
    Step 1: Psychological "Stop" (Calming message)
    Step 2: Photo analysis (Empathetic tone)
    Step 3: Ally search (How to tell parents)
    Step 4: Emergency protection (Stop the Spread)
    """

    await callback.message.edit_text(
        "🆘 <b>I Need Help (Teenager Support)</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Step 1: Breathe. You're Safe.</b>\n\n"
        "This happens to many people, and <b>it's not your fault</b>.\n\n"
        "Let's look at the facts together:\n\n"
        "1️⃣ Most blackmail photos are AI-generated fakes\n"
        "2️⃣ You have rights and legal protection\n"
        "3️⃣ Telling a trusted adult makes this easier\n"
        "4️⃣ We can help you stop the spread\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>Next step:</b> Send the photo\n\n"
        "I'll analyze it and show you the technical proof\n"
        "that it's likely fake.",
        parse_mode="HTML"
    )

    await state.set_state(TeenagerSOSStates.psychological_stop)
    await callback.answer("You're safe. Let's take this step by step.")


@router.callback_query(F.data == "scenario:select")
async def scenario_back_to_selection(callback: CallbackQuery, state: FSMContext):
    """
    Return to scenario selection

    Deletes current message and sends fresh welcome message to avoid clutter
    """

    # Delete the current message (analysis result, counter-measures, etc.)
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"[Scenario Select] Could not delete message: {e}")

    # Send fresh welcome message
    await callback.message.answer(
        "👋 <b>Welcome to TruthSnap</b>\n\n"
        "🛡️ <b>AI Deepfake Detection & Blackmail Protection</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Choose your scenario:</b>",
        parse_mode="HTML",
        reply_markup=get_scenario_selection_keyboard()
    )

    # Clear state
    await state.clear()
    await state.set_state(ScenarioStates.selecting_scenario)
    await callback.answer()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADULT BLACKMAIL SCENARIO - Photo Handler
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(F.photo, AdultBlackmailStates.waiting_for_evidence)
async def adult_blackmail_photo(message: Message, state: FSMContext):
    """
    Adult Blackmail - Step 1: Analyze Evidence (Photo)

    Cold, clinical approach:
    - AI Score
    - SHA-256 Hash
    - Report ID
    """

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if user can analyze
    user_repo = UserRepository()
    can_analyze, error_msg = await user_repo.can_user_analyze(user_id)

    if not can_analyze:
        await message.answer(error_msg, parse_mode="HTML")
        return

    import time
    handler_start = time.time()

    logger.info(f"[Adult Blackmail] Photo received from user {user_id}")

    # Get photo
    photo = message.photo[-1]

    # Download
    stage_start = time.time()
    file = await message.bot.get_file(photo.file_id)
    file_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, file_bytes)
    file_bytes.seek(0)
    download_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Adult Blackmail] Downloaded in {download_duration:.0f}ms")

    # Validate
    stage_start = time.time()
    validator = ImageValidator(max_size_mb=settings.MAX_PHOTO_SIZE_MB)
    validation_report = await validator.validate(file_bytes.getvalue())
    validation_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Adult Blackmail] Validated in {validation_duration:.0f}ms | result={validation_report.result.value}")

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
                "🤖 <b>Pre-Analysis: AI Watermark Detected</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "This image was generated by AI software.\n"
                "No forensic analysis needed - it's definitively not a real photo.",
                parse_mode="HTML"
            )
        elif validation_report.result == ValidationResult.SCREENSHOT:
            await message.answer(
                "📱 <b>Screenshot Detected</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "Please send the <b>original photo</b>, not a screenshot.\n"
                "Screenshots cannot be forensically verified.",
                parse_mode="HTML"
            )
        logger.warning(f"[Adult Blackmail] Validation failed: {validation_report.reason}")
        return

    # Upload to S3
    stage_start = time.time()
    s3 = S3Storage()
    s3_key = f"temp/{user_id}/{photo.file_unique_id}.jpg"

    try:
        await s3.upload(file_bytes.getvalue(), s3_key)
        upload_duration = (time.time() - stage_start) * 1000
        logger.info(f"[Adult Blackmail] Uploaded to S3 in {upload_duration:.0f}ms")
    except Exception as e:
        logger.error(f"[Adult Blackmail] S3 upload failed: {e}")
        await message.answer("❌ Upload failed. Please try again.")
        return

    # Get user tier
    user = await user_repo.get_user(user_id)
    tier = user['subscription_tier']
    priority = "high" if tier == "pro" else "default"

    # Enqueue analysis
    stage_start = time.time()
    queue = TaskQueue()
    job_id = queue.enqueue_analysis(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message.message_id,
        photo_s3_key=s3_key,
        tier="photo",
        priority=priority,
        scenario="adult_blackmail"  # Pass scenario context
    )
    enqueue_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Adult Blackmail] Enqueued in {enqueue_duration:.0f}ms | job_id={job_id}")

    # Response - Clinical tone
    await message.answer(
        "🔬 <b>Forensic Analysis Started</b>\n\n"
        "📊 Running multi-layer detection:\n"
        "• AI generation patterns\n"
        "• Face-swap artifacts\n"
        "• EXIF metadata validation\n"
        "• Frequency domain analysis\n\n"
        "⏱ ETA: 20-30 seconds\n"
        f"<code>Job ID: {job_id[:8]}</code>",
        parse_mode="HTML"
    )

    # Decrement daily checks
    await user_repo.decrement_daily_checks(user_id)

    # Save analysis context
    await state.update_data(
        analysis_job_id=job_id,
        scenario="adult_blackmail"
    )

    total_duration = (time.time() - handler_start) * 1000
    logger.info(f"[Adult Blackmail] Handler completed in {total_duration:.0f}ms")


@router.message(F.document, AdultBlackmailStates.waiting_for_evidence)
async def adult_blackmail_document(message: Message, state: FSMContext):
    """
    Adult Blackmail - Step 1: Analyze Evidence (Document)

    PRESERVES EXIF - best for legal proof
    """

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
        return

    import time
    handler_start = time.time()

    logger.info(f"[Adult Blackmail] DOCUMENT received from user {user_id} (EXIF preserved)")

    # Download document
    stage_start = time.time()
    file = await message.bot.get_file(message.document.file_id)
    file_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, file_bytes)
    file_bytes.seek(0)
    download_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Adult Blackmail] Downloaded document in {download_duration:.0f}ms")

    # Validate
    stage_start = time.time()
    validator = ImageValidator(max_size_mb=settings.MAX_PHOTO_SIZE_MB)
    validation_report = await validator.validate(file_bytes.getvalue())
    validation_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Adult Blackmail] Document validated in {validation_duration:.0f}ms")

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
                "🤖 <b>EXIF Analysis: AI Watermark Found</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "Definitive proof: This is AI-generated.\n"
                "Camera metadata confirms it was never captured by a real device.",
                parse_mode="HTML"
            )
        elif validation_report.result == ValidationResult.SCREENSHOT:
            await message.answer(
                "📱 <b>Screenshot Detected in EXIF</b>\n\n"
                f"⚠️ {validation_report.reason}\n\n"
                "Please send the original photo file, not a screenshot.",
                parse_mode="HTML"
            )
        logger.warning(f"[Adult Blackmail] Document validation failed: {validation_report.reason}")
        return

    # Upload to S3
    stage_start = time.time()
    s3 = S3Storage()
    s3_key = f"temp/{user_id}/{message.document.file_unique_id}.{message.document.file_name.split('.')[-1]}"

    try:
        await s3.upload(file_bytes.getvalue(), s3_key)
        upload_duration = (time.time() - stage_start) * 1000
        logger.info(f"[Adult Blackmail] Uploaded to S3 in {upload_duration:.0f}ms")
    except Exception as e:
        logger.error(f"[Adult Blackmail] S3 upload failed: {e}")
        await message.answer("❌ Upload failed. Please try again.")
        return

    # Get user tier
    user = await user_repo.get_user(user_id)
    tier = user['subscription_tier']
    priority = "high" if tier == "pro" else "default"

    # Enqueue analysis - DOCUMENT tier (preserve EXIF)
    stage_start = time.time()
    queue = TaskQueue()
    job_id = queue.enqueue_analysis(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message.message_id,
        photo_s3_key=s3_key,
        tier="document",  # PRESERVE EXIF
        priority=priority,
        scenario="adult_blackmail"  # Pass scenario context
    )
    enqueue_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Adult Blackmail] Enqueued document in {enqueue_duration:.0f}ms | job_id={job_id}")

    # Response - Emphasize EXIF value
    await message.answer(
        "✅ <b>FULL METADATA PRESERVED</b>\n\n"
        "🔬 Running <b>forensic-grade analysis</b>:\n"
        "• EXIF camera fingerprinting\n"
        "• GPS coordinate validation\n"
        "• Edit history timeline\n"
        "• AI generation signatures\n"
        "• Face-swap detection\n\n"
        "⏱ ETA: 20-30 seconds\n"
        f"<code>Job ID: {job_id[:8]}</code>\n\n"
        "💡 This will provide the <b>strongest legal evidence</b>.",
        parse_mode="HTML"
    )

    # Decrement daily checks
    await user_repo.decrement_daily_checks(user_id)

    # Save analysis context
    await state.update_data(
        analysis_job_id=job_id,
        scenario="adult_blackmail"
    )

    total_duration = (time.time() - handler_start) * 1000
    logger.info(f"[Adult Blackmail] Document handler completed in {total_duration:.0f}ms")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEENAGER SOS SCENARIO - Photo Handler
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.message(F.photo, TeenagerSOSStates.psychological_stop)
async def teenager_sos_photo(message: Message, state: FSMContext):
    """
    Teenager SOS - Step 2: Photo Analysis (Empathetic Tone)

    Focus on:
    - Technical errors in fake
    - "This isn't you, it's broken code"
    - Reassurance
    """

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if user can analyze
    user_repo = UserRepository()
    can_analyze, error_msg = await user_repo.can_user_analyze(user_id)

    if not can_analyze:
        await message.answer(error_msg, parse_mode="HTML")
        return

    import time
    handler_start = time.time()

    logger.info(f"[Teenager SOS] Photo received from user {user_id}")

    # Get photo
    photo = message.photo[-1]

    # Download
    stage_start = time.time()
    file = await message.bot.get_file(photo.file_id)
    file_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, file_bytes)
    file_bytes.seek(0)
    download_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Teenager SOS] Downloaded in {download_duration:.0f}ms")

    # Validate
    stage_start = time.time()
    validator = ImageValidator(max_size_mb=settings.MAX_PHOTO_SIZE_MB)
    validation_report = await validator.validate(file_bytes.getvalue())
    validation_duration = (time.time() - stage_start) * 1000

    logger.info(f"[Teenager SOS] Validated in {validation_duration:.0f}ms")

    if not validation_report.is_valid:
        if validation_report.result == ValidationResult.AI_GENERATED:
            await message.answer(
                "✅ <b>Good news!</b>\n\n"
                "This photo has AI watermarks in it.\n"
                "That means it was <b>made by a computer</b>, not a real camera.\n\n"
                "It's not you. It's just code.\n\n"
                "💡 Show this to a trusted adult - they'll understand.",
                parse_mode="HTML"
            )
        elif validation_report.result == ValidationResult.SCREENSHOT:
            await message.answer(
                "📱 I see this is a screenshot.\n\n"
                "Can you send me the <b>original photo</b> instead?\n"
                "That way I can check all the hidden data inside it.",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"❌ {validation_report.reason}")
        return

    # Upload to S3
    s3 = S3Storage()
    s3_key = f"temp/{user_id}/{photo.file_unique_id}.jpg"

    try:
        await s3.upload(file_bytes.getvalue(), s3_key)
    except Exception as e:
        logger.error(f"[Teenager SOS] S3 upload failed: {e}")
        await message.answer("❌ Upload failed. Please try again.")
        return

    # Get user tier
    user = await user_repo.get_user(user_id)
    tier = user['subscription_tier']
    priority = "high" if tier == "pro" else "default"

    # Enqueue analysis
    queue = TaskQueue()
    job_id = queue.enqueue_analysis(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message.message_id,
        photo_s3_key=s3_key,
        tier="photo",
        priority=priority,
        scenario="teenager_sos"  # Pass scenario context
    )

    logger.info(f"[Teenager SOS] Enqueued job {job_id}")

    # Response - Empathetic tone
    await message.answer(
        "✅ <b>I'm analyzing this now</b>\n\n"
        "I'm looking for technical mistakes in the photo.\n"
        "If it's fake (which it probably is), I'll show you the proof.\n\n"
        "⏱ This takes about 20-30 seconds.\n\n"
        "While you wait: Remember that <b>none of this is your fault</b>.",
        parse_mode="HTML"
    )

    # Decrement daily checks
    await user_repo.decrement_daily_checks(user_id)

    # Save context
    await state.update_data(
        analysis_job_id=job_id,
        scenario="teenager_sos"
    )
    await state.set_state(TeenagerSOSStates.waiting_for_photo)

    logger.info(f"[Teenager SOS] Handler completed")


@router.message(F.document, TeenagerSOSStates.psychological_stop)
async def teenager_sos_document(message: Message, state: FSMContext):
    """Teenager SOS - Document upload (same as photo but with EXIF)"""

    user_id = message.from_user.id
    chat_id = message.chat.id

    if not message.document.mime_type or not message.document.mime_type.startswith('image/'):
        await message.answer(
            "📸 I need an image file.\n\n"
            "Can you send the photo again?",
            parse_mode="HTML"
        )
        return

    user_repo = UserRepository()
    can_analyze, error_msg = await user_repo.can_user_analyze(user_id)

    if not can_analyze:
        await message.answer(error_msg, parse_mode="HTML")
        return

    logger.info(f"[Teenager SOS] DOCUMENT received from user {user_id}")

    # Download
    file = await message.bot.get_file(message.document.file_id)
    file_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, file_bytes)
    file_bytes.seek(0)

    # Validate
    validator = ImageValidator(max_size_mb=settings.MAX_PHOTO_SIZE_MB)
    validation_report = await validator.validate(file_bytes.getvalue())

    if not validation_report.is_valid:
        if validation_report.result == ValidationResult.AI_GENERATED:
            await message.answer(
                "✅ <b>This proves it's fake!</b>\n\n"
                "The file has AI signatures inside it.\n"
                "A real camera would never create those.\n\n"
                "It's not you. Someone made this with software.",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"❌ {validation_report.reason}")
        return

    # Upload
    s3 = S3Storage()
    s3_key = f"temp/{user_id}/{message.document.file_unique_id}.{message.document.file_name.split('.')[-1]}"

    try:
        await s3.upload(file_bytes.getvalue(), s3_key)
    except Exception as e:
        logger.error(f"[Teenager SOS] S3 upload failed: {e}")
        await message.answer("❌ Upload failed. Please try again.")
        return

    # Get user tier
    user = await user_repo.get_user(user_id)
    tier = user['subscription_tier']
    priority = "high" if tier == "pro" else "default"

    # Enqueue
    queue = TaskQueue()
    job_id = queue.enqueue_analysis(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message.message_id,
        photo_s3_key=s3_key,
        tier="document",
        priority=priority,
        scenario="teenager_sos"  # Pass scenario context
    )

    await message.answer(
        "✅ <b>I'm checking everything</b>\n\n"
        "Because you sent a file, I can see ALL the hidden data.\n"
        "This makes it easier to prove if it's fake.\n\n"
        "⏱ Give me 20-30 seconds...",
        parse_mode="HTML"
    )

    await user_repo.decrement_daily_checks(user_id)

    await state.update_data(
        analysis_job_id=job_id,
        scenario="teenager_sos"
    )
    await state.set_state(TeenagerSOSStates.waiting_for_photo)


@router.message(AdultBlackmailStates.waiting_for_evidence)
async def adult_blackmail_other(message: Message):
    """Handle non-photo/document messages in Adult scenario"""
    await message.answer(
        "📸 Please send the blackmail photo.\n\n"
        "💡 Send as FILE for best results (preserves metadata)",
        parse_mode="HTML"
    )


@router.message(TeenagerSOSStates.psychological_stop)
async def teenager_sos_other(message: Message):
    """Handle non-photo messages in Teenager scenario"""
    await message.answer(
        "📸 Send me the photo when you're ready.\n\n"
        "There's no rush. Take your time.",
        parse_mode="HTML"
    )
