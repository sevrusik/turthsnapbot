"""
ICC Profile Detector for Camera Fingerprinting

ICC (International Color Consortium) profiles are color calibration data embedded in images.
Each camera manufacturer uses unique ICC profiles as a "color fingerprint".

Detection methods:
1. Profile mismatch detection (EXIF camera vs ICC profile vendor)
2. Monitor profile detection (screenshots have monitor ICC profiles)
3. AI generation detection (AI uses standard sRGB without vendor tags)
4. Profile tampering detection (modified or missing ICC)
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageCms
import io

logger = logging.getLogger(__name__)


class ICCProfileDetector:
    """Detect fraud through ICC color profile analysis"""

    def __init__(self):
        self.name = "ICC Profile Detector"

        # Known camera manufacturer ICC profiles
        self.camera_profiles = {
            'apple': {
                'names': ['Display P3', 'Display', 'Apple Display P3'],
                'colorspace': 'RGB',
                'description_contains': ['Display P3', 'Apple'],
                'notes': 'iPhone/iPad use Display P3 (wide gamut)'
            },
            'samsung': {
                'names': ['sRGB IEC61966-2.1', 'sRGB'],
                'colorspace': 'RGB',
                'description_contains': ['sRGB'],
                'notes': 'Samsung uses standard sRGB with custom tags'
            },
            'canon': {
                'names': ['Adobe RGB (1998)', 'sRGB IEC61966-2.1'],
                'colorspace': 'RGB',
                'description_contains': ['Adobe RGB', 'sRGB'],
                'notes': 'Canon DSLR supports both Adobe RGB and sRGB'
            },
            'nikon': {
                'names': ['Adobe RGB (1998)', 'sRGB IEC61966-2.1'],
                'colorspace': 'RGB',
                'description_contains': ['Adobe RGB', 'sRGB'],
                'notes': 'Nikon DSLR supports both Adobe RGB and sRGB'
            },
            'sony': {
                'names': ['sRGB IEC61966-2.1', 'Adobe RGB (1998)'],
                'colorspace': 'RGB',
                'description_contains': ['sRGB', 'Adobe RGB'],
                'notes': 'Sony cameras use sRGB or Adobe RGB'
            },
            'google': {
                'names': ['sRGB IEC61966-2.1'],
                'colorspace': 'RGB',
                'description_contains': ['sRGB'],
                'notes': 'Google Pixel uses standard sRGB'
            }
        }

        # Monitor ICC profiles (screenshot indicators)
        self.monitor_profiles = [
            'Dell', 'LG', 'Samsung', 'HP', 'ASUS', 'BenQ', 'Acer', 'Lenovo',
            'Monitor', 'Display', 'LCD', 'LED', 'UltraFine', 'ThinkPad',
            'MacBook', 'iMac', 'Studio Display', 'Pro Display XDR',
            'U2719', 'P2719', 'S2719', 'U3419', 'U2520', 'U2720',  # Dell models
            '27MD5K', '27UK850', '34WK95U',  # LG models
            'Color LCD'  # Generic monitor profile
        ]

        # Editing software ICC profiles
        self.editing_software_profiles = [
            'Adobe RGB (1998)',
            'ProPhoto RGB',
            'sRGB IEC61966-2.1 (Photoshop)',
            'ColorMatch RGB',
            'Apple RGB',
            'Wide Gamut RGB'
        ]

        logger.info("✅ ICC Profile Detector initialized")

    async def detect(self, image_path: str, claimed_camera: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze ICC color profile for fraud indicators

        Args:
            image_path: Path to image file
            claimed_camera: Camera model from EXIF (e.g., "iPhone 15 Pro", "SM-G991B")

        Returns:
            Detection result with fraud score and details
        """
        try:
            result = {
                'has_anomalies': False,
                'fraud_score': 0,
                'details': {
                    'has_icc_profile': False,
                    'profile_description': None,
                    'profile_vendor': None,
                    'colorspace': None,
                    'profile_size': None,
                    'profile_class': None,
                    'anomalies': []
                }
            }

            # Extract ICC profile
            with Image.open(image_path) as img:
                icc_profile = img.info.get('icc_profile')

                # Check if this is a legitimate screenshot (from EXIF UserComment)
                is_screenshot = False
                try:
                    exif = img.getexif()
                    if exif:
                        user_comment = exif.get(0x9286)  # UserComment tag
                        if user_comment and 'screenshot' in str(user_comment).lower():
                            is_screenshot = True
                            logger.info("📸 Screenshot detected in EXIF - adjusting ICC profile scoring")
                except:
                    pass

                if not icc_profile:
                    # Missing ICC profile is suspicious (most cameras embed ICC)
                    result['details']['has_icc_profile'] = False
                    result['details']['anomalies'].append('Missing ICC profile (suspicious for camera photo)')
                    result['fraud_score'] += 15
                    result['has_anomalies'] = True
                    return result

                result['details']['has_icc_profile'] = True
                result['details']['profile_size'] = len(icc_profile)

                # Parse ICC profile using PIL/ImageCms
                try:
                    profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_profile))

                    # Extract profile metadata
                    profile_description = ImageCms.getProfileDescription(profile)
                    profile_info = ImageCms.getProfileInfo(profile)
                    profile_copyright = ImageCms.getProfileCopyright(profile)
                    profile_manufacturer = ImageCms.getProfileManufacturer(profile)
                    profile_model = ImageCms.getProfileModel(profile)

                    result['details']['profile_description'] = profile_description
                    result['details']['profile_info'] = profile_info
                    result['details']['profile_copyright'] = profile_copyright
                    result['details']['profile_manufacturer'] = profile_manufacturer
                    result['details']['profile_model'] = profile_model

                    # Get color space info
                    try:
                        result['details']['colorspace'] = ImageCms.getColorSpace(profile)
                    except:
                        result['details']['colorspace'] = 'Unknown'

                    # Get rendering intent
                    try:
                        result['details']['rendering_intent'] = ImageCms.getDefaultIntent(profile)
                    except:
                        result['details']['rendering_intent'] = 'Unknown'

                    # Get ICC profile version from raw bytes
                    try:
                        # ICC profile version is at bytes 8-11 (major.minor.bugfix)
                        if len(icc_profile) >= 12:
                            version_major = icc_profile[8]
                            version_minor = icc_profile[9] >> 4
                            version_bugfix = icc_profile[9] & 0x0F
                            profile_version = f"{version_major}.{version_minor}.{version_bugfix}"
                            result['details']['icc_version'] = profile_version
                            logger.info(f"   ICC Version: {profile_version}")
                    except Exception as e:
                        logger.debug(f"Could not extract ICC version: {e}")

                    # Get profile creation date from raw bytes (if available)
                    try:
                        # ICC profile date is at bytes 24-35 (year, month, day, hour, min, sec)
                        if len(icc_profile) >= 36:
                            year = int.from_bytes(icc_profile[24:26], 'big')
                            month = int.from_bytes(icc_profile[26:28], 'big')
                            day = int.from_bytes(icc_profile[28:30], 'big')
                            if year > 0 and month > 0 and day > 0:
                                profile_date = f"{year:04d}-{month:02d}-{day:02d}"
                                result['details']['profile_creation_date'] = profile_date
                                logger.info(f"   Creation Date: {profile_date}")
                    except Exception as e:
                        logger.debug(f"Could not extract ICC date: {e}")

                    logger.info(f"📊 ICC Profile: {profile_description}")
                    logger.info(f"   Manufacturer: {profile_manufacturer}")
                    logger.info(f"   Model: {profile_model}")
                    logger.info(f"   Colorspace: {result['details']['colorspace']}")
                    logger.info(f"   Size: {len(icc_profile)} bytes")

                    # Check 1: Monitor profile detection (screenshot indicator)
                    is_monitor_profile = self._is_monitor_profile(profile_description, profile_manufacturer)
                    if is_monitor_profile:
                        result['details']['is_monitor_profile'] = True

                        if is_screenshot:
                            # Legitimate screenshot - monitor profile is expected
                            result['details']['anomalies'].append(
                                f'Monitor ICC profile detected: {profile_description} - legitimate screenshot (no penalty)'
                            )
                            logger.info(f"📸 Monitor profile expected for screenshot: {profile_description}")
                        else:
                            # Monitor profile but NOT a screenshot = suspicious (photo fraud)
                            result['details']['anomalies'].append(
                                f'Monitor ICC profile detected: {profile_description} - indicates screenshot fraud'
                            )
                            result['fraud_score'] += 40
                            result['has_anomalies'] = True
                            logger.warning(f"🖥️ Monitor profile detected (not screenshot): {profile_description}")

                    # Check 2: Editing software profile detection
                    is_editing_software = self._is_editing_software_profile(profile_description)
                    if is_editing_software:
                        result['details']['is_editing_software_profile'] = True
                        result['details']['anomalies'].append(
                            f'Editing software ICC profile: {profile_description} - photo was edited'
                        )
                        result['fraud_score'] += 25
                        result['has_anomalies'] = True
                        logger.warning(f"✏️ Editing software profile detected: {profile_description}")

                    # Check 3: Camera profile mismatch (if claimed_camera provided)
                    if claimed_camera:
                        mismatch = self._check_camera_profile_mismatch(
                            claimed_camera,
                            profile_description,
                            profile_manufacturer
                        )
                        if mismatch:
                            result['details']['camera_mismatch'] = mismatch
                            result['details']['anomalies'].append(
                                f"Camera/ICC mismatch: EXIF claims '{claimed_camera}' but ICC profile is '{profile_description}'"
                            )
                            result['fraud_score'] += 35
                            result['has_anomalies'] = True
                            logger.warning(f"⚠️ Camera/ICC mismatch: {mismatch['reason']}")

                    # Check 4: Generic sRGB (AI generation indicator)
                    if self._is_generic_srgb(profile_description, profile_manufacturer):
                        result['details']['is_generic_srgb'] = True
                        result['details']['anomalies'].append(
                            'Generic sRGB profile without vendor tags - possible AI generation'
                        )
                        # Lower score - generic sRGB is common in older cameras too
                        result['fraud_score'] += 10
                        logger.info(f"ℹ️ Generic sRGB detected (could be AI or older camera)")

                    # Check 5: Profile size anomalies
                    if len(icc_profile) < 300:
                        result['details']['anomalies'].append(
                            f'Suspiciously small ICC profile ({len(icc_profile)} bytes) - possibly stripped or fake'
                        )
                        result['fraud_score'] += 20
                        result['has_anomalies'] = True

                    elif len(icc_profile) > 1000000:  # >1MB
                        result['details']['anomalies'].append(
                            f'Unusually large ICC profile ({len(icc_profile)} bytes) - suspicious'
                        )
                        result['fraud_score'] += 15
                        result['has_anomalies'] = True

                except Exception as profile_error:
                    logger.warning(f"Could not parse ICC profile: {profile_error}")
                    result['details']['anomalies'].append('Corrupted or invalid ICC profile')
                    result['fraud_score'] += 25
                    result['has_anomalies'] = True

            logger.info(f"✅ ICC analysis complete: score={result['fraud_score']}, anomalies={len(result['details']['anomalies'])}")
            return result

        except Exception as e:
            logger.error(f"ICC profile detection failed: {e}", exc_info=True)
            return {
                'has_anomalies': False,
                'fraud_score': 0,
                'details': {
                    'error': str(e)
                }
            }

    def _is_monitor_profile(self, description: str, manufacturer: str) -> bool:
        """Check if ICC profile is from a monitor/display (screenshot indicator)"""
        if not description and not manufacturer:
            return False

        text = f"{description} {manufacturer}".lower()

        for monitor_keyword in self.monitor_profiles:
            if monitor_keyword.lower() in text:
                return True

        return False

    def _is_editing_software_profile(self, description: str) -> bool:
        """Check if ICC profile is from editing software (Photoshop, etc.)"""
        if not description:
            return False

        # Check for exact matches (case-insensitive)
        for software_profile in self.editing_software_profiles:
            if software_profile.lower() in description.lower():
                # But exclude if it's just standard sRGB (cameras use this too)
                if 'photoshop' in description.lower() or 'adobe' in description.lower():
                    return True

        return False

    def _check_camera_profile_mismatch(
        self,
        claimed_camera: str,
        profile_description: str,
        profile_manufacturer: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if EXIF camera claim matches ICC profile

        Returns mismatch details if found, None otherwise
        """
        if not claimed_camera or not profile_description:
            return None

        claimed_lower = claimed_camera.lower()
        profile_lower = profile_description.lower()
        manufacturer_lower = (profile_manufacturer or '').lower()

        # Detect claimed manufacturer
        claimed_vendor = None
        if 'iphone' in claimed_lower or 'ipad' in claimed_lower or 'apple' in claimed_lower:
            claimed_vendor = 'apple'
        elif 'samsung' in claimed_lower or 'sm-' in claimed_lower or 'galaxy' in claimed_lower:
            claimed_vendor = 'samsung'
        elif 'canon' in claimed_lower or 'eos' in claimed_lower:
            claimed_vendor = 'canon'
        elif 'nikon' in claimed_lower:
            claimed_vendor = 'nikon'
        elif 'sony' in claimed_lower or 'ilce' in claimed_lower or 'dsc' in claimed_lower:
            claimed_vendor = 'sony'
        elif 'pixel' in claimed_lower:
            claimed_vendor = 'google'

        if not claimed_vendor:
            return None  # Unknown camera, can't verify

        # Get expected ICC profiles for this manufacturer
        expected_profiles = self.camera_profiles.get(claimed_vendor, {})
        expected_keywords = expected_profiles.get('description_contains', [])

        # Check if profile matches expected
        profile_matches = False
        for keyword in expected_keywords:
            if keyword.lower() in profile_lower or keyword.lower() in manufacturer_lower:
                profile_matches = True
                break

        if not profile_matches:
            # Special case: Apple devices should have Display P3
            if claimed_vendor == 'apple':
                if 'display p3' not in profile_lower and 'apple' not in manufacturer_lower:
                    return {
                        'claimed_vendor': 'Apple',
                        'claimed_camera': claimed_camera,
                        'expected_profile': 'Display P3',
                        'actual_profile': profile_description,
                        'reason': f"Apple devices should use Display P3, but found '{profile_description}'"
                    }

            # General mismatch
            return {
                'claimed_vendor': claimed_vendor.title(),
                'claimed_camera': claimed_camera,
                'expected_profile': ', '.join(expected_keywords),
                'actual_profile': profile_description,
                'reason': f"{claimed_vendor.title()} camera should use {expected_keywords[0]}, but found '{profile_description}'"
            }

        return None

    def _is_generic_srgb(self, description: str, manufacturer: str) -> bool:
        """
        Check if ICC profile is generic sRGB (AI generation indicator)

        Cameras usually add vendor-specific tags to sRGB profiles.
        Pure "sRGB IEC61966-2.1" without vendor info suggests AI generation.
        """
        if not description:
            return False

        desc_lower = description.lower()
        manufacturer_lower = (manufacturer or '').lower()

        # Exact generic sRGB profile
        is_generic_srgb = (
            desc_lower == 'srgb iec61966-2.1' or
            desc_lower == 'srgb' or
            desc_lower == 'srgb iec61966-2-1'
        )

        # No vendor information
        has_vendor_info = bool(manufacturer_lower and manufacturer_lower != 'none')

        return is_generic_srgb and not has_vendor_info
