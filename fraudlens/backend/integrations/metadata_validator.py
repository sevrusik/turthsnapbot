"""
Advanced 10-Layer EXIF Metadata Validator

Based on FraudLensAI detection logic for insurance fraud detection.
Adapted for TruthSnap Bot to detect AI-generated images and manipulation.
"""

import io
import logging
from typing import Dict, List, Optional
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataValidator:
    """
    10-Layer EXIF Validation System

    Performs forensic analysis to detect:
    - AI-generated images
    - Screenshots
    - WhatsApp/Telegram processing
    - Photo editing/manipulation
    - Metadata fabrication
    """

    # Scoring weights
    APPLE_RUNTIME_MISSING = 95  # Smoking gun for fake iPhone photos
    MONITOR_PROFILE_DETECTED = 95  # Screenshot from monitor
    AI_SOFTWARE_DETECTED = 98  # Definitive AI proof
    PHOTOSHOP_EDITING = 85  # Professional manipulation (reduced if in trust list)
    GPS_MISSING = 70  # Suspicious for modern cameras
    TIMESTAMP_MODIFIED = 75  # Post-capture editing
    TEMPORAL_PARADOX = 85  # File created before photo taken
    LENS_MISMATCH = 60  # Inconsistent metadata
    PHYSICS_VIOLATION = 88  # Impossible camera parameters

    # SOFTWARE TRUST LIST - Professional photography tools (not AI generation)
    TRUSTED_PHOTO_SOFTWARE = {
        # RAW processors & color grading
        "lightroom": {"trust_level": "high", "penalty_reduction": 50},
        "capture one": {"trust_level": "high", "penalty_reduction": 50},
        "darktable": {"trust_level": "high", "penalty_reduction": 45},
        "rawtherapee": {"trust_level": "medium", "penalty_reduction": 40},

        # Professional editing (legitimate use cases)
        "photoshop": {"trust_level": "medium", "penalty_reduction": 30},
        "affinity photo": {"trust_level": "medium", "penalty_reduction": 35},

        # Mobile photo apps
        "snapseed": {"trust_level": "medium", "penalty_reduction": 40},
        "vsco": {"trust_level": "medium", "penalty_reduction": 40},
        "lightroom mobile": {"trust_level": "high", "penalty_reduction": 45},
    }

    # AI GENERATION TOOLS - Definitive proof of AI
    AI_GENERATION_TOOLS = [
        "midjourney", "dalle", "dall-e", "stable diffusion",
        "photoshop generative", "adobe firefly", "gemini",
        "imagen", "edited with google ai", "generative fill"
    ]

    def __init__(self, telegram_mode: bool = False, source_platform: str = None):
        """
        Args:
            telegram_mode: If True, adjusts scoring for Telegram context
                          (where EXIF is stripped automatically)
            source_platform: Social media platform (linkedin, instagram, etc.)
                           If set, applies platform-specific normalization
        """
        self.enabled = True
        self.telegram_mode = telegram_mode
        self.source_platform = source_platform

    async def validate(self, image_bytes: bytes) -> Dict:
        """
        Perform comprehensive EXIF validation

        Returns:
            {
                "score": int (0-100, higher = more suspicious),
                "risk_level": str,
                "red_flags": [...],
                "exif_data": {...},
                "checks": [...]
            }
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))

            # Extract EXIF (basic)
            exif_data = self._extract_exif(image)

            # Extract detailed EXIF with exiftool (includes MakerNote fields)
            exiftool_data = self._extract_exiftool(image_bytes)

            # Merge exiftool data into exif_data (exiftool has priority for conflicts)
            # This allows all checks to access both PIL EXIF and exiftool data
            if exiftool_data:
                # Store original exif_data count for logging
                original_count = len(exif_data)
                # Merge - exiftool data takes precedence
                exif_data.update(exiftool_data)
                logger.info(f"[Validator] Merged EXIF data: PIL={original_count} + exiftool={len(exiftool_data)} = {len(exif_data)} total fields")

            # Run 11-layer validation (added Layer 0: Camera Authenticity)
            red_flags = []
            checks = []
            score = 0

            # Layer 0: Camera Authenticity (Serial Numbers) - BONUS for real cameras
            camera_auth_check = self._check_camera_authenticity(exif_data)
            checks.append(camera_auth_check)
            if camera_auth_check["score"] != 0:  # Can be negative (bonus) or positive
                if camera_auth_check["score"] < 0:
                    # Bonus - reduces fraud score
                    score += camera_auth_check["score"]
                    logger.info(f"[Validator] ✅ Camera Authenticity BONUS: {camera_auth_check['score']} pts | reason={camera_auth_check.get('reason')}")
                else:
                    # Penalty (shouldn't happen for this check, but handle it)
                    red_flags.append(camera_auth_check)
                    score += camera_auth_check["score"]
                    logger.info(f"[Validator] Camera Authenticity check: +{camera_auth_check['score']} pts | reason={camera_auth_check.get('reason')}")

            # Layer 1: Apple Hardware Token (use exiftool data)
            apple_check = self._check_apple_runtime(exif_data, exiftool_data)
            checks.append(apple_check)
            if apple_check["score"] > 0:
                red_flags.append(apple_check)
                score += apple_check["score"]
                logger.info(f"[Validator] Apple Runtime check: +{apple_check['score']} pts | reason={apple_check.get('reason')}")

            # Layer 2: Screenshot Detection (Monitor Profile)
            screenshot_check = self._check_screenshot(image, exif_data)
            checks.append(screenshot_check)
            if screenshot_check["score"] > 0:
                red_flags.append(screenshot_check)
                score = max(score, screenshot_check["score"])  # Smoking gun
                logger.info(f"[Validator] Screenshot check: score set to {screenshot_check['score']} pts | reason={screenshot_check.get('reason')}")

            # Layer 3: Software Manipulation
            software_check = self._check_software_manipulation(exif_data)
            checks.append(software_check)
            if software_check["score"] > 0:
                red_flags.append(software_check)
                old_score = score
                score = max(score, software_check["score"])  # Smoking gun for AI
                logger.info(f"[Validator] Software check: {old_score} → {score} pts | adjusted={software_check['score']} | reason={software_check.get('reason')}")

            # Layer 4: GPS Validation
            gps_check = self._check_gps(exif_data)
            checks.append(gps_check)
            if gps_check["score"] > 0:
                red_flags.append(gps_check)
                score += gps_check["score"]
                logger.info(f"[Validator] GPS check: +{gps_check['score']} pts | total={score} | reason={gps_check.get('reason')}")

            # Layer 5: Timestamp Consistency
            timestamp_check = self._check_timestamps(exif_data)
            checks.append(timestamp_check)
            if timestamp_check["score"] > 0:
                red_flags.append(timestamp_check)
                score += timestamp_check["score"]
                logger.info(f"[Validator] Timestamp check: +{timestamp_check['score']} pts | total={score} | reason={timestamp_check.get('reason')}")

            # Layer 6: Google AI Credits (XMP)
            ai_credit_check = self._check_google_ai_credits(image_bytes)
            checks.append(ai_credit_check)
            if ai_credit_check["score"] > 0:
                red_flags.append(ai_credit_check)
                old_score = score
                score = max(score, ai_credit_check["score"])  # Smoking gun
                logger.info(f"[Validator] AI Credit check: {old_score} → {score} pts | reason={ai_credit_check.get('reason')}")

            # Layer 7: Physics/Sensor Validation
            physics_check = self._check_physics(exif_data)
            checks.append(physics_check)
            if physics_check["score"] > 0:
                red_flags.append(physics_check)
                score += physics_check["score"]
                logger.info(f"[Validator] Physics check: +{physics_check['score']} pts | total={score} | reason={physics_check.get('reason')}")

            # Layer 8: Lens Model Consistency
            lens_check = self._check_lens_consistency(exif_data)
            checks.append(lens_check)
            if lens_check["score"] > 0:
                red_flags.append(lens_check)
                score += lens_check["score"]
                logger.info(f"[Validator] Lens check: +{lens_check['score']} pts | total={score} | reason={lens_check.get('reason')}")

            # Layer 9: Format Validation
            format_check = self._check_format(image)
            checks.append(format_check)
            if format_check["score"] > 0:
                red_flags.append(format_check)
                score += format_check["score"]
                logger.info(f"[Validator] Format check: +{format_check['score']} pts | total={score} | reason={format_check.get('reason')}")

            # Layer 10: WhatsApp/Telegram Detection
            messaging_check = self._check_messaging_app(image_bytes, image, exif_data)
            checks.append(messaging_check)
            if messaging_check["score"] > 0:
                red_flags.append(messaging_check)
                old_score = score
                score = max(score, messaging_check["score"])
                logger.info(f"[Validator] Messaging check: {old_score} → {score} pts | reason={messaging_check.get('reason')}")

            # Cap score at 100
            score = min(score, 100)

            # Determine risk level
            risk_level = self._calculate_risk_level(score)

            logger.info(f"[Validator] Final score: {score}/100 | risk={risk_level} | red_flags={len(red_flags)} | telegram_mode={self.telegram_mode}")

            return {
                "score": score,
                "risk_level": risk_level,
                "red_flags": red_flags,
                "exif_data": exif_data,
                "checks": checks,
                "verdict": self._get_verdict(score, red_flags)
            }

        except Exception as e:
            logger.error(f"Metadata validation failed: {e}")
            return {
                "score": 50,
                "risk_level": "UNKNOWN",
                "red_flags": [],
                "exif_data": {},
                "checks": [],
                "error": str(e)
            }

    def _extract_exif(self, image: Image.Image) -> Dict:
        """Extract EXIF data from image using modern getexif() method"""
        exif_data = {}

        try:
            # Use modern getexif() instead of deprecated _getexif()
            exif = image.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    try:
                        exif_data[tag] = str(value)
                    except:
                        pass
        except:
            pass

        # Try piexif for more detailed extraction
        try:
            exif_dict = piexif.load(image.info.get("exif", b""))

            # Extract MakerNotes (Apple Runtime Token)
            if "Exif" in exif_dict:
                for key, value in exif_dict["Exif"].items():
                    if key == 37500:  # MakerNote tag
                        exif_data["MakerNote"] = str(value)

        except:
            pass

        return exif_data

    def _extract_exiftool(self, image_bytes: bytes) -> Dict:
        """
        Extract detailed EXIF using exiftool

        This properly parses MakerNote fields including:
        - Apple RunTimeFlags, RunTimeSincePowerUp
        - AccelerationVector
        - etc.

        Returns:
            Dict with all EXIF fields from exiftool
        """
        try:
            from exiftool import ExifToolHelper
            import tempfile
            import os

            logger.info(f"[Validator] Starting exiftool extraction for {len(image_bytes)} bytes")

            with ExifToolHelper() as et:
                # Write bytes to temporary location for exiftool
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name

                logger.info(f"[Validator] Wrote temp file: {tmp_path}")

                # Extract metadata
                metadata = et.get_metadata(tmp_path)

                # Clean up temp file
                os.unlink(tmp_path)

                if metadata:
                    result = metadata[0]  # First item
                    logger.info(f"[Validator] exiftool extracted {len(result)} fields")

                    # Log Apple-specific fields
                    apple_fields = {k: v for k, v in result.items() if 'Apple' in k or 'RunTime' in k}
                    if apple_fields:
                        logger.info(f"[Validator] Apple fields found: {list(apple_fields.keys())}")
                    else:
                        logger.warning(f"[Validator] No Apple fields found in {len(result)} total fields")

                    return result
                else:
                    logger.warning(f"[Validator] exiftool returned empty metadata")
                    return {}

        except Exception as e:
            logger.error(f"[Validator] exiftool extraction failed: {e}", exc_info=True)

        return {}

    def _check_camera_authenticity(self, exif_data: Dict) -> Dict:
        """
        Layer 0: Camera Authenticity (Serial Numbers)

        Serial numbers = SMOKING GUN for real cameras.
        AI generators CANNOT create valid camera/lens serial numbers.

        Returns NEGATIVE score = BONUS for authentic cameras
        """
        # Extract serial numbers from merged EXIF data
        camera_serial = exif_data.get("SerialNumber") or \
                       exif_data.get("EXIF:SerialNumber") or \
                       exif_data.get("MakerNotes:InternalSerialNumber") or \
                       exif_data.get("MakerNotes:SerialNumber")

        lens_serial = exif_data.get("LensSerialNumber") or \
                     exif_data.get("EXIF:LensSerialNumber") or \
                     exif_data.get("MakerNotes:LensSerialNumber")

        # Check camera make/model for context
        camera_make = exif_data.get("Make", "")
        camera_model = exif_data.get("Model", "")

        # Both camera AND lens serials = highly authentic
        if camera_serial and lens_serial:
            logger.info(f"[Validator] ✅ Camera Authenticity BONUS: Camera SN={camera_serial}, Lens SN={lens_serial}")
            return {
                "layer": "Camera Authenticity",
                "status": "PASS",
                "score": -30,  # NEGATIVE = BONUS (reduces fraud score)
                "reason": f"Camera + Lens serials verified ({camera_make} {camera_model})",
                "severity": "bonus",
                "description": "Serial numbers = smoking gun for real camera (AI cannot fake these)",
                "details": {
                    "camera_serial": str(camera_serial)[:8] + "***",  # Partial for privacy
                    "lens_serial": str(lens_serial)[:6] + "***",
                    "camera": f"{camera_make} {camera_model}"
                }
            }

        # Only camera serial = still good
        if camera_serial:
            logger.info(f"[Validator] ✅ Camera Authenticity: Camera SN={camera_serial}")
            return {
                "layer": "Camera Authenticity",
                "status": "PASS",
                "score": -20,  # NEGATIVE = BONUS
                "reason": f"Camera serial verified ({camera_make} {camera_model})",
                "severity": "bonus",
                "description": "Camera serial number indicates real camera",
                "details": {
                    "camera_serial": str(camera_serial)[:8] + "***",
                    "camera": f"{camera_make} {camera_model}"
                }
            }

        # Only lens serial (rare, but valid)
        if lens_serial:
            logger.info(f"[Validator] ✅ Camera Authenticity: Lens SN={lens_serial}")
            return {
                "layer": "Camera Authenticity",
                "status": "PASS",
                "score": -15,  # NEGATIVE = BONUS
                "reason": "Lens serial verified",
                "severity": "bonus",
                "description": "Lens serial number indicates real lens",
                "details": {
                    "lens_serial": str(lens_serial)[:6] + "***"
                }
            }

        # No serials found - neutral (not all cameras include serials in EXIF)
        return {
            "layer": "Camera Authenticity",
            "status": "N/A",
            "score": 0,
            "reason": "No serial numbers in EXIF (not all cameras include these)"
        }

    def _check_apple_runtime(self, exif_data: Dict, exiftool_data: Dict) -> Dict:
        """
        Layer 1: Apple Hardware Token

        iPhone photos contain unfakeable runtime metadata.
        Missing = screenshot or non-iPhone photo.

        In Telegram mode: Skip this check (Telegram strips all EXIF)
        """
        # In Telegram mode, EXIF absence is expected - skip this check
        if self.telegram_mode and not exif_data:
            return {
                "layer": "Apple Hardware Token",
                "status": "N/A",
                "score": 0,
                "reason": "EXIF stripped by Telegram (expected)"
            }

        make = exif_data.get("Make", "").lower()
        model = exif_data.get("Model", "").lower()
        software = exif_data.get("Software", "")

        logger.info(f"[Validator] EXIF Debug: Make={make} | Model={model} | Software={software}")
        logger.info(f"[Validator] EXIF Debug: Total fields={len(exif_data)} | Has MakerNote={bool(exif_data.get('MakerNote'))}")

        # Check if claimed to be iPhone
        is_iphone = "apple" in make or "iphone" in model

        if not is_iphone:
            return {
                "layer": "Apple Hardware Token",
                "status": "N/A",
                "score": 0,
                "reason": "Not an iPhone photo"
            }

        # Check for Apple Runtime Token using exiftool data
        # These fields are unique to iPhone and cannot be fabricated:
        # - MakerNotes:RunTimeFlags
        # - Composite:RunTimeSincePowerUp
        # - MakerNotes:RunTimeEpoch
        # - MakerNotes:AccelerationVector

        runtime_flags = exiftool_data.get("MakerNotes:RunTimeFlags")
        runtime_since_powerup = exiftool_data.get("Composite:RunTimeSincePowerUp")
        runtime_epoch = exiftool_data.get("MakerNotes:RunTimeEpoch")
        acceleration_vector = exiftool_data.get("MakerNotes:AccelerationVector")

        logger.info(f"[Validator] iPhone detected: {model}")
        logger.info(f"[Validator] Apple Runtime Tokens:")
        logger.info(f"[Validator]   - RunTimeFlags: {runtime_flags}")
        logger.info(f"[Validator]   - RunTimeSincePowerUp: {runtime_since_powerup}")
        logger.info(f"[Validator]   - RunTimeEpoch: {runtime_epoch}")
        logger.info(f"[Validator]   - AccelerationVector: {acceleration_vector}")

        # Check if at least one runtime token is present
        has_runtime = bool(runtime_flags or runtime_since_powerup or runtime_epoch or acceleration_vector)

        if not has_runtime:
            return {
                "layer": "Apple Hardware Token",
                "status": "FAIL",
                "score": self.APPLE_RUNTIME_MISSING,
                "reason": "Missing Apple runtime token (unfakeable hardware marker)",
                "severity": "critical",
                "description": "Original iPhone photos contain processor-generated tokens that cannot be fabricated"
            }

        return {
            "layer": "Apple Hardware Token",
            "status": "PASS",
            "score": 0,
            "reason": f"Valid Apple runtime token detected (RunTimeFlags={runtime_flags})"
        }

    def _check_screenshot(self, image: Image.Image, exif_data: Dict) -> Dict:
        """
        Layer 2: Screenshot Detection

        Checks color profile for monitor signatures.
        """
        # Get ICC profile description
        try:
            icc_profile = image.info.get("icc_profile")
            if icc_profile:
                # Parse profile description
                profile_desc = str(icc_profile[:200])  # First 200 bytes often contain description

                # Check for Display P3 (legitimate iPhone)
                if "display p3" in profile_desc.lower():
                    return {
                        "layer": "Screenshot Detection",
                        "status": "PASS",
                        "score": 0,
                        "reason": "Display P3 - legitimate iPhone camera profile"
                    }

                # Check for monitor profiles
                monitor_keywords = ["LU28R55", "Dell", "HP Z", "Samsung", "monitor", "display"]
                for keyword in monitor_keywords:
                    if keyword.lower() in profile_desc.lower():
                        return {
                            "layer": "Screenshot Detection",
                            "status": "FAIL",
                            "score": self.MONITOR_PROFILE_DETECTED,
                            "reason": f"Monitor profile detected: {keyword}",
                            "severity": "critical",
                            "description": "Image captured from screen, not camera"
                        }
        except:
            pass

        # Check software field
        software = exif_data.get("Software", "").lower()
        screenshot_keywords = ["screenshot", "snipping tool", "screen capture"]

        for keyword in screenshot_keywords:
            if keyword in software:
                return {
                    "layer": "Screenshot Detection",
                    "status": "FAIL",
                    "score": self.MONITOR_PROFILE_DETECTED,
                    "reason": f"Screenshot software detected: {software}",
                    "severity": "critical"
                }

        # Check if all camera data missing (likely screenshot OR stock photo)
        make = exif_data.get("Make")
        model = exif_data.get("Model")
        lens = exif_data.get("LensModel")
        copyright_info = exif_data.get("Copyright", "").lower()

        if not make and not model and not lens and exif_data:
            # Check for stock photo services (they strip EXIF for privacy)
            stock_photo_services = [
                "freepik",
                "shutterstock",
                "getty images",
                "istockphoto",
                "adobe stock",
                "pexels",
                "unsplash",
                "pixabay"
            ]

            for stock_service in stock_photo_services:
                if stock_service in copyright_info:
                    return {
                        "layer": "Screenshot Detection",
                        "status": "PASS",
                        "score": 0,
                        "reason": f"Stock photo from {stock_service} (EXIF stripped by provider)",
                        "description": "Professional stock photo services remove EXIF for privacy"
                    }

            # Not a stock photo - suspicious
            return {
                "layer": "Screenshot Detection",
                "status": "WARN",
                "score": 40,
                "reason": "Missing camera info (possible screenshot)",
                "severity": "medium"
            }

        return {
            "layer": "Screenshot Detection",
            "status": "PASS",
            "score": 0,
            "reason": "No screenshot indicators found"
        }

    def _check_software_manipulation(self, exif_data: Dict) -> Dict:
        """
        Layer 3: Software Manipulation

        Detects professional editing tools and AI generators.
        Now with Software Trust List - differentiates between:
        - AI generation tools (definitive proof)
        - Professional photo editing (legitimate use, reduced penalty)
        - Native apps (acceptable)

        Checks BOTH Software (EXIF) and CreatorTool (XMP) fields
        """
        software = exif_data.get("Software", "").lower()
        # Also check CreatorTool (XMP metadata) - often contains Lightroom info
        creator_tool = exif_data.get("XMP:CreatorTool", "") or exif_data.get("CreatorTool", "")
        if creator_tool:
            creator_tool = str(creator_tool).lower()
        else:
            creator_tool = ""

        # Combine both fields for comprehensive check
        combined_software = software + " " + creator_tool

        # Check 1: AI generators (smoking gun - 100% AI)
        for tool in self.AI_GENERATION_TOOLS:
            if tool in combined_software:
                return {
                    "layer": "Software Manipulation",
                    "status": "FAIL",
                    "score": self.AI_SOFTWARE_DETECTED,
                    "reason": f"AI generation tool detected: {tool}",
                    "severity": "critical",
                    "description": "Definitive proof of AI generation",
                    "requires_visual_proof": False  # Metadata alone is enough
                }

        # Check 2: Trusted professional software (legitimate photography)
        # Check CreatorTool FIRST (higher priority for Lightroom workflow)
        best_match = None
        best_trust_level = None

        for trusted_name, trust_info in self.TRUSTED_PHOTO_SOFTWARE.items():
            if trusted_name in combined_software:
                # Prefer matches from CreatorTool (higher trust for RAW workflow)
                if trusted_name in creator_tool:
                    best_match = (trusted_name, trust_info)
                    best_trust_level = trust_info["trust_level"]
                    break  # CreatorTool match = highest priority
                elif not best_match:
                    best_match = (trusted_name, trust_info)
                    best_trust_level = trust_info["trust_level"]

        if best_match:
            trusted_name, trust_info = best_match
            # Reduce penalty significantly for professional photo tools
            penalty_reduction = trust_info["penalty_reduction"]
            adjusted_score = max(0, self.PHOTOSHOP_EDITING - penalty_reduction)

            # Log which field matched (CreatorTool or Software)
            matched_in = "CreatorTool" if trusted_name in creator_tool else "Software"
            logger.info(
                f"[Validator] Trusted software '{trusted_name}' detected in {matched_in} | "
                f"Base penalty: {self.PHOTOSHOP_EDITING} → Adjusted: {adjusted_score} "
                f"(reduced by {penalty_reduction})"
            )

            return {
                "layer": "Software Manipulation",
                "status": "WARN" if adjusted_score > 20 else "PASS",
                "score": adjusted_score,
                "reason": f"Professional photo software: {trusted_name} (from {matched_in})",
                "severity": "low",
                "description": f"Legitimate photo editing tool (trust level: {trust_info['trust_level']})",
                "requires_visual_proof": True,  # Need FFT/visual evidence for final verdict
                "trust_level": trust_info["trust_level"]
            }

        # Check 3: Other editing tools (medium suspicion)
        suspicious_editing = ["gimp", "paint.net", "pixelmator"]
        for tool in suspicious_editing:
            if tool in combined_software:
                return {
                    "layer": "Software Manipulation",
                    "status": "WARN",
                    "score": 60,
                    "reason": f"Editing software detected: {tool}",
                    "severity": "medium",
                    "requires_visual_proof": True
                }

        # Check 4: Native photo apps (acceptable)
        native_apps = ["ios", "android", "windows photos", "photos app", "google photos"]
        for app in native_apps:
            if app in combined_software:
                return {
                    "layer": "Software Manipulation",
                    "status": "PASS",
                    "score": 0,
                    "reason": f"Native photo app: {software or creator_tool}",
                    "requires_visual_proof": False
                }

        return {
            "layer": "Software Manipulation",
            "status": "PASS",
            "score": 0,
            "reason": "No editing software detected",
            "requires_visual_proof": False
        }

    def _check_gps(self, exif_data: Dict) -> Dict:
        """
        Layer 4: GPS Validation

        Modern smartphones always embed GPS.
        Missing GPS = suspicious.

        In Telegram mode: Skip - Telegram strips GPS
        """
        # In Telegram mode, GPS absence is expected
        if self.telegram_mode and not exif_data:
            return {
                "layer": "GPS Validation",
                "status": "N/A",
                "score": 0,
                "reason": "GPS stripped by Telegram (expected)"
            }

        gps_present = any(key.startswith("GPS") for key in exif_data.keys())

        # Check if modern camera
        model = exif_data.get("Model", "")
        is_modern = any(year in model for year in ["11", "12", "13", "14", "15", "20", "21", "22", "23", "24", "25"])

        if not gps_present and is_modern:
            return {
                "layer": "GPS Validation",
                "status": "FAIL",
                "score": self.GPS_MISSING,
                "reason": "GPS data missing on modern device",
                "severity": "high",
                "description": "Modern smartphones always embed GPS coordinates"
            }

        if not gps_present:
            return {
                "layer": "GPS Validation",
                "status": "WARN",
                "score": 30,
                "reason": "GPS data missing",
                "severity": "medium"
            }

        return {
            "layer": "GPS Validation",
            "status": "PASS",
            "score": 0,
            "reason": "GPS coordinates present"
        }

    def _check_timestamps(self, exif_data: Dict) -> Dict:
        """
        Layer 5: Timestamp Consistency

        Detects post-capture editing via timestamp gaps.

        In Telegram mode: Skip - Telegram strips timestamps
        UPDATED: Professional photo editing (Lightroom) is expected to have large gaps
        """
        # In Telegram mode, timestamp absence is expected
        if self.telegram_mode and not exif_data:
            return {
                "layer": "Timestamp Consistency",
                "status": "N/A",
                "score": 0,
                "reason": "Timestamps stripped by Telegram (expected)"
            }

        datetime_original = exif_data.get("DateTimeOriginal")
        datetime_modified = exif_data.get("DateTime")
        software = exif_data.get("Software", "").lower()

        if not datetime_original or not datetime_modified:
            return {
                "layer": "Timestamp Consistency",
                "status": "WARN",
                "score": 20,
                "reason": "Missing timestamps"
            }

        # Check if trusted photo software was used
        trusted_software_used = any(
            trusted_name in software
            for trusted_name in self.TRUSTED_PHOTO_SOFTWARE.keys()
        )

        try:
            # Parse timestamps
            dt_orig = datetime.strptime(datetime_original, "%Y:%m:%d %H:%M:%S")
            dt_mod = datetime.strptime(datetime_modified, "%Y:%m:%d %H:%M:%S")

            # Check gap
            gap = abs((dt_mod - dt_orig).total_seconds())

            if gap > 3600:  # More than 1 hour
                # If trusted software (Lightroom, etc.) - this is EXPECTED professional workflow
                if trusted_software_used:
                    return {
                        "layer": "Timestamp Consistency",
                        "status": "PASS",
                        "score": 0,
                        "reason": f"Professional editing workflow (modified {gap/3600:.1f}h after capture with trusted software)",
                        "description": "Lightroom/professional editing expected to have time gap"
                    }
                else:
                    # No trusted software - suspicious
                    return {
                        "layer": "Timestamp Consistency",
                        "status": "FAIL",
                        "score": self.TIMESTAMP_MODIFIED,
                        "reason": f"Photo modified {gap/3600:.1f}h after capture (no professional software detected)",
                        "severity": "high",
                        "description": "Time gap without professional editing software is suspicious"
                    }
            elif gap > 60:  # More than 1 minute
                return {
                    "layer": "Timestamp Consistency",
                    "status": "WARN",
                    "score": 10 if trusted_software_used else 30,
                    "reason": f"Minor modification {gap:.0f}s after capture"
                }
        except:
            pass

        return {
            "layer": "Timestamp Consistency",
            "status": "PASS",
            "score": 0,
            "reason": "Timestamps consistent"
        }

    def _check_google_ai_credits(self, image_bytes: bytes) -> Dict:
        """
        Layer 6: Google AI Credits (XMP)

        Google's Gemini/Imagen embed XMP markers.

        FIXED: Search only in XMP metadata section, not entire file
        (to avoid false positives from random text in image)
        """
        try:
            # Extract XMP metadata section only (between <x:xmpmeta> tags)
            image_str = image_bytes.decode('latin-1', errors='ignore')

            # Look for XMP section
            xmp_start = image_str.find('<x:xmpmeta')
            xmp_end = image_str.find('</x:xmpmeta>')

            if xmp_start == -1 or xmp_end == -1:
                # No XMP metadata found - not suspicious
                return {
                    "layer": "Google AI Credits",
                    "status": "PASS",
                    "score": 0,
                    "reason": "No XMP metadata present"
                }

            # Search only within XMP section
            xmp_section = image_str[xmp_start:xmp_end + len('</x:xmpmeta>')].lower()

            # Definitive AI generation markers (must be in XMP)
            ai_markers = {
                "edited with google ai": "Google AI editing marker",
                "trainedalgorithmicmedia": "AI-generated content tag",
                "google ai": "Google AI attribution"
            }

            for marker, description in ai_markers.items():
                if marker in xmp_section:
                    return {
                        "layer": "Google AI Credits",
                        "status": "FAIL",
                        "score": self.AI_SOFTWARE_DETECTED,
                        "reason": f"XMP AI marker: {marker}",
                        "severity": "critical",
                        "description": f"Definitive proof: {description}"
                    }

            # Check for generic "gemini" or "imagen" ONLY if part of AI attribution
            # (avoid false positives from image names, descriptions, etc.)
            # FIXED: Use word boundaries to avoid matching "xmpmm" as "imagen"
            import re

            has_gemini = bool(re.search(r'\bgemini\b', xmp_section))
            has_imagen = bool(re.search(r'\bimagen\b', xmp_section))
            has_ai_context = bool(re.search(r'\b(ai|artificial.?intelligence|trainedalgorithmicmedia)\b', xmp_section))

            if (has_gemini or has_imagen) and has_ai_context:
                # Log XMP section for debugging
                logger.warning(f"[Validator] XMP AI marker detected! gemini={has_gemini}, imagen={has_imagen}, ai_context={has_ai_context}")
                logger.warning(f"[Validator] XMP section preview: {xmp_section[:500]}...")
                return {
                    "layer": "Google AI Credits",
                    "status": "FAIL",
                    "score": self.AI_SOFTWARE_DETECTED,
                    "reason": "Google AI tool detected in XMP (Gemini/Imagen)",
                    "severity": "critical",
                    "description": "AI generation tool attribution found"
                }

        except Exception as e:
            logger.warning(f"[Validator] XMP parsing failed: {e}")

        return {
            "layer": "Google AI Credits",
            "status": "PASS",
            "score": 0,
            "reason": "No Google AI markers in XMP metadata"
        }

    def _check_physics(self, exif_data: Dict) -> Dict:
        """
        Layer 7: Physics/Sensor Validation

        Validates camera parameters are physically possible.
        """
        model = exif_data.get("Model", "").lower()
        f_number = exif_data.get("FNumber")
        iso = exif_data.get("ISOSpeedRatings")

        # iPhone validation
        if "iphone" in model:
            # iPhone apertures are always f/1.5 - f/2.8
            if f_number:
                try:
                    f_val = float(f_number)
                    if f_val < 1.0 or f_val > 3.0:
                        return {
                            "layer": "Physics Validation",
                            "status": "FAIL",
                            "score": self.PHYSICS_VIOLATION,
                            "reason": f"Impossible aperture for iPhone: f/{f_val}",
                            "severity": "critical",
                            "description": "Fabricated EXIF data"
                        }
                except:
                    pass

        return {
            "layer": "Physics Validation",
            "status": "PASS",
            "score": 0,
            "reason": "Camera parameters valid"
        }

    def _check_lens_consistency(self, exif_data: Dict) -> Dict:
        """
        Layer 8: Lens Model Consistency

        Checks if lens matches device.
        """
        model = exif_data.get("Model", "").lower()
        lens_model = exif_data.get("LensModel", "").lower()

        if not lens_model:
            return {
                "layer": "Lens Consistency",
                "status": "PASS",
                "score": 0,
                "reason": "No lens model specified"
            }

        # Check iPhone
        if "iphone" in model:
            if "canon" in lens_model or "nikon" in lens_model:
                return {
                    "layer": "Lens Consistency",
                    "status": "FAIL",
                    "score": self.LENS_MISMATCH,
                    "reason": f"iPhone with DSLR lens: {lens_model}",
                    "severity": "high"
                }

        return {
            "layer": "Lens Consistency",
            "status": "PASS",
            "score": 0,
            "reason": "Lens matches device"
        }

    def _check_format(self, image: Image.Image) -> Dict:
        """
        Layer 9: Format Validation

        PNG/WebP often indicate screenshots or AI generation.
        """
        format = image.format

        if format == "PNG":
            return {
                "layer": "Format Validation",
                "status": "WARN",
                "score": 40,
                "reason": "PNG format (typically screenshots or editing)",
                "severity": "medium"
            }

        if format == "WEBP":
            return {
                "layer": "Format Validation",
                "status": "WARN",
                "score": 50,
                "reason": "WebP format (AI generation or web download)",
                "severity": "medium"
            }

        return {
            "layer": "Format Validation",
            "status": "PASS",
            "score": 0,
            "reason": f"{format} is standard camera format"
        }

    def _check_messaging_app(self, image_bytes: bytes, image: Image.Image, exif_data: Dict) -> Dict:
        """
        Layer 10: WhatsApp/Telegram Detection

        Messaging apps strip ALL forensic metadata.

        UPDATED: Skip check for stock photos (they also strip EXIF)
        UPDATED: Skip check for known social media platforms (LinkedIn, Instagram, etc.)
        """
        # Skip check if source platform is known (LinkedIn, Instagram, etc.)
        if self.source_platform:
            platform_name = self.source_platform.lower()
            # Social media platforms that strip EXIF
            known_platforms = ['linkedin', 'instagram', 'facebook', 'twitter', 'x']
            if platform_name in known_platforms:
                return {
                    "layer": "Messaging App Detection",
                    "status": "PASS",
                    "score": 0,
                    "reason": f"Image from {self.source_platform} (EXIF stripped by platform)",
                    "description": f"{self.source_platform} strips EXIF metadata - this is expected behavior"
                }

        # Check for stock photo services first
        copyright_info = exif_data.get("Copyright", "").lower()
        stock_photo_services = [
            "freepik", "shutterstock", "getty images", "istockphoto",
            "adobe stock", "pexels", "unsplash", "pixabay"
        ]

        for stock_service in stock_photo_services:
            if stock_service in copyright_info:
                return {
                    "layer": "Messaging App Detection",
                    "status": "PASS",
                    "score": 0,
                    "reason": f"Stock photo from {stock_service} (not messaging app)",
                    "description": "Stock photos have stripped EXIF by design"
                }

        width, height = image.size
        max_dimension = max(width, height)
        file_size = len(image_bytes)

        # Calculate bytes per pixel
        bytes_per_pixel = file_size / (width * height)

        confidence = 0.0
        reasons = []

        # Check 1: Complete EXIF absence
        if not exif_data or len(exif_data) < 3:
            confidence += 0.50
            reasons.append("Complete EXIF absence")

        # Check 2: File size in messaging range
        if 50000 <= file_size <= 1500000:  # 50KB - 1.5MB
            confidence += 0.20
            reasons.append(f"File size {file_size/1024:.0f}KB in messaging range")

        # Check 3: Bytes per pixel (aggressive compression)
        if 0.10 <= bytes_per_pixel <= 0.50:
            confidence += 0.10
            reasons.append(f"Aggressive compression ({bytes_per_pixel:.2f} bytes/pixel)")

        # Check 4: WhatsApp resize signature (1600px)
        if max_dimension == 1600:
            confidence += 0.30
            reasons.append("WhatsApp resize signature (1600px)")

        # Check 5: Telegram resize signature (1280px)
        if max_dimension == 1280:
            confidence += 0.30
            reasons.append("Telegram resize signature (1280px)")

        if confidence >= 0.60:
            return {
                "layer": "Messaging App Detection",
                "status": "FAIL",
                "score": 80,
                "reason": f"WhatsApp/Telegram detected (confidence: {confidence:.2f})",
                "severity": "critical",
                "description": "Messaging apps strip all forensic metadata",
                "details": reasons
            }

        return {
            "layer": "Messaging App Detection",
            "status": "PASS",
            "score": 0,
            "reason": "No messaging app processing detected"
        }

    def _calculate_risk_level(self, score: int) -> str:
        """Calculate risk level from score"""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"

    def _get_verdict(self, score: int, red_flags: List[Dict]) -> str:
        """Generate verdict message"""
        if score >= 80:
            return "High probability of AI generation or manipulation"
        elif score >= 60:
            return "Suspicious indicators detected, manual review recommended"
        elif score >= 40:
            return "Some concerns identified, additional verification suggested"
        elif score >= 20:
            return "Minor anomalies detected, likely legitimate"
        else:
            return "Strong indicators of authentic photograph"
