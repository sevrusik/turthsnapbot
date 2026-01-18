"""
FFT-based AI Image Detection

Analyzes frequency domain characteristics to detect AI-generated images:
1. JPEG compression artifacts (DCT block patterns)
2. High-frequency content analysis
3. Spectral anomalies (GAN fingerprints)
4. Power spectrum distribution
"""

import io
import logging
from typing import Dict, Tuple
import numpy as np
from PIL import Image
from scipy import fft, signal

logger = logging.getLogger(__name__)


class FFTDetector:
    """
    Frequency-domain analysis for AI detection

    Real photos show:
    - JPEG 8x8 DCT block artifacts
    - Natural high-frequency noise
    - Smooth power spectrum falloff

    AI-generated images show:
    - Missing/weak JPEG artifacts
    - Unnatural high-frequency patterns
    - Spectral anomalies from GAN processing
    """

    def __init__(self):
        self.enabled = True

    async def analyze(self, image_bytes: bytes) -> Dict:
        """
        Run FFT analysis on image

        Args:
            image_bytes: Image binary data

        Returns:
            {
                "fft_score": float (0-1, higher = more likely AI),
                "checks": list,
                "spectral_anomalies": dict
            }
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Downsample large images for FFT performance
            # FFT doesn't need full resolution - frequency domain characteristics
            # are preserved even at lower resolutions
            original_size = img.size
            max_dimension = 2048

            if max(img.size) > max_dimension:
                # Calculate new size maintaining aspect ratio
                if img.width > img.height:
                    new_width = max_dimension
                    new_height = int(img.height * (max_dimension / img.width))
                else:
                    new_height = max_dimension
                    new_width = int(img.width * (max_dimension / img.height))

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"FFT: Downsampled {original_size} → {img.size} for performance")

            img_array = np.array(img.convert('RGB'))

            # OPTIMIZATION: Convert to grayscale once
            gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array

            # OPTIMIZATION: Compute FFT once and reuse
            f = fft.fft2(gray)
            fshift = fft.fftshift(f)
            magnitude_spectrum = np.abs(fshift)
            power_spectrum = magnitude_spectrum ** 2

            # Precompute geometric arrays once
            h, w = magnitude_spectrum.shape
            center_h, center_w = h // 2, w // 2
            y, x = np.ogrid[:h, :w]
            dist = np.sqrt((x - center_w)**2 + (y - center_h)**2)

            checks = []

            # CHECK 1: JPEG compression artifacts (8x8 DCT blocks)
            jpeg_score = self._check_jpeg_artifacts_optimized(magnitude_spectrum, center_h, center_w)
            checks.append({
                "layer": "JPEG Artifacts",
                "status": "FAIL" if jpeg_score > 0.6 else "PASS",
                "score": jpeg_score,
                "reason": "Missing JPEG compression patterns" if jpeg_score > 0.6 else "Normal JPEG artifacts detected",
                "confidence": 0.85
            })

            # CHECK 2: High-frequency content analysis
            hf_score = self._check_high_frequency_optimized(magnitude_spectrum, dist, center_h, center_w)
            checks.append({
                "layer": "High-Frequency Analysis",
                "status": "FAIL" if hf_score > 0.6 else "PASS",
                "score": hf_score,
                "reason": "Unnatural high-frequency patterns" if hf_score > 0.6 else "Natural frequency distribution",
                "confidence": 0.80
            })

            # CHECK 3: Power spectrum distribution
            spectrum_score = self._check_power_spectrum_optimized(power_spectrum, dist, center_h, center_w)
            checks.append({
                "layer": "Power Spectrum",
                "status": "FAIL" if spectrum_score > 0.6 else "PASS",
                "score": spectrum_score,
                "reason": "Anomalous spectral distribution" if spectrum_score > 0.6 else "Natural power spectrum",
                "confidence": 0.75
            })

            # CHECK 4: Periodic patterns (GAN fingerprints)
            periodic_score = self._check_periodic_patterns_optimized(magnitude_spectrum, center_h, center_w)
            checks.append({
                "layer": "Periodic Patterns",
                "status": "FAIL" if periodic_score > 0.6 else "PASS",
                "score": periodic_score,
                "reason": "GAN-like periodic artifacts" if periodic_score > 0.6 else "No artificial periodicities",
                "confidence": 0.70
            })

            # Calculate weighted average
            weights = [0.85, 0.80, 0.75, 0.70]
            fft_score = sum(c["score"] * w for c, w in zip(checks, weights)) / sum(weights)

            logger.info(f"FFT analysis complete: score={fft_score:.2f}")

            return {
                "fft_score": fft_score,
                "checks": checks,
                "spectral_anomalies": {
                    "jpeg_artifacts_missing": jpeg_score > 0.6,
                    "high_freq_anomaly": hf_score > 0.6,
                    "power_spectrum_anomaly": spectrum_score > 0.6,
                    "periodic_patterns": periodic_score > 0.6
                }
            }

        except Exception as e:
            logger.error(f"FFT analysis failed: {e}")
            return {
                "fft_score": 0.5,
                "checks": [],
                "spectral_anomalies": {}
            }

    def _check_jpeg_artifacts_optimized(self, magnitude_spectrum: np.ndarray, center_h: int, center_w: int) -> float:
        """
        Optimized JPEG artifact check - reuses precomputed FFT
        """
        try:
            # Sample along horizontal and vertical axes
            horizontal = magnitude_spectrum[center_h, :]
            vertical = magnitude_spectrum[:, center_w]

            # Check for periodicity at 8-pixel intervals
            def check_8px_periodicity(signal_1d):
                # Autocorrelation to find periodic patterns
                autocorr = np.correlate(signal_1d, signal_1d, mode='full')
                autocorr = autocorr[len(autocorr)//2:]

                # Normalize
                if autocorr[0] > 0:
                    autocorr = autocorr / autocorr[0]

                # Check for peaks at 8-pixel intervals
                if len(autocorr) > 32:
                    peaks_8 = autocorr[8] if len(autocorr) > 8 else 0
                    peaks_16 = autocorr[16] if len(autocorr) > 16 else 0
                    avg_8px_peaks = (peaks_8 + peaks_16) / 2
                    return avg_8px_peaks
                return 0

            h_periodicity = check_8px_periodicity(horizontal)
            v_periodicity = check_8px_periodicity(vertical)
            avg_periodicity = (h_periodicity + v_periodicity) / 2

            # High periodicity = JPEG artifacts present = likely real photo
            # Low periodicity = no JPEG artifacts = likely AI
            if avg_periodicity > 0.3:
                return 0.1  # Strong JPEG artifacts = real
            elif avg_periodicity > 0.15:
                return 0.4  # Some artifacts
            else:
                return 0.8  # No JPEG artifacts = suspicious

        except Exception as e:
            logger.debug(f"JPEG artifact check failed: {e}")
            return 0.5

    def _check_jpeg_artifacts(self, img_array: np.ndarray) -> float:
        """
        Check for JPEG 8x8 DCT block artifacts

        Real JPEG photos have characteristic 8x8 block boundaries.
        AI-generated images often lack these or have them artificially added.
        """
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array

            # Compute 2D FFT
            f = fft.fft2(gray)
            fshift = fft.fftshift(f)
            magnitude_spectrum = np.abs(fshift)

            # Look for peaks at multiples of 8 pixels (JPEG block size)
            # This creates a grid pattern in frequency space
            h, w = magnitude_spectrum.shape
            center_h, center_w = h // 2, w // 2

            # Sample along horizontal and vertical axes
            horizontal = magnitude_spectrum[center_h, :]
            vertical = magnitude_spectrum[:, center_w]

            # Check for periodicity at 8-pixel intervals
            # Real JPEG should show peaks at f = n/8 where n is integer
            def check_8px_periodicity(signal_1d):
                # Autocorrelation to find periodic patterns
                autocorr = np.correlate(signal_1d, signal_1d, mode='full')
                autocorr = autocorr[len(autocorr)//2:]

                # Normalize
                if autocorr[0] > 0:
                    autocorr = autocorr / autocorr[0]

                # Check for peaks at 8-pixel intervals
                # Look at lag=8, 16, 24, 32
                if len(autocorr) > 32:
                    peaks_8 = autocorr[8] if len(autocorr) > 8 else 0
                    peaks_16 = autocorr[16] if len(autocorr) > 16 else 0
                    avg_8px_peaks = (peaks_8 + peaks_16) / 2
                    return avg_8px_peaks
                return 0

            h_periodicity = check_8px_periodicity(horizontal)
            v_periodicity = check_8px_periodicity(vertical)
            avg_periodicity = (h_periodicity + v_periodicity) / 2

            # High periodicity = JPEG artifacts present = likely real photo
            # Low periodicity = no JPEG artifacts = likely AI
            if avg_periodicity > 0.3:
                return 0.1  # Strong JPEG artifacts = real
            elif avg_periodicity > 0.15:
                return 0.4  # Some artifacts
            else:
                return 0.8  # No JPEG artifacts = suspicious

        except Exception as e:
            logger.debug(f"JPEG artifact check failed: {e}")
            return 0.5

    def _check_high_frequency_optimized(self, magnitude_spectrum: np.ndarray, dist: np.ndarray, center_h: int, center_w: int) -> float:
        """
        Optimized high-frequency check - reuses precomputed arrays
        """
        try:
            # Define high-frequency region (outer 30% of radius)
            max_dist = min(center_h, center_w)
            hf_mask = dist > (0.7 * max_dist)

            # Calculate energy in high-frequency region
            total_energy = np.sum(magnitude_spectrum**2)
            hf_energy = np.sum((magnitude_spectrum[hf_mask])**2)

            if total_energy > 0:
                hf_ratio = hf_energy / total_energy
            else:
                return 0.5

            # Real photos: HF ratio typically 0.05-0.20
            # AI over-smoothed: HF ratio < 0.03
            # AI artifacts: HF ratio > 0.25

            if hf_ratio < 0.03:
                return 0.85  # Too smooth = AI
            elif hf_ratio > 0.25:
                return 0.75  # Too much HF = AI artifacts
            elif 0.05 <= hf_ratio <= 0.20:
                return 0.15  # Natural range
            else:
                return 0.5  # Borderline

        except Exception as e:
            logger.debug(f"High-frequency check failed: {e}")
            return 0.5

    def _check_high_frequency(self, img_array: np.ndarray) -> float:
        """
        Analyze high-frequency content

        AI-generated images often have:
        - Too little high-frequency content (over-smoothed)
        - OR too much unnatural high-frequency content (GAN artifacts)
        """
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array

            # Compute 2D FFT
            f = fft.fft2(gray)
            fshift = fft.fftshift(f)
            magnitude_spectrum = np.abs(fshift)

            # Create high-frequency mask (outer ring)
            h, w = magnitude_spectrum.shape
            center_h, center_w = h // 2, w // 2

            # Create distance matrix from center
            y, x = np.ogrid[:h, :w]
            dist = np.sqrt((x - center_w)**2 + (y - center_h)**2)

            # Define high-frequency region (outer 30% of radius)
            max_dist = min(center_h, center_w)
            hf_mask = dist > (0.7 * max_dist)

            # Calculate energy in high-frequency region
            total_energy = np.sum(magnitude_spectrum**2)
            hf_energy = np.sum((magnitude_spectrum * hf_mask)**2)

            if total_energy > 0:
                hf_ratio = hf_energy / total_energy
            else:
                return 0.5

            # Real photos: HF ratio typically 0.05-0.20
            # AI over-smoothed: HF ratio < 0.03
            # AI artifacts: HF ratio > 0.25

            if hf_ratio < 0.03:
                return 0.85  # Too smooth = AI
            elif hf_ratio > 0.25:
                return 0.75  # Too much HF = AI artifacts
            elif 0.05 <= hf_ratio <= 0.20:
                return 0.15  # Natural range
            else:
                return 0.5  # Borderline

        except Exception as e:
            logger.debug(f"High-frequency check failed: {e}")
            return 0.5

    def _check_power_spectrum_optimized(self, power_spectrum: np.ndarray, dist: np.ndarray, center_h: int, center_w: int) -> float:
        """
        Optimized power spectrum check - vectorized radial profile computation
        """
        try:
            # Convert distance to integer bins
            max_radius = min(center_h, center_w)
            dist_int = dist.astype(int)

            # Vectorized radial profile using bincount
            radial_sum = np.bincount(dist_int.ravel(), weights=power_spectrum.ravel())
            radial_count = np.bincount(dist_int.ravel())

            # Avoid division by zero
            radial_count[radial_count == 0] = 1
            radial_profile = radial_sum / radial_count

            # Use only valid radius range
            radial_profile = radial_profile[1:max_radius]

            if len(radial_profile) < 10:
                return 0.5

            frequencies = np.arange(1, len(radial_profile) + 1)

            # Fit to power law: P(f) = A * f^(-alpha)
            log_freq = np.log(frequencies)
            log_power = np.log(radial_profile + 1e-10)

            # Linear regression
            coeffs = np.polyfit(log_freq, log_power, 1)
            slope = coeffs[0]  # This is -alpha

            # Expected: slope ~ -2 for natural images
            if -2.5 < slope < -1.5:
                return 0.1  # Natural power law
            elif -3.0 < slope < -1.0:
                return 0.4  # Close to natural
            else:
                return 0.8  # Unnatural power spectrum

        except Exception as e:
            logger.debug(f"Power spectrum check failed: {e}")
            return 0.5

    def _check_power_spectrum(self, img_array: np.ndarray) -> float:
        """
        Analyze power spectrum distribution

        Natural images follow 1/f^2 power law.
        AI-generated images often deviate from this.
        """
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array

            # Compute 2D FFT
            f = fft.fft2(gray)
            fshift = fft.fftshift(f)
            power_spectrum = np.abs(fshift)**2

            # Convert to radial profile
            h, w = power_spectrum.shape
            center_h, center_w = h // 2, w // 2

            y, x = np.ogrid[:h, :w]
            dist = np.sqrt((x - center_w)**2 + (y - center_h)**2).astype(int)

            # Compute average power at each radius
            max_radius = min(center_h, center_w)
            radial_profile = []

            for r in range(1, max_radius):
                mask = (dist == r)
                if np.any(mask):
                    radial_profile.append(np.mean(power_spectrum[mask]))

            if len(radial_profile) < 10:
                return 0.5

            radial_profile = np.array(radial_profile)
            frequencies = np.arange(1, len(radial_profile) + 1)

            # Fit to power law: P(f) = A * f^(-alpha)
            # Natural images: alpha ~ 2
            # Take log for linear fit
            log_freq = np.log(frequencies)
            log_power = np.log(radial_profile + 1e-10)

            # Linear regression
            coeffs = np.polyfit(log_freq, log_power, 1)
            slope = coeffs[0]  # This is -alpha

            # Expected: slope ~ -2 for natural images
            # AI images often have different slopes

            if -2.5 < slope < -1.5:
                return 0.1  # Natural power law
            elif -3.0 < slope < -1.0:
                return 0.4  # Close to natural
            else:
                return 0.8  # Unnatural power spectrum

        except Exception as e:
            logger.debug(f"Power spectrum check failed: {e}")
            return 0.5

    def _check_periodic_patterns_optimized(self, magnitude_spectrum: np.ndarray, center_h: int, center_w: int) -> float:
        """
        Optimized periodic pattern check - simplified without expensive maximum_filter
        """
        try:
            # Use variance in frequency domain as proxy for periodic patterns
            # High variance indicates many strong peaks (GAN artifacts)
            # Low variance indicates few peaks or over-smoothing

            h, w = magnitude_spectrum.shape

            # Mask out center (DC component)
            mask = np.ones((h, w), dtype=bool)
            mask[center_h-10:center_h+10, center_w-10:center_w+10] = False

            # Get masked spectrum values
            masked_spectrum = magnitude_spectrum[mask]

            # Use log for better dynamic range
            log_masked = np.log(masked_spectrum + 1)

            # Calculate coefficient of variation (normalized std)
            mean_val = np.mean(log_masked)
            std_val = np.std(log_masked)

            if mean_val > 0:
                cv = std_val / mean_val
            else:
                return 0.5

            # Natural images: CV typically 0.4-0.8
            # GAN artifacts: very high CV (>1.0) - many strong peaks
            # Over-smoothed: very low CV (<0.3) - too uniform

            if cv > 1.0:
                return 0.85  # Too many strong peaks = GAN
            elif cv < 0.3:
                return 0.75  # Too uniform = suspicious
            elif 0.4 <= cv <= 0.8:
                return 0.15  # Natural range
            else:
                return 0.5  # Borderline

        except Exception as e:
            logger.debug(f"Periodic pattern check failed: {e}")
            return 0.5

    def _check_periodic_patterns(self, img_array: np.ndarray) -> float:
        """
        Check for periodic patterns (GAN fingerprints)

        Some GANs leave periodic artifacts in the frequency domain.
        """
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array

            # Compute 2D FFT
            f = fft.fft2(gray)
            fshift = fft.fftshift(f)
            magnitude_spectrum = np.abs(fshift)

            # Log scale for better visualization of peaks
            log_spectrum = np.log(magnitude_spectrum + 1)

            # Find local maxima (peaks)
            # Exclude center region (DC component)
            h, w = log_spectrum.shape
            center_h, center_w = h // 2, w // 2

            # Mask out center
            mask = np.ones((h, w), dtype=bool)
            mask[center_h-10:center_h+10, center_w-10:center_w+10] = False

            # Find peaks using local maxima
            # A peak is a point higher than its 8 neighbors
            from scipy.ndimage import maximum_filter

            local_max = maximum_filter(log_spectrum, size=5)
            peaks = (log_spectrum == local_max) & mask

            # Count significant peaks
            threshold = np.percentile(log_spectrum[mask], 95)
            significant_peaks = peaks & (log_spectrum > threshold)
            num_peaks = np.sum(significant_peaks)

            # Natural images: few strong peaks (5-20)
            # GAN artifacts: many periodic peaks (>50) or very few (<3)

            if num_peaks > 50:
                return 0.85  # Too many peaks = GAN artifacts
            elif num_peaks < 3:
                return 0.75  # Too few = suspicious
            elif 5 <= num_peaks <= 20:
                return 0.15  # Natural range
            else:
                return 0.5  # Borderline

        except Exception as e:
            logger.debug(f"Periodic pattern check failed: {e}")
            return 0.5
