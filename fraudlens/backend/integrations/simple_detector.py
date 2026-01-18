"""
Simple AI Detection Heuristics (MVP)

Basic checks that give more realistic results than random hash.
Not ML-based, but better than nothing!
"""

from PIL import Image
import io
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def detect_ai_basic(image_bytes: bytes) -> Dict:
    """
    Basic AI detection using simple heuristics

    Checks:
    1. EXIF metadata presence (real photos usually have it)
    2. Noise levels (AI = too clean, real = natural noise)
    3. Color distribution (AI often has unnatural saturation)
    4. Compression artifacts (AI = minimal, real = visible)

    Returns:
        {
            "ai_score": float (0-1),
            "checks": list,
            "primary_reason": str
        }
    """

    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to numpy array for analysis
        img_array = np.array(img.convert('RGB'))

        checks = []

        # CHECK 1: EXIF Metadata Analysis
        exif_score = check_exif(img)
        checks.append({
            "layer": "EXIF Metadata",
            "status": "FAIL" if exif_score > 0.5 else "PASS",
            "score": exif_score,
            "reason": "Missing camera metadata" if exif_score > 0.5 else "Camera metadata present",
            "confidence": 0.7
        })

        # CHECK 2: Noise Pattern Analysis
        noise_score = check_noise_pattern(img_array)
        checks.append({
            "layer": "Noise Pattern",
            "status": "FAIL" if noise_score > 0.5 else "PASS",
            "score": noise_score,
            "reason": "Unnaturally clean image" if noise_score > 0.5 else "Natural noise detected",
            "confidence": 0.75
        })

        # CHECK 3: Color Distribution
        color_score = check_color_distribution(img_array)
        checks.append({
            "layer": "Color Distribution",
            "status": "FAIL" if color_score > 0.5 else "PASS",
            "score": color_score,
            "reason": "Unnatural color saturation" if color_score > 0.5 else "Natural color range",
            "confidence": 0.65
        })

        # CHECK 4: Smoothness (AI tends to over-smooth)
        smooth_score = check_smoothness(img_array)
        checks.append({
            "layer": "Gradient Smoothness",
            "status": "FAIL" if smooth_score > 0.5 else "PASS",
            "score": smooth_score,
            "reason": "Over-smoothed gradients" if smooth_score > 0.5 else "Natural texture variation",
            "confidence": 0.8
        })

        # Calculate weighted average
        weights = [0.7, 0.75, 0.65, 0.8]  # confidence values
        ai_score = sum(c["score"] * w for c, w in zip(checks, weights)) / sum(weights)

        # Determine primary reason
        if ai_score > 0.7:
            primary_reason = "Multiple AI generation indicators detected"
        elif ai_score > 0.5:
            primary_reason = "Some suspicious patterns found"
        elif ai_score < 0.3:
            primary_reason = "Strong indicators of real photograph"
        else:
            primary_reason = "Mixed signals, unclear origin"

        return {
            "ai_score": ai_score,
            "primary_reason": primary_reason,
            "checks": checks,
            "ai_signatures": {
                "midjourney": False,  # Can't detect specific tools yet
                "dalle": False,
                "stable_diffusion": False,
                "unknown_ai": ai_score > 0.6
            }
        }

    except Exception as e:
        logger.error(f"Simple detection failed: {e}")
        # Fallback to safe default
        return {
            "ai_score": 0.5,
            "primary_reason": "Analysis failed, inconclusive",
            "checks": [],
            "ai_signatures": {}
        }


def check_exif(img: Image.Image) -> float:
    """
    Check EXIF metadata

    Real photos from cameras/phones have rich EXIF.
    AI-generated images usually lack this.
    """
    try:
        exif = img.getexif()

        if not exif or len(exif) < 3:
            # No EXIF or very minimal = suspicious
            return 0.8

        # Check for camera-specific tags
        camera_tags = [271, 272, 305]  # Make, Model, Software
        has_camera_info = any(tag in exif for tag in camera_tags)

        if has_camera_info:
            return 0.1  # Likely real camera photo
        else:
            return 0.6  # Has EXIF but no camera info = suspicious

    except:
        return 0.7  # Can't read EXIF = suspicious


def check_noise_pattern(img_array: np.ndarray) -> float:
    """
    Analyze noise levels

    Real photos have natural sensor noise.
    AI images are often too clean.
    """
    try:
        # Convert to grayscale for noise analysis
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Calculate local variance (noise indicator)
        # Use 3x3 windows
        from scipy.ndimage import uniform_filter

        local_mean = uniform_filter(gray, size=3)
        local_var = uniform_filter(gray**2, size=3) - local_mean**2

        avg_variance = np.mean(local_var)

        # Typical ranges (empirical):
        # Real photos: variance 20-200
        # AI generated: variance < 10 (too clean)

        if avg_variance < 5:
            return 0.9  # Way too clean = AI
        elif avg_variance < 15:
            return 0.7  # Suspiciously clean
        elif avg_variance > 50:
            return 0.1  # Natural noise
        else:
            return 0.4  # Borderline

    except:
        # If scipy not available, use simpler method
        try:
            # Standard deviation as noise proxy
            std = np.std(img_array)

            if std < 10:
                return 0.8
            elif std > 30:
                return 0.2
            else:
                return 0.5
        except:
            return 0.5  # Can't determine


def check_color_distribution(img_array: np.ndarray) -> float:
    """
    Check color saturation and distribution

    AI often over-saturates or has unnatural color distributions.
    """
    try:
        # Convert to HSV to check saturation
        from PIL import Image

        img_pil = Image.fromarray(img_array.astype('uint8'))
        hsv = img_pil.convert('HSV')
        hsv_array = np.array(hsv)

        # Get saturation channel (index 1)
        saturation = hsv_array[:, :, 1]

        # Check average saturation
        avg_sat = np.mean(saturation)

        # Typical ranges:
        # Real photos: 50-150
        # AI over-saturated: > 180
        # AI under-saturated: < 30

        if avg_sat > 180:
            return 0.8  # Over-saturated = likely AI
        elif avg_sat < 30:
            return 0.7  # Under-saturated = suspicious
        elif 80 < avg_sat < 140:
            return 0.2  # Natural range
        else:
            return 0.4  # Borderline

    except:
        return 0.5  # Can't determine


def check_smoothness(img_array: np.ndarray) -> float:
    """
    Check gradient smoothness

    AI tends to create unnaturally smooth gradients.
    Real photos have more texture variation.
    """
    try:
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Calculate gradients
        grad_x = np.diff(gray, axis=1)
        grad_y = np.diff(gray, axis=0)

        # Calculate gradient magnitude
        grad_mag = np.sqrt(grad_x[:-1, :]**2 + grad_y[:, :-1]**2)

        # Check histogram of gradients
        # Real photos: wide distribution
        # AI: concentrated around small values (smooth)

        hist, _ = np.histogram(grad_mag.flatten(), bins=50)

        # Calculate entropy of gradient histogram
        hist_norm = hist / (hist.sum() + 1e-10)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))

        # Typical entropy:
        # Real photos: > 4.5
        # AI smooth: < 3.5

        if entropy < 3.0:
            return 0.9  # Very smooth = AI
        elif entropy < 4.0:
            return 0.7  # Suspicious
        elif entropy > 4.8:
            return 0.1  # Natural texture
        else:
            return 0.4  # Borderline

    except:
        return 0.5  # Can't determine
