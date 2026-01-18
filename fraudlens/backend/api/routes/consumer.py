"""
Consumer API Endpoint for TruthSnap Bot

Simplified photo verification without claim context
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import asyncio
from datetime import datetime
import sys
import os
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.core.fraud_detector import FraudDetector
from backend.integrations.watermark_detector import WatermarkDetector
from backend.integrations.metadata import MetadataAnalyzer
from backend.integrations.metadata_validator import MetadataValidator
from backend.integrations.fft_detector import FFTDetector
from backend.integrations.face_swap_detector import FaceSwapDetector
from backend.integrations.visual_watermark_detector import VisualWatermarkDetector
from backend.core.database import save_consumer_analysis
from backend.models.consumer import ConsumerVerificationResponse
from backend.integrations.pdf_report import PDFReportGenerator

router = APIRouter(prefix="/api/v1/consumer", tags=["consumer"])


@router.post("/verify", response_model=ConsumerVerificationResponse)
async def verify_photo(
    image: UploadFile = File(...),
    detail_level: str = Form("basic"),  # "basic" | "detailed"
    preserve_exif: bool = Form(False),  # True = document mode (full EXIF validation)
    generate_pdf: bool = Form(False)  # True = also generate PDF report
):
    """
    Consumer-focused photo verification

    Optimized for TruthSnap bot:
    - No claim text required
    - No location required
    - Focus: Real vs AI-generated
    - Fast response (< 30 seconds)

    Args:
        image: Photo file (JPEG, PNG, HEIC, WebP)
        detail_level: "basic" or "detailed"

    Returns:
        {
            "verdict": "real" | "ai_generated" | "manipulated" | "inconclusive",
            "confidence": 0.95,
            "watermark_detected": true,
            "watermark_analysis": {...},
            "processing_time_ms": 2340
        }
    """

    start_time = datetime.now()
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"[API] 🔍 STAGE 1: Received image | size={image.size if hasattr(image, 'size') else 'unknown'} | content_type={image.content_type}")

        # Validate file
        if not image.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")

        # Read image
        stage_start = datetime.now()
        image_bytes = await image.read()
        stage_duration = (datetime.now() - stage_start).total_seconds() * 1000

        logger.info(f"[API] ⏱️  STAGE 2: Read image in {stage_duration:.0f}ms | bytes={len(image_bytes)}")

        # Size limit: 20MB
        if len(image_bytes) > 20 * 1024 * 1024:
            raise HTTPException(400, "Image too large (max 20MB)")

        # Initialize detectors
        stage_start = datetime.now()
        fraud_detector = FraudDetector()
        watermark_detector = WatermarkDetector()
        visual_watermark_detector = VisualWatermarkDetector()
        metadata_analyzer = MetadataAnalyzer()
        fft_detector = FFTDetector()
        face_swap_detector = FaceSwapDetector()
        # Telegram mode: ON for photos (EXIF stripped), OFF for documents (EXIF preserved)
        telegram_mode = not preserve_exif
        metadata_validator = MetadataValidator(telegram_mode=telegram_mode)
        init_duration = (datetime.now() - stage_start).total_seconds() * 1000

        mode_label = "DOCUMENT (EXIF preserved)" if preserve_exif else "PHOTO (EXIF stripped)"
        logger.info(f"[API] ⏱️  STAGE 3: Initialized detectors in {init_duration:.0f}ms | Mode: {mode_label}")

        # Save image to temp file for visual watermark detection (needs path)
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_path = temp_file.name
        temp_file.write(image_bytes)
        temp_file.close()
        logger.debug(f"[API] Saved temp file for watermark detection: {temp_path}")

        # Run detections in parallel
        stage_start = datetime.now()
        detection_task = asyncio.create_task(
            fraud_detector.detect_ai_generation(image_bytes)
        )
        watermark_task = asyncio.create_task(
            watermark_detector.detect(image_bytes)
        )
        # Visual watermark detector needs file path (synchronous, run in thread)
        visual_watermark_task = asyncio.create_task(
            asyncio.to_thread(visual_watermark_detector.detect_watermark, temp_path)
        )
        metadata_task = asyncio.create_task(
            metadata_analyzer.analyze(image_bytes)
        )
        validation_task = asyncio.create_task(
            metadata_validator.validate(image_bytes)
        )
        fft_task = asyncio.create_task(
            fft_detector.analyze(image_bytes)
        )
        face_swap_task = asyncio.create_task(
            face_swap_detector.analyze(image_bytes)
        )

        logger.info(f"[API] 🚀 STAGE 4: Running 7 detectors in parallel...")

        # Await all
        detection_result, watermark_result, visual_watermark_result, metadata_result, validation_result, fft_result, face_swap_result = await asyncio.gather(
            detection_task,
            watermark_task,
            visual_watermark_task,
            metadata_task,
            validation_task,
            fft_task,
            face_swap_task,
            return_exceptions=True
        )
        detection_duration = (datetime.now() - stage_start).total_seconds() * 1000

        logger.info(f"[API] ⏱️  STAGE 5: All detections completed in {detection_duration:.0f}ms")
        logger.info(f"[API]   ├─ AI Detection: score={detection_result.get('ai_score', 0):.2f}")
        logger.info(f"[API]   ├─ Watermark (C2PA): detected={watermark_result.get('detected', False) if not isinstance(watermark_result, Exception) else False}")
        logger.info(f"[API]   ├─ Visual Watermark (OCR): detected={visual_watermark_result.get('has_watermark', False) if not isinstance(visual_watermark_result, Exception) else False} | type={visual_watermark_result.get('watermark_type', 'N/A') if not isinstance(visual_watermark_result, Exception) else 'ERROR'} | provider={visual_watermark_result.get('provider', 'N/A') if not isinstance(visual_watermark_result, Exception) else 'ERROR'}")
        logger.info(f"[API]   ├─ Metadata: anomalies={len(metadata_result.get('anomalies', [])) if not isinstance(metadata_result, Exception) else 0}")
        logger.info(f"[API]   ├─ Validation: score={validation_result.get('score', 0) if not isinstance(validation_result, Exception) else 0}/100 | risk={validation_result.get('risk_level', 'UNKNOWN') if not isinstance(validation_result, Exception) else 'ERROR'}")
        logger.info(f"[API]   ├─ FFT Analysis: score={fft_result.get('fft_score', 0) if not isinstance(fft_result, Exception) else 0:.2f}")
        logger.info(f"[API]   └─ Face Swap: score={face_swap_result.get('face_swap_score', 0) if not isinstance(face_swap_result, Exception) else 0:.2f} | faces={face_swap_result.get('faces_detected', 0) if not isinstance(face_swap_result, Exception) else 0}")

        # Handle errors
        if isinstance(detection_result, Exception):
            raise HTTPException(500, f"AI detection failed: {str(detection_result)}")

        # Determine final verdict using enhanced validation (10-layer + FFT + Face Swap + Visual Watermarks)
        stage_start = datetime.now()
        verdict = determine_consumer_verdict(
            detection_result,
            watermark_result if not isinstance(watermark_result, Exception) else {"detected": False},
            metadata_result if not isinstance(metadata_result, Exception) else {},
            validation_result if not isinstance(validation_result, Exception) else {"score": 0, "risk_level": "UNKNOWN"},
            fft_result if not isinstance(fft_result, Exception) else {"fft_score": 0.5},
            face_swap_result if not isinstance(face_swap_result, Exception) else {"face_swap_score": 0.0, "faces_detected": 0},
            visual_watermark_result if not isinstance(visual_watermark_result, Exception) else {"detected": False}
        )
        verdict_duration = (datetime.now() - stage_start).total_seconds() * 1000

        logger.info(f"[API] ⏱️  STAGE 6: Determined verdict in {verdict_duration:.0f}ms | verdict={verdict['status']} | confidence={verdict['confidence']:.2f}")

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"[API] ✅ TOTAL: Analysis completed in {processing_time:.0f}ms ({processing_time/1000:.1f}s)")

        # Build response
        response = {
            "verdict": verdict["status"],
            "confidence": verdict["confidence"],
            "watermark_detected": watermark_result.get("detected", False) if not isinstance(watermark_result, Exception) else False,
            "processing_time_ms": int(processing_time)
        }

        # Add C2PA watermark details if found
        if response["watermark_detected"]:
            response["watermark_analysis"] = {
                "type": watermark_result["type"],
                "confidence": watermark_result["confidence"],
                "metadata": watermark_result.get("metadata", {})
            }

        # Add visual watermark details if found
        if not isinstance(visual_watermark_result, Exception) and visual_watermark_result.get("detected"):
            response["visual_watermark"] = {
                "detected": True,
                "type": visual_watermark_result.get("watermark_type"),
                "provider": visual_watermark_result.get("provider"),
                "text_found": visual_watermark_result.get("text_found"),
                "confidence": visual_watermark_result.get("confidence")
            }

        # Add detailed findings if requested
        if detail_level == "detailed":
            response["findings"] = detection_result.get("checks", [])
            response["metadata"] = metadata_result if not isinstance(metadata_result, Exception) else {}
            response["ai_signatures"] = detection_result.get("ai_signatures", {})

            # Add 10-layer validation results
            if not isinstance(validation_result, Exception):
                response["metadata_validation"] = {
                    "score": validation_result.get("score", 0),
                    "risk_level": validation_result.get("risk_level", "UNKNOWN"),
                    "red_flags": validation_result.get("red_flags", []),
                    "checks": validation_result.get("checks", []),
                    "verdict": validation_result.get("verdict", "")
                }

            # Add FFT analysis results
            if not isinstance(fft_result, Exception):
                response["fft_analysis"] = {
                    "score": fft_result.get("fft_score", 0),
                    "checks": fft_result.get("checks", []),
                    "spectral_anomalies": fft_result.get("spectral_anomalies", {})
                }

            # Add Face Swap analysis results
            if not isinstance(face_swap_result, Exception):
                response["face_swap_analysis"] = {
                    "score": face_swap_result.get("face_swap_score", 0),
                    "faces_detected": face_swap_result.get("faces_detected", 0),
                    "checks": face_swap_result.get("checks", []),
                    "artifacts": face_swap_result.get("artifacts", {})
                }

        # Save to database
        await save_consumer_analysis(
            image_hash=compute_hash(image_bytes),
            verdict=response["verdict"],
            confidence=response["confidence"],
            full_result=response
        )

        # Generate PDF if requested
        if generate_pdf:
            try:
                pdf_generator = PDFReportGenerator()
                pdf_bytes = await pdf_generator.generate_report(
                    image_bytes=image_bytes,
                    analysis_result=response,
                    include_image=True
                )

                # Save PDF temporarily and add URL to response
                import base64
                response["pdf_report"] = {
                    "available": True,
                    "size_bytes": len(pdf_bytes),
                    "download_url": "/api/v1/consumer/report/pdf",  # Client should call this endpoint separately
                    "note": "Use /api/v1/consumer/report/pdf endpoint to download full report"
                }

                logger.info(f"[API] Generated PDF report ({len(pdf_bytes)} bytes)")
            except Exception as pdf_error:
                logger.error(f"[API] PDF generation failed: {pdf_error}", exc_info=True)
                response["pdf_report"] = {
                    "available": False,
                    "error": str(pdf_error)
                }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        # Cleanup temp file
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"[API] Cleaned up temp file: {temp_path}")
        except Exception as cleanup_error:
            logger.warning(f"[API] Failed to cleanup temp file: {cleanup_error}")


def determine_consumer_verdict(detection: dict, watermark: dict, metadata: dict, validation: dict, fft: dict, face_swap: dict, visual_watermark: dict = None) -> dict:
    """
    НОВАЯ ЛОГИКА: Weighted Average вместо логики "ИЛИ"

    Вместо "если хоть один детектор закричал - ставим AI",
    используем взвешенное голосование с учетом доверительных уровней.

    Формула:
    Score = (AI_heuristics × 0.3) + (FFT × 0.4) + (Metadata_risk × 0.2) + (Face_swap × 0.1)

    Исключения (smoking guns - срабатывают сразу):
    1. Watermark detection → definitive AI
    2. AI software в EXIF (Midjourney, DALL-E) → definitive AI
    3. Trusted software (Lightroom) → требует визуальных доказательств

    Returns:
        {
            "status": str,
            "confidence": float,
            "reason": str
        }
    """
    import logging
    logger = logging.getLogger(__name__)

    # SMOKING GUN 1a: Visual watermark detection (AI generator text overlay - most obvious)
    if visual_watermark and visual_watermark.get("has_watermark"):
        watermark_type = visual_watermark.get("watermark_type", "unknown")
        provider = visual_watermark.get("provider", "unknown")
        text_found = visual_watermark.get("text_found", "")

        # Check if it's AI generator (not stock photo)
        if provider in ["google", "openai", "midjourney", "stable_diffusion", "adobe", "canva", "craiyon", "nightcafe", "artbreeder", "deepai"]:
            return {
                "status": "ai_generated",
                "confidence": max(0.98, visual_watermark.get("confidence", 0.98)),
                "reason": f"AI generator watermark detected: {provider} ({text_found})"
            }
        elif watermark_type == "stock_photo":
            return {
                "status": "manipulated",
                "confidence": 0.90,
                "reason": f"Stock photo watermark detected: {provider} - unlicensed use"
            }

    # SMOKING GUN 1b: C2PA digital watermark detection (metadata-based)
    if watermark.get("detected"):
        return {
            "status": "ai_generated",
            "confidence": max(0.95, watermark.get("confidence", 0.95)),
            "reason": f"Digital watermark detected ({watermark['type']})"
        }

    # SMOKING GUN 2: AI software in EXIF (definitive proof)
    validation_score = validation.get("score", 0)
    red_flags = validation.get("red_flags", [])

    for flag in red_flags:
        if flag.get("severity") == "critical":
            # AI generation tools - definitive proof
            if ("ai" in flag.get("reason", "").lower() or "google ai" in flag.get("reason", "").lower()) \
               and not flag.get("requires_visual_proof", False):
                return {
                    "status": "ai_generated",
                    "confidence": 0.98,
                    "reason": flag.get("reason", "AI generation markers detected")
                }
            # Screenshot - definitive manipulation
            elif "screenshot" in flag.get("reason", "").lower():
                return {
                    "status": "manipulated",
                    "confidence": 0.95,
                    "reason": "Screenshot detected - not original photo"
                }

    # SMOKING GUN 3: High fraud score (>=80) - Priority-based detection from FraudLensAI
    # This matches the logic in standalone PhotoVerifier (photo_verifier.py:148-162)
    # High fraud scores indicate AI generation or manipulation with high confidence
    if validation_score >= 80:
        verdict_type = "ai_generated" if validation_score >= 90 else "manipulated"
        confidence = min(validation_score / 100.0, 0.98)

        # Build reason from red flags
        reason_parts = [f"EXIF fraud score: {validation_score}/100"]
        if red_flags:
            top_flags = [flag.get("reason", "") for flag in red_flags[:2] if flag.get("reason")]
            if top_flags:
                reason_parts.append(", ".join(top_flags))

        logger.info(f"[Verdict] 🚨 HIGH FRAUD SCORE: {validation_score} → {verdict_type} @ {confidence:.2%}")
        return {
            "status": verdict_type,
            "confidence": confidence,
            "reason": ". ".join(reason_parts)
        }

    # WEIGHTED SCORING: Calculate combined score from all detectors
    ai_heuristic = detection.get("ai_score", 0.0)
    fft_score = fft.get("fft_score", 0.5)
    face_swap_score = face_swap.get("face_swap_score", 0.0)
    faces_detected = face_swap.get("faces_detected", 0)

    # Normalize metadata validation score to 0-1 scale
    metadata_risk = validation_score / 100.0

    # SPECIAL CASE: Trusted software detected (Lightroom, Capture One)
    # Reduce metadata penalty, increase requirement for visual evidence
    trusted_software_detected = False
    for flag in red_flags:
        if flag.get("trust_level") in ["high", "medium"]:
            trusted_software_detected = True
            # Reduce metadata risk significantly
            metadata_risk = max(0, metadata_risk - 0.30)
            logger.info(f"[Verdict] Trusted software detected, reducing metadata risk: {validation_score}/100 → {metadata_risk:.2f}")
            break

    # SPECIAL CASE 2: Stock photo detected (Freepik, Shutterstock, etc.)
    # These are professional photos with stripped EXIF - not manipulated
    stock_photo_detected = False
    for check in validation.get("checks", []):
        reason = check.get("reason", "").lower()
        if "stock photo" in reason or any(service in reason for service in ["freepik", "shutterstock", "getty", "pexels", "unsplash"]):
            stock_photo_detected = True
            # Reduce AI heuristic weight (likely false positive on professional photo)
            logger.info(f"[Verdict] Stock photo detected: {reason}")
            break

    # WEIGHTED AVERAGE FORMULA (IMPROVED)
    # AI heuristics: 35% (basic patterns)
    # FFT: 30% (frequency domain - reduced from 40% due to false positives on JPEG compression)
    # Metadata risk: 25% (EXIF validation - increased importance)
    # Face swap: 10% (specific to deepfakes)
    #
    # Key improvement: Reduced FFT weight (40% → 30%) to avoid false positives
    # on real photos with JPEG compression artifacts or text content

    combined_score = (
        (ai_heuristic * 0.35) +
        (fft_score * 0.30) +
        (metadata_risk * 0.25) +
        (face_swap_score * 0.10 if faces_detected > 0 else 0)
    )

    # BONUS: Good metadata reduces suspicion
    # If metadata risk is LOW (<40) and device is known, boost confidence in "real"
    # Extract camera info directly from metadata EXIF data
    camera_make = metadata.get("exif", {}).get("Make", "").strip() if isinstance(metadata, dict) else ""
    camera_model = metadata.get("exif", {}).get("Model", "").strip() if isinstance(metadata, dict) else ""

    good_metadata_bonus = 0.0
    if validation_score < 40 and (camera_make or camera_model):
        good_metadata_bonus = (40 - validation_score) / 100.0  # Max 0.40 bonus
        logger.info(f"[Verdict] Good metadata bonus: {good_metadata_bonus:.2f} (fraud_score={validation_score}, device={camera_make} {camera_model})")

    logger.info(f"[Verdict] Weighted scores: AI={ai_heuristic:.2f}×0.35={ai_heuristic*0.35:.2f} | "
                f"FFT={fft_score:.2f}×0.30={fft_score*0.30:.2f} | "
                f"Meta={metadata_risk:.2f}×0.25={metadata_risk*0.25:.2f} | "
                f"Face={face_swap_score:.2f}×0.10={face_swap_score*0.10:.2f} | "
                f"Combined={combined_score:.2f}")

    # VERDICT DETERMINATION based on combined score

    # DEFINITIVE AI-GENERATED (score > 0.85)
    if combined_score > 0.85:
        return {
            "status": "ai_generated",
            "confidence": min(0.98, combined_score),
            "reason": f"Strong AI generation indicators (score: {combined_score:.2f})"
        }

    # HIGH PROBABILITY AI-GENERATED (score 0.70-0.85)
    if combined_score > 0.70:
        # Check if this is primarily driven by metadata or visual evidence
        visual_score = (ai_heuristic * 0.3) + (fft_score * 0.4)

        if trusted_software_detected and visual_score < 0.50:
            # Trusted software + low visual score = likely professional photo editing
            return {
                "status": "real",
                "confidence": 0.70,
                "reason": "Professional photo editing detected, but visual analysis shows natural patterns"
            }

        return {
            "status": "ai_generated",
            "confidence": combined_score,
            "reason": f"AI generation likely (combined indicators: {combined_score:.2f})"
        }

    # SUSPICIOUS/MANIPULATED (score 0.50-0.70)
    if combined_score > 0.50:
        # STOCK PHOTO CHECK: Professional stock photos in this range are real
        if stock_photo_detected:
            return {
                "status": "real",
                "confidence": 0.70,
                "reason": "Professional stock photo (Freepik/Shutterstock) - EXIF stripped by provider"
            }

        # TRUSTED SOFTWARE CHECK: Lightroom/professional editing in this range is acceptable
        if trusted_software_detected:
            visual_score = (ai_heuristic * 0.3) + (fft_score * 0.4)

            # If visual evidence is weak but metadata is clean → professional editing
            if visual_score < 0.60:
                return {
                    "status": "real",
                    "confidence": 0.75,
                    "reason": f"Professional photo editing (Lightroom/trusted software) - visual analysis shows natural patterns"
                }

        # Primarily face swap?
        if faces_detected > 0 and face_swap_score > 0.70:
            return {
                "status": "manipulated",
                "confidence": face_swap_score,
                "reason": f"Face swap / deepfake indicators detected"
            }

        # Messaging app processing?
        for flag in red_flags:
            if "whatsapp" in flag.get("reason", "").lower() or "telegram" in flag.get("reason", "").lower():
                return {
                    "status": "manipulated",
                    "confidence": 0.75,
                    "reason": "Messaging app processing - forensic data stripped"
                }

        return {
            "status": "manipulated",
            "confidence": combined_score,
            "reason": f"Suspicious indicators detected (score: {combined_score:.2f})"
        }

    # BORDERLINE/INCONCLUSIVE (score 0.35-0.50)
    if combined_score > 0.35:
        # Check if good metadata can push this to "real"
        if good_metadata_bonus > 0 and combined_score < 0.50:
            # Good EXIF data + known camera = likely real, just noisy compression
            logger.info(f"[Verdict] Applying good metadata bonus: inconclusive → real")
            return {
                "status": "real",
                "confidence": max(0.70, 1.0 - combined_score + good_metadata_bonus),
                "reason": f"Authentic camera photo with complete EXIF data (device verified)"
            }

        return {
            "status": "inconclusive",
            "confidence": 0.50,
            "reason": f"Mixed signals - manual review recommended (score: {combined_score:.2f})"
        }

    # LIKELY REAL (score 0.20-0.35)
    if combined_score > 0.20:
        confidence = min(0.90, 1.0 - combined_score + good_metadata_bonus)
        return {
            "status": "real",
            "confidence": confidence,
            "reason": f"Natural photo characteristics detected (score: {combined_score:.2f})"
        }

    # DEFINITIVE REAL (score < 0.20)
    confidence = min(0.95, max(0.85, 1.0 - combined_score + good_metadata_bonus))
    return {
        "status": "real",
        "confidence": confidence,
        "reason": "Strong indicators of authentic photograph"
    }


def compute_hash(image_bytes: bytes) -> str:
    """Compute SHA-256 hash of image"""
    import hashlib
    return hashlib.sha256(image_bytes).hexdigest()


@router.post("/report/pdf")
async def generate_pdf_report(
    image: UploadFile = File(...),
    detail_level: str = Form("detailed"),
    preserve_exif: bool = Form(False),
    include_image: bool = Form(True)
):
    """
    Generate PDF forensic report

    Returns a downloadable PDF report with comprehensive analysis.

    Args:
        image: Photo file (JPEG, PNG, HEIC, WebP)
        detail_level: "basic" or "detailed"
        preserve_exif: True = document mode (full EXIF validation)
        include_image: Whether to embed analyzed image in PDF

    Returns:
        PDF file download
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"[PDF API] Generating PDF report")

        # Validate file
        if not image.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")

        # Read image
        image_bytes = await image.read()

        # Size limit: 20MB
        if len(image_bytes) > 20 * 1024 * 1024:
            raise HTTPException(400, "Image too large (max 20MB)")

        # Run full analysis (reuse verify endpoint logic)
        fraud_detector = FraudDetector()
        watermark_detector = WatermarkDetector()
        visual_watermark_detector = VisualWatermarkDetector()
        metadata_analyzer = MetadataAnalyzer()
        fft_detector = FFTDetector()
        face_swap_detector = FaceSwapDetector()
        telegram_mode = not preserve_exif
        metadata_validator = MetadataValidator(telegram_mode=telegram_mode)

        # Run detections in parallel
        detection_task = asyncio.create_task(
            fraud_detector.detect_ai_generation(image_bytes)
        )
        watermark_task = asyncio.create_task(
            watermark_detector.detect(image_bytes)
        )
        visual_watermark_task = asyncio.create_task(
            visual_watermark_detector.detect(image_bytes)
        )
        metadata_task = asyncio.create_task(
            metadata_analyzer.analyze(image_bytes)
        )
        validation_task = asyncio.create_task(
            metadata_validator.validate(image_bytes)
        )
        fft_task = asyncio.create_task(
            fft_detector.analyze(image_bytes)
        )
        face_swap_task = asyncio.create_task(
            face_swap_detector.analyze(image_bytes)
        )

        # Await all
        detection_result, watermark_result, visual_watermark_result, metadata_result, validation_result, fft_result, face_swap_result = await asyncio.gather(
            detection_task,
            watermark_task,
            visual_watermark_task,
            metadata_task,
            validation_task,
            fft_task,
            face_swap_task,
            return_exceptions=True
        )

        # Handle errors
        if isinstance(detection_result, Exception):
            raise HTTPException(500, f"AI detection failed: {str(detection_result)}")

        # Determine verdict
        verdict = determine_consumer_verdict(
            detection_result,
            watermark_result if not isinstance(watermark_result, Exception) else {"detected": False},
            metadata_result if not isinstance(metadata_result, Exception) else {},
            validation_result if not isinstance(validation_result, Exception) else {"score": 0, "risk_level": "UNKNOWN"},
            fft_result if not isinstance(fft_result, Exception) else {"fft_score": 0.5},
            face_swap_result if not isinstance(face_swap_result, Exception) else {"face_swap_score": 0.0, "faces_detected": 0},
            visual_watermark_result if not isinstance(visual_watermark_result, Exception) else {"detected": False}
        )

        # Build full analysis result
        analysis_result = {
            "verdict": verdict["status"],
            "confidence": verdict["confidence"],
            "watermark_detected": watermark_result.get("detected", False) if not isinstance(watermark_result, Exception) else False,
            "findings": detection_result.get("checks", []),
            "metadata": metadata_result if not isinstance(metadata_result, Exception) else {},
            "ai_signatures": detection_result.get("ai_signatures", {})
        }

        # Add watermark details if found
        if analysis_result["watermark_detected"]:
            analysis_result["watermark_analysis"] = {
                "type": watermark_result["type"],
                "confidence": watermark_result["confidence"],
                "metadata": watermark_result.get("metadata", {})
            }

        # Add validation results
        if not isinstance(validation_result, Exception):
            analysis_result["metadata_validation"] = {
                "score": validation_result.get("score", 0),
                "risk_level": validation_result.get("risk_level", "UNKNOWN"),
                "red_flags": validation_result.get("red_flags", []),
                "checks": validation_result.get("checks", []),
                "verdict": validation_result.get("verdict", "")
            }

        # Add FFT analysis
        if not isinstance(fft_result, Exception):
            analysis_result["fft_analysis"] = {
                "score": fft_result.get("fft_score", 0),
                "checks": fft_result.get("checks", []),
                "spectral_anomalies": fft_result.get("spectral_anomalies", {})
            }

        # Add Face Swap analysis
        if not isinstance(face_swap_result, Exception):
            analysis_result["face_swap_analysis"] = {
                "score": face_swap_result.get("face_swap_score", 0),
                "faces_detected": face_swap_result.get("faces_detected", 0),
                "checks": face_swap_result.get("checks", []),
                "artifacts": face_swap_result.get("artifacts", {})
            }

        # Generate PDF report
        pdf_generator = PDFReportGenerator()
        pdf_bytes = await pdf_generator.generate_report(
            image_bytes=image_bytes,
            analysis_result=analysis_result,
            include_image=include_image
        )

        logger.info(f"[PDF API] Generated PDF report ({len(pdf_bytes)} bytes)")

        # Return as downloadable file
        filename = f"truthsnap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF API] Failed to generate PDF: {e}", exc_info=True)
        raise HTTPException(500, f"PDF generation failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FraudLens Consumer API"}
