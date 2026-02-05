"""
Image Validation and Screening

Comprehensive pre-processing checks:
- Format validation (JPEG/PNG/HEIC)
- File size limits
- AI-generated image detection (metadata screening)
- Screenshot detection
- Perceptual hash (pHash) for duplicate detection
- HEIC to JPEG conversion
"""

import io
import logging
from typing import Dict, Tuple, Optional
from PIL import Image, ExifTags
import imagehash
from dataclasses import dataclass
from enum import Enum

# Import pillow-heif for HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False
    logging.warning("pillow-heif not installed - HEIC/HEIF support disabled")

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation outcome"""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_SIZE = "invalid_size"
    AI_GENERATED = "ai_generated"
    SCREENSHOT = "screenshot"
    DUPLICATE = "duplicate"


@dataclass
class ImageValidationReport:
    """Complete validation report"""
    is_valid: bool
    result: ValidationResult
    reason: Optional[str] = None
    metadata: Optional[Dict] = None
    phash: Optional[str] = None
    should_skip_gpu: bool = False  # Skip expensive GPU analysis


class ImageValidator:
    """
    Pre-flight validation for uploaded images

    Rejects:
    - Invalid formats (non JPEG/PNG)
    - Oversized files
    - AI-generated images (detected via metadata)
    - Screenshots

    Calculates:
    - Perceptual hash for duplicate detection
    """

    # Supported formats
    ALLOWED_FORMATS = {'JPEG', 'PNG', 'MPO', 'HEIC', 'HEIF'}  # HEIC/HEIF = Apple's High Efficiency Image Format

    # AI generation software signatures
    AI_SOFTWARE_SIGNATURES = [
        'midjourney',
        'dall-e',
        'dalle',
        'stable diffusion',
        'stablediffusion',
        'photoshop generative',
        'firefly',
        'leonardo.ai',
        'bluewillow',
        'nijijourney',
        'artbreeder',
        'craiyon',
        'nightcafe',
        'wombo',
        'deepai',
        'runway',
        'canva ai'
    ]

    # Screenshot indicators
    SCREENSHOT_INDICATORS = {
        'software': [
            'screenshot',
            'snagit',
            'lightshot',
            'greenshot',
            'sharex',
            'gyazo',
            'screenpresso',
            'monosnap',
            'skitch',
            'capture',
            'grab',
            'screencapture'
        ],
        'make': [
            'apple',  # Combined with screenshot software
            'microsoft'  # Combined with snipping tool
        ]
    }

    def __init__(self, max_size_mb: float = 10.0):
        """
        Initialize validator

        Args:
            max_size_mb: Maximum allowed file size in MB
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)

    async def validate(self, image_bytes: bytes) -> ImageValidationReport:
        """
        Comprehensive image validation

        Args:
            image_bytes: Raw image data

        Returns:
            ImageValidationReport with validation results
        """
        try:
            # 1. Size check (fast, do first)
            if len(image_bytes) > self.max_size_bytes:
                size_mb = len(image_bytes) / (1024 * 1024)
                max_mb = self.max_size_bytes / (1024 * 1024)
                return ImageValidationReport(
                    is_valid=False,
                    result=ValidationResult.INVALID_SIZE,
                    reason=f"File too large: {size_mb:.2f}MB (max {max_mb:.0f}MB)"
                )

            # 2. Load image and validate format
            image = Image.open(io.BytesIO(image_bytes))

            # Convert HEIC/HEIF to JPEG for processing
            if image.format in ('HEIC', 'HEIF'):
                if not HEIF_SUPPORT:
                    return ImageValidationReport(
                        is_valid=False,
                        result=ValidationResult.INVALID_FORMAT,
                        reason="HEIC/HEIF format not supported (pillow-heif not installed)"
                    )

                logger.info(f"Converting {image.format} to JPEG for processing...")

                # Preserve EXIF data before conversion
                exif_data = image.info.get('exif', b'')

                # Convert to RGB (HEIC can be in different color modes)
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Convert to JPEG in memory with EXIF preservation
                jpeg_buffer = io.BytesIO()
                if exif_data:
                    image.save(jpeg_buffer, format='JPEG', quality=95, exif=exif_data)
                    logger.info(f"HEIC→JPEG with EXIF preserved ({len(exif_data)} bytes)")
                else:
                    image.save(jpeg_buffer, format='JPEG', quality=95)
                    logger.warning(f"HEIC→JPEG: No EXIF data found in source")

                jpeg_buffer.seek(0)
                image_bytes = jpeg_buffer.getvalue()

                # Reload as JPEG
                image = Image.open(io.BytesIO(image_bytes))
                logger.info(f"HEIC converted to JPEG successfully ({len(image_bytes)} bytes)")

            if image.format not in self.ALLOWED_FORMATS:
                return ImageValidationReport(
                    is_valid=False,
                    result=ValidationResult.INVALID_FORMAT,
                    reason=f"Unsupported format: {image.format}. Only JPEG/PNG/MPO/HEIC allowed."
                )

            # 3. Extract metadata
            metadata = self._extract_metadata(image)

            # 4. Check for AI generation (REJECT immediately, skip GPU)
            is_ai, ai_reason = self._detect_ai_generated(metadata)
            if is_ai:
                logger.warning(f"AI-generated image detected: {ai_reason}")
                return ImageValidationReport(
                    is_valid=False,
                    result=ValidationResult.AI_GENERATED,
                    reason=ai_reason,
                    metadata=metadata,
                    should_skip_gpu=True  # Don't waste GPU on AI images
                )

            # 5. Check for screenshots (REJECT immediately, skip GPU)
            is_screenshot, screenshot_reason = self._detect_screenshot(metadata, image)
            if is_screenshot:
                logger.warning(f"Screenshot detected: {screenshot_reason}")
                return ImageValidationReport(
                    is_valid=False,
                    result=ValidationResult.SCREENSHOT,
                    reason=screenshot_reason,
                    metadata=metadata,
                    should_skip_gpu=True  # Don't waste GPU on screenshots
                )

            # 6. Calculate perceptual hash (for duplicate detection)
            phash = self._calculate_phash(image)

            # All checks passed
            logger.info(f"Image validated: {image.format} {image.size} | pHash: {phash}")
            return ImageValidationReport(
                is_valid=True,
                result=ValidationResult.VALID,
                metadata=metadata,
                phash=phash,
                should_skip_gpu=False
            )

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ImageValidationReport(
                is_valid=False,
                result=ValidationResult.INVALID_FORMAT,
                reason=f"Image processing error: {str(e)}"
            )

    def _extract_metadata(self, image: Image.Image) -> Dict:
        """
        Extract EXIF and other metadata

        Args:
            image: PIL Image object

        Returns:
            Dictionary with metadata
        """
        metadata = {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height
        }

        # For MPO files, mark as multi-picture
        if image.format == 'MPO':
            metadata['is_mpo'] = True
            try:
                # MPO files contain multiple JPEG images
                # Extract number of frames if available
                metadata['n_frames'] = getattr(image, 'n_frames', 1)
            except:
                pass

        # Extract EXIF
        try:
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    try:
                        # Convert to string for consistency
                        metadata[tag] = str(value)
                    except:
                        pass
        except:
            pass

        return metadata

    def _detect_ai_generated(self, metadata: Dict) -> Tuple[bool, Optional[str]]:
        """
        Detect AI-generated images via metadata

        Checks:
        - Software field for AI tools
        - Missing EXIF (suspicious for "photos")
        - Artist/Copyright fields with AI signatures

        Args:
            metadata: Extracted metadata

        Returns:
            (is_ai_generated, reason)
        """
        # Check Software field
        software = metadata.get('Software', '').lower()
        for signature in self.AI_SOFTWARE_SIGNATURES:
            if signature in software:
                return True, f"AI software detected: {metadata.get('Software')}"

        # Check Artist field
        artist = metadata.get('Artist', '').lower()
        for signature in self.AI_SOFTWARE_SIGNATURES:
            if signature in artist:
                return True, f"AI artist tag: {metadata.get('Artist')}"

        # Check Copyright field
        copyright_field = metadata.get('Copyright', '').lower()
        for signature in self.AI_SOFTWARE_SIGNATURES:
            if signature in copyright_field:
                return True, f"AI copyright tag: {metadata.get('Copyright')}"

        # Check UserComment (sometimes AI tools add metadata here)
        user_comment = metadata.get('UserComment', '').lower()
        for signature in self.AI_SOFTWARE_SIGNATURES:
            if signature in user_comment:
                return True, f"AI signature in UserComment"

        return False, None

    def _detect_screenshot(self, metadata: Dict, image: Image.Image) -> Tuple[bool, Optional[str]]:
        """
        Detect screenshots

        Heuristics:
        1. Software field contains screenshot tools
        2. Specific resolution patterns (common screen sizes)
        3. Missing camera EXIF but has software metadata

        Args:
            metadata: Extracted metadata
            image: PIL Image object

        Returns:
            (is_screenshot, reason)
        """
        software = metadata.get('Software', '').lower()
        make = metadata.get('Make', '').lower()
        model = metadata.get('Model', '').lower()

        # Check software field for screenshot tools
        for indicator in self.SCREENSHOT_INDICATORS['software']:
            if indicator in software:
                return True, f"Screenshot tool detected: {metadata.get('Software')}"

        # Check for screenshot keywords in model/make
        if 'screenshot' in model or 'screenshot' in make:
            return True, "Screenshot keyword in device info"

        # Heuristic: Common screenshot resolutions (exact pixels)
        # This catches many desktop/mobile screenshots
        common_screenshot_sizes = {
            (1920, 1080), (2560, 1440), (3840, 2160),  # Desktop
            (1366, 768), (1440, 900), (1600, 900),      # Laptop
            (1080, 1920), (1080, 2340), (1440, 3040),   # Mobile vertical
            (1920, 1080), (2340, 1080), (3040, 1440),   # Mobile horizontal
            (750, 1334), (1125, 2436), (828, 1792),     # iPhone
            (1080, 1920), (1440, 2960), (1440, 3040)    # Android
        }

        if image.size in common_screenshot_sizes:
            # Additional check: no camera EXIF
            has_camera_exif = any(k in metadata for k in ['Make', 'Model', 'LensModel', 'FocalLength'])
            if not has_camera_exif:
                return True, f"Screenshot resolution detected: {image.size[0]}x{image.size[1]}"

        return False, None

    def _calculate_phash(self, image: Image.Image) -> str:
        """
        Calculate perceptual hash (pHash)

        Used for duplicate detection - similar images will have similar hashes

        Args:
            image: PIL Image object

        Returns:
            Hex string of perceptual hash
        """
        try:
            # Use imagehash library for pHash
            # Default hash_size=8 gives 64-bit hash
            phash = imagehash.phash(image, hash_size=8)
            return str(phash)
        except Exception as e:
            logger.error(f"pHash calculation failed: {e}")
            return "0" * 16  # Fallback hash

    def compare_phashes(self, hash1: str, hash2: str) -> int:
        """
        Compare two perceptual hashes

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            Hamming distance (0 = identical, <5 = very similar)
        """
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            return h1 - h2  # Hamming distance
        except:
            return 999  # Error = not similar
