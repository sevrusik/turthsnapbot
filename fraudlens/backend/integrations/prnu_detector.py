"""
PRNU (Photo Response Non-Uniformity) Detector

PRNU - уникальный паттерн шума сенсора, возникающий из-за производственных
дефектов в пикселях матрицы. Это "отпечаток пальца" конкретной камеры.

Detection methods:
1. PRNU presence check - есть ли sensor noise pattern (AI не имеет)
2. PRNU consistency check - однородность pattern (splice detection)
3. PRNU strength check - сила pattern (обработка ослабляет)
4. Block-wise analysis - детекция подделок через неоднородность

References:
- Lukas et al. "Digital Camera Identification From Sensor Pattern Noise" (2006)
- Goljan et al. "Large Scale Test of Sensor Fingerprint Camera Identification" (2009)
"""
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)


class PRNUDetector:
    """Detect fraud through sensor noise pattern (PRNU) analysis"""

    def __init__(self):
        self.name = "PRNU Detector"
        self.scipy_available = self._check_scipy()

        # Detection thresholds
        self.prnu_presence_threshold = 0.15  # Minimum PRNU strength
        self.consistency_threshold = 0.25    # Max variance in block-wise PRNU
        self.splice_threshold = 0.30         # Splice detection threshold

        logger.info("✅ PRNU Detector initialized")

    def _check_scipy(self) -> bool:
        """Check if scipy is available for advanced filtering"""
        try:
            import scipy
            import scipy.ndimage
            import scipy.signal
            return True
        except ImportError:
            logger.warning("⚠️ scipy not available - some PRNU features disabled")
            return False

    async def detect(
        self,
        image_path: str,
        block_size: int = 64,
        check_consistency: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze PRNU sensor noise pattern for fraud indicators

        Args:
            image_path: Path to image file
            block_size: Size of blocks for consistency analysis (default: 64x64)
            check_consistency: Whether to perform block-wise consistency check

        Returns:
            Detection result with fraud score and details
        """
        try:
            result = {
                'has_anomalies': False,
                'fraud_score': 0,
                'details': {
                    'has_prnu': False,
                    'prnu_strength': 0.0,
                    'consistency_score': 1.0,
                    'anomalies': []
                }
            }

            # Load image
            with Image.open(image_path) as img:
                # Convert to grayscale for PRNU analysis
                if img.mode != 'L':
                    img_gray = img.convert('L')
                else:
                    img_gray = img

                img_array = np.array(img_gray, dtype=np.float64)

                # Limit size for performance (max 1024x1024)
                max_size = 1024
                if img_array.shape[0] > max_size or img_array.shape[1] > max_size:
                    # Downsample
                    scale = min(max_size / img_array.shape[0], max_size / img_array.shape[1])
                    new_size = (int(img_array.shape[1] * scale), int(img_array.shape[0] * scale))
                    img_gray = img_gray.resize(new_size, Image.Resampling.BILINEAR)
                    img_array = np.array(img_gray, dtype=np.float64)

                logger.info(f"📊 PRNU analysis: image shape {img_array.shape}")

                # Extract PRNU pattern
                prnu_pattern = self._extract_prnu_pattern(img_array)

                if prnu_pattern is None:
                    result['details']['anomalies'].append('Could not extract PRNU pattern')
                    result['fraud_score'] += 5
                    return result

                # Check 1: PRNU presence (AI images lack sensor noise)
                prnu_strength = self._calculate_prnu_strength(prnu_pattern)
                result['details']['prnu_strength'] = float(prnu_strength)
                result['details']['has_prnu'] = prnu_strength > self.prnu_presence_threshold

                logger.info(f"   PRNU Strength: {prnu_strength:.4f}")

                if prnu_strength < self.prnu_presence_threshold:
                    result['details']['anomalies'].append(
                        f'Weak or missing PRNU pattern (strength={prnu_strength:.3f}) - possible AI generation or heavy editing'
                    )
                    result['fraud_score'] += 25
                    result['has_anomalies'] = True
                    logger.warning(f"⚠️ Weak PRNU: {prnu_strength:.4f}")

                # Check 2: PRNU consistency (splice/paste detection)
                if check_consistency and img_array.shape[0] >= block_size * 2 and img_array.shape[1] >= block_size * 2:
                    consistency_result = self._check_prnu_consistency(
                        img_array,
                        block_size=block_size
                    )

                    result['details']['consistency_score'] = float(consistency_result['score'])
                    result['details']['block_analysis'] = {
                        'num_blocks': consistency_result['num_blocks'],
                        'variance': float(consistency_result['variance']),
                        'max_deviation': float(consistency_result['max_deviation'])
                    }

                    logger.info(f"   PRNU Consistency: {consistency_result['score']:.4f}")
                    logger.info(f"   Block Variance: {consistency_result['variance']:.4f}")

                    if consistency_result['score'] < (1.0 - self.consistency_threshold):
                        result['details']['anomalies'].append(
                            f'PRNU inconsistency detected (score={consistency_result["score"]:.3f}) - possible splice/composite'
                        )
                        result['fraud_score'] += 35
                        result['has_anomalies'] = True
                        logger.warning(f"⚠️ PRNU inconsistency: {consistency_result['score']:.4f}")

                    # Check for extreme outlier blocks (splice detection)
                    if consistency_result['max_deviation'] > self.splice_threshold:
                        result['details']['anomalies'].append(
                            f'Extreme PRNU deviation in blocks (max={consistency_result["max_deviation"]:.3f}) - likely splice'
                        )
                        result['fraud_score'] += 45
                        result['has_anomalies'] = True
                        logger.warning(f"🚨 Splice detected: max_deviation={consistency_result['max_deviation']:.4f}")

                # Check 3: PRNU pattern naturalness (frequency analysis)
                if self.scipy_available:
                    naturalness = self._check_prnu_naturalness(prnu_pattern)
                    result['details']['prnu_naturalness'] = float(naturalness)

                    logger.info(f"   PRNU Naturalness: {naturalness:.4f}")

                    if naturalness < 0.3:
                        result['details']['anomalies'].append(
                            f'Unnatural PRNU pattern (naturalness={naturalness:.3f}) - possible synthetic image'
                        )
                        result['fraud_score'] += 20
                        result['has_anomalies'] = True

                logger.info(f"✅ PRNU analysis complete: score={result['fraud_score']}, anomalies={len(result['details']['anomalies'])}")

            return result

        except Exception as e:
            logger.error(f"PRNU detection failed: {e}", exc_info=True)
            return {
                'has_anomalies': False,
                'fraud_score': 0,
                'details': {
                    'error': str(e)
                }
            }

    def _extract_prnu_pattern(self, img: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract PRNU pattern from image using denoising

        PRNU = Image - Denoised(Image)

        Uses Wiener-like filtering to remove image content and leave sensor noise
        """
        try:
            # Simple denoising using local averaging (approximation of Wiener filter)
            if self.scipy_available:
                from scipy.ndimage import uniform_filter

                # Denoise with local averaging (5x5 window)
                window_size = 5
                denoised = uniform_filter(img, size=window_size, mode='reflect')

                # PRNU = original - denoised
                prnu = img - denoised

            else:
                # Fallback: simple local mean subtraction
                kernel_size = 5
                pad = kernel_size // 2

                # Pad image
                img_padded = np.pad(img, pad, mode='reflect')

                # Compute local mean
                denoised = np.zeros_like(img)
                for i in range(img.shape[0]):
                    for j in range(img.shape[1]):
                        window = img_padded[i:i+kernel_size, j:j+kernel_size]
                        denoised[i, j] = np.mean(window)

                prnu = img - denoised

            # Normalize PRNU
            prnu_mean = np.mean(prnu)
            prnu_std = np.std(prnu)

            if prnu_std > 0:
                prnu_normalized = (prnu - prnu_mean) / prnu_std
            else:
                prnu_normalized = prnu - prnu_mean

            return prnu_normalized

        except Exception as e:
            logger.error(f"PRNU extraction failed: {e}")
            return None

    def _calculate_prnu_strength(self, prnu: np.ndarray) -> float:
        """
        Calculate strength of PRNU pattern

        Higher values indicate stronger sensor noise pattern
        """
        try:
            # Calculate standard deviation of PRNU
            prnu_std = np.std(prnu)

            # Calculate energy in high-frequency components
            # Real sensor noise has characteristic frequency distribution
            if self.scipy_available:
                from scipy import fft

                # 2D FFT
                prnu_fft = fft.fft2(prnu)
                prnu_fft_shifted = fft.fftshift(prnu_fft)

                # Power spectrum
                power_spectrum = np.abs(prnu_fft_shifted) ** 2

                # Energy in high frequencies (outer region of spectrum)
                h, w = power_spectrum.shape
                center_h, center_w = h // 2, w // 2

                # Mask for high frequencies (exclude center 25%)
                mask = np.ones((h, w), dtype=bool)
                mask[
                    center_h - h//4:center_h + h//4,
                    center_w - w//4:center_w + w//4
                ] = False

                high_freq_energy = np.sum(power_spectrum[mask])
                total_energy = np.sum(power_spectrum)

                high_freq_ratio = high_freq_energy / (total_energy + 1e-10)

                # Combine std and frequency ratio
                strength = (prnu_std * 0.5 + high_freq_ratio * 0.5)

            else:
                # Fallback: use std only
                strength = prnu_std

            return float(np.clip(strength, 0, 1))

        except Exception as e:
            logger.error(f"PRNU strength calculation failed: {e}")
            return 0.0

    def _check_prnu_consistency(
        self,
        img: np.ndarray,
        block_size: int = 64
    ) -> Dict[str, Any]:
        """
        Check PRNU consistency across image blocks

        Spliced/composited images will have inconsistent PRNU patterns
        """
        try:
            h, w = img.shape

            # Divide image into blocks
            blocks_h = h // block_size
            blocks_w = w // block_size

            if blocks_h < 2 or blocks_w < 2:
                return {
                    'score': 1.0,
                    'variance': 0.0,
                    'max_deviation': 0.0,
                    'num_blocks': 0
                }

            # Extract PRNU for each block
            block_strengths = []

            for i in range(blocks_h):
                for j in range(blocks_w):
                    y_start = i * block_size
                    x_start = j * block_size
                    y_end = y_start + block_size
                    x_end = x_start + block_size

                    block = img[y_start:y_end, x_start:x_end]

                    # Extract PRNU for this block
                    block_prnu = self._extract_prnu_pattern(block)

                    if block_prnu is not None:
                        block_strength = self._calculate_prnu_strength(block_prnu)
                        block_strengths.append(block_strength)

            if len(block_strengths) < 4:
                return {
                    'score': 1.0,
                    'variance': 0.0,
                    'max_deviation': 0.0,
                    'num_blocks': len(block_strengths)
                }

            # Calculate statistics
            mean_strength = np.mean(block_strengths)
            variance = np.var(block_strengths)
            std_dev = np.std(block_strengths)

            # Max deviation from mean
            max_deviation = np.max(np.abs(np.array(block_strengths) - mean_strength))

            # Consistency score (1.0 = perfect consistency, 0.0 = inconsistent)
            # Normalize by mean to get relative variance
            if mean_strength > 0:
                relative_variance = variance / (mean_strength ** 2)
                consistency_score = 1.0 / (1.0 + relative_variance)
            else:
                consistency_score = 1.0

            return {
                'score': float(consistency_score),
                'variance': float(variance),
                'std_dev': float(std_dev),
                'max_deviation': float(max_deviation),
                'mean_strength': float(mean_strength),
                'num_blocks': len(block_strengths),
                'block_strengths': [float(s) for s in block_strengths]
            }

        except Exception as e:
            logger.error(f"PRNU consistency check failed: {e}")
            return {
                'score': 1.0,
                'variance': 0.0,
                'max_deviation': 0.0,
                'num_blocks': 0
            }

    def _check_prnu_naturalness(self, prnu: np.ndarray) -> float:
        """
        Check if PRNU pattern looks natural (from real sensor)

        Real sensor noise has specific frequency characteristics
        Synthetic images lack this structure
        """
        try:
            from scipy import fft

            # 2D FFT
            prnu_fft = fft.fft2(prnu)
            prnu_fft_shifted = fft.fftshift(prnu_fft)

            # Power spectrum
            power_spectrum = np.abs(prnu_fft_shifted) ** 2

            # Real sensor noise has radially symmetric power spectrum
            # Check for this property

            h, w = power_spectrum.shape
            center_h, center_w = h // 2, w // 2

            # Create radial profile
            y, x = np.ogrid[:h, :w]
            r = np.sqrt((x - center_w)**2 + (y - center_h)**2).astype(int)

            max_r = min(center_h, center_w)
            radial_profile = []

            for radius in range(0, max_r, 5):
                mask = (r >= radius) & (r < radius + 5)
                if np.any(mask):
                    radial_mean = np.mean(power_spectrum[mask])
                    radial_profile.append(radial_mean)

            if len(radial_profile) < 3:
                return 0.5

            # Real sensor noise decays smoothly with radius
            # Calculate smoothness of radial profile
            radial_profile = np.array(radial_profile)

            # Normalize
            if np.max(radial_profile) > 0:
                radial_profile = radial_profile / np.max(radial_profile)

            # Check for smooth decay (compute gradient variance)
            gradient = np.diff(radial_profile)
            gradient_variance = np.var(gradient)

            # Lower variance = smoother = more natural
            naturalness = 1.0 / (1.0 + gradient_variance * 10)

            return float(np.clip(naturalness, 0, 1))

        except Exception as e:
            logger.error(f"PRNU naturalness check failed: {e}")
            return 0.5
