"""
Intrinsic AI Detection - Works WITHOUT metadata
Detects AI-generated images based on pixel-level characteristics

These methods work even if:
- EXIF metadata stripped
- Watermarks cropped
- Image re-compressed
- Screenshot taken

Detection is based on:
- GAN fingerprints (frequency domain artifacts)
- Color anomalies (impossible colors)
- Noise patterns (unnatural noise distribution)
- Visual artifacts (AI-specific patterns)
- JPEG quantization patterns (camera "fingerprints")
- ICC color profiles (manufacturer color calibration)
- PRNU sensor noise (device "fingerprints")
"""
import logging
import numpy as np
from typing import Dict, Any, Optional
from PIL import Image

logger = logging.getLogger(__name__)


class IntrinsicAIDetector:
    """
    Detect AI-generated images WITHOUT relying on metadata

    Uses pixel-level analysis:
    - Frequency domain patterns (GAN fingerprints)
    - Color distribution anomalies
    - Noise characteristics
    - Visual artifacts
    """

    def __init__(self):
        self.name = "Intrinsic AI Detector"
        self.opencv_available = self._check_opencv()
        self.jpeg_detector = None
        self.icc_detector = None
        self.prnu_detector = None
        self._init_jpeg_detector()
        self._init_icc_detector()
        self._init_prnu_detector()

    def _check_opencv(self) -> bool:
        """Check if OpenCV is available"""
        try:
            import cv2
            return True
        except ImportError:
            logger.warning("OpenCV not available - some intrinsic checks disabled")
            return False

    def _init_jpeg_detector(self):
        """Initialize JPEG quantization detector"""
        try:
            from backend.integrations.jpeg_quantization_detector import JPEGQuantizationDetector
            self.jpeg_detector = JPEGQuantizationDetector()
            logger.info("✅ JPEG quantization detector initialized")
        except ImportError as e:
            logger.warning(f"⚠️ JPEG quantization detector not available: {e}")
            self.jpeg_detector = None

    def _init_icc_detector(self):
        """Initialize ICC profile detector"""
        try:
            from backend.integrations.icc_profile_detector import ICCProfileDetector
            self.icc_detector = ICCProfileDetector()
            logger.info("✅ ICC profile detector initialized")
        except ImportError as e:
            logger.warning(f"⚠️ ICC profile detector not available: {e}")
            self.icc_detector = None

    def _init_prnu_detector(self):
        """Initialize PRNU sensor noise detector"""
        try:
            from backend.integrations.prnu_detector import PRNUDetector
            self.prnu_detector = PRNUDetector()
            logger.info("✅ PRNU detector initialized")
        except ImportError as e:
            logger.warning(f"⚠️ PRNU detector not available: {e}")
            self.prnu_detector = None

    async def detect(self, image_path: str, claimed_camera: Optional[str] = None, is_screenshot: bool = False) -> Dict[str, Any]:
        """
        Run intrinsic AI detection

        Args:
            image_path: Path to image file
            claimed_camera: Optional camera model from EXIF (e.g., "iPhone 15 Pro")
            is_screenshot: If True, skip PRNU and EXIF-dependent checks (screenshots don't have camera sensor data)

        Returns:
            Dict with:
            - is_ai_intrinsic: bool
            - confidence: float (0-1)
            - total_score: int
            - detection_methods: list
            - details: dict
        """

        results = {
            'is_ai_intrinsic': False,
            'confidence': 0.0,
            'total_score': 0,
            'detection_methods': [],
            'details': {},
            'survives_metadata_stripping': True,
            'is_screenshot': is_screenshot
        }

        try:
            # Load image
            img = Image.open(image_path)

            # OPTIMIZATION: Downsample large images for faster analysis
            # Intrinsic features are visible at lower resolution too
            max_size = 1536  # Max dimension (good balance: quality vs speed)
            original_size = img.size

            if max(img.size) > max_size:
                scale = max_size / max(img.size)
                new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 Downsampled for intrinsic analysis: {original_size} → {new_size}")

            img_array = np.array(img)

            # Check 1: Basic color anomalies (fast, always available)
            color_result = self._check_color_anomalies(img_array)
            results['details']['color_anomalies'] = color_result

            if color_result['has_anomalies']:
                results['total_score'] += color_result['score']
                results['detection_methods'].append('color_anomalies')

            # Check 2: Noise patterns (requires OpenCV)
            if self.opencv_available:
                noise_result = self._check_noise_patterns(img_array)
                results['details']['noise_patterns'] = noise_result

                if noise_result['has_anomalies']:
                    results['total_score'] += noise_result['score']
                    results['detection_methods'].append('noise_patterns')

                # Check 3: Visual artifacts
                artifact_result = self._check_visual_artifacts(img_array)
                results['details']['visual_artifacts'] = artifact_result

                if artifact_result['has_artifacts']:
                    results['total_score'] += artifact_result['score']
                    results['detection_methods'].append('visual_artifacts')

                # Check 4: GAN fingerprints (frequency domain analysis)
                gan_result = self._check_gan_fingerprints(img_array)
                results['details']['gan_fingerprints'] = gan_result

                if gan_result['has_fingerprints']:
                    results['total_score'] += gan_result['score']
                    results['detection_methods'].append('gan_fingerprints')

            # Check 5: JPEG quantization patterns (camera fingerprints)
            # SKIP for screenshots - they don't have camera quantization tables
            if self.jpeg_detector and not is_screenshot:
                jpeg_result = await self.jpeg_detector.detect(image_path, claimed_camera)
                results['details']['jpeg_quantization'] = jpeg_result

                if jpeg_result.get('has_anomalies'):
                    results['total_score'] += jpeg_result['fraud_score']
                    results['detection_methods'].append('jpeg_quantization')
            elif is_screenshot:
                logger.info("📸 Skipping JPEG quantization check for screenshot")
                results['details']['jpeg_quantization'] = {'skipped': True, 'reason': 'screenshot'}

            # Check 6: ICC color profile analysis (camera fingerprints)
            # SKIP for screenshots - they have monitor profiles, not camera profiles
            if self.icc_detector and not is_screenshot:
                icc_result = await self.icc_detector.detect(image_path, claimed_camera)
                results['details']['icc_profile'] = icc_result

                if icc_result.get('has_anomalies'):
                    results['total_score'] += icc_result['fraud_score']
                    results['detection_methods'].append('icc_profile')
            elif is_screenshot:
                logger.info("📸 Skipping ICC profile check for screenshot")
                results['details']['icc_profile'] = {'skipped': True, 'reason': 'screenshot'}

            # Check 7: PRNU sensor noise analysis (device fingerprints)
            # SKIP for screenshots - they don't have camera sensor noise
            if self.prnu_detector and not is_screenshot:
                prnu_result = await self.prnu_detector.detect(image_path, block_size=64, check_consistency=True)
                results['details']['prnu'] = prnu_result

                if prnu_result.get('has_anomalies'):
                    results['total_score'] += prnu_result['fraud_score']
                    results['detection_methods'].append('prnu')
            elif is_screenshot:
                logger.info("📸 Skipping PRNU sensor noise check for screenshot")
                results['details']['prnu'] = {'skipped': True, 'reason': 'screenshot'}

            # Final decision
            results['total_score'] = min(results['total_score'], 100)
            results['confidence'] = results['total_score'] / 100
            results['is_ai_intrinsic'] = results['total_score'] > 50

            if results['is_ai_intrinsic']:
                logger.info(f"🔬 Intrinsic AI detection: score={results['total_score']}, methods={results['detection_methods']}")

            return results

        except Exception as e:
            logger.error(f"Intrinsic detection error: {e}", exc_info=True)
            return {
                'is_ai_intrinsic': False,
                'confidence': 0.0,
                'total_score': 0,
                'detection_methods': [],
                'details': {'error': str(e)},
                'survives_metadata_stripping': True
            }

    def _check_color_anomalies(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Check for color anomalies that are uncommon in real photos

        AI often creates:
        - Oversaturated colors
        - Unnatural color distributions
        - Too uniform saturation
        """

        red_flags = []
        score = 0

        try:
            # Convert to RGB if needed
            if len(img_array.shape) == 2:  # Grayscale
                return {'has_anomalies': False, 'score': 0}

            if img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]

            # Calculate per-channel statistics
            r_channel = img_array[:, :, 0]
            g_channel = img_array[:, :, 1]
            b_channel = img_array[:, :, 2]

            # Check 1: Oversaturation
            # Real photos typically have moderate saturation
            # AI often oversaturates

            # Calculate simple saturation proxy (max - min per pixel)
            max_rgb = np.maximum(np.maximum(r_channel, g_channel), b_channel)
            min_rgb = np.minimum(np.minimum(r_channel, g_channel), b_channel)
            saturation_proxy = max_rgb - min_rgb

            sat_mean = np.mean(saturation_proxy)
            sat_std = np.std(saturation_proxy)

            if sat_mean > 120:  # High saturation (повышаем порог с 100 до 120)
                # EXCEPTION: Night Mode often boosts saturation for better visibility
                # Check if overall image is dark (night photo)
                brightness_mean = np.mean(img_array)

                if brightness_mean > 120:  # Not a night photo
                    red_flags.append(f"High saturation (mean: {sat_mean:.1f})")
                    score += 15  # Снижаем с 25 до 15
                else:
                    # Dark image with high saturation = likely Night Mode compensation
                    logger.info(f"✅ High saturation ({sat_mean:.1f}) but dark image (brightness={brightness_mean:.0f}) - likely Night Mode")
                    # Reduce penalty for night photos
                    score += 5  # Снижаем с 10 до 5

            if sat_std < 20:  # Too uniform (понижаем порог с 30 до 20)
                red_flags.append(f"Uniform saturation (std: {sat_std:.1f})")
                score += 15  # Снижаем с 20 до 15

            # Check 2: Pure values (0 or 255)
            # Real photos rarely have pure black or pure white
            total_pixels = img_array.shape[0] * img_array.shape[1]

            pure_white = np.sum((r_channel == 255) & (g_channel == 255) & (b_channel == 255))
            pure_black = np.sum((r_channel == 0) & (g_channel == 0) & (b_channel == 0))

            if pure_white > total_pixels * 0.08:  # >8% pure white (было 5%)
                red_flags.append(f"Excessive pure white ({pure_white/total_pixels:.1%})")
                score += 15  # Снижаем с 25 до 15

            if pure_black > total_pixels * 0.05:  # >5% pure black
                # EXCEPTION: Night photography can have lots of pure black (dark sky, shadows)
                # Check if overall image is dark (low brightness)
                brightness_mean = np.mean(img_array)

                if brightness_mean > 100:  # Not a night photo (bright overall)
                    red_flags.append(f"Excessive pure black ({pure_black/total_pixels:.1%})")
                    score += 25
                else:
                    # Dark overall = likely night photo, not AI
                    logger.info(f"✅ High pure black ({pure_black/total_pixels:.1%}) but dark image (brightness={brightness_mean:.0f}) - likely night photo")
                    # Don't penalize

            # Check 3: Color channel correlations
            # Real photos have natural R-G-B correlations
            # AI can have unusual correlations

            r_flat = r_channel.flatten().astype(float)
            g_flat = g_channel.flatten().astype(float)
            b_flat = b_channel.flatten().astype(float)

            # Sample for performance (10k pixels)
            sample_size = min(10000, len(r_flat))
            indices = np.random.choice(len(r_flat), sample_size, replace=False)

            r_sample = r_flat[indices]
            g_sample = g_flat[indices]
            b_sample = b_flat[indices]

            # Calculate correlations
            rg_corr = np.corrcoef(r_sample, g_sample)[0, 1]
            rb_corr = np.corrcoef(r_sample, b_sample)[0, 1]
            gb_corr = np.corrcoef(g_sample, b_sample)[0, 1]

            correlations = [rg_corr, rb_corr, gb_corr]

            # Real photos typically 0.5-0.9
            if min(correlations) < 0.15:  # Снижаем порог с 0.2 до 0.15
                red_flags.append(f"Weak color correlation (min: {min(correlations):.2f})")
                score += 15  # Снижаем с 20 до 15

            # Too perfect is also suspicious
            if all(c > 0.97 for c in correlations):  # Повышаем порог с 0.95 до 0.97
                red_flags.append("Unnaturally perfect color correlation")
                score += 15  # Снижаем с 20 до 15

            return {
                'has_anomalies': score > 20,
                'score': score,
                'red_flags': red_flags
            }

        except Exception as e:
            logger.debug(f"Color anomaly check error: {e}")
            return {'has_anomalies': False, 'score': 0, 'error': str(e)}

    def _check_noise_patterns(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Check for unnatural noise patterns

        Real cameras have specific noise (Poisson + Gaussian)
        AI has different noise characteristics
        """

        if not self.opencv_available:
            return {'has_anomalies': False, 'score': 0}

        red_flags = []
        score = 0

        try:
            import cv2

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # High-pass filter to isolate noise
            kernel_size = 5
            blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
            noise = gray.astype(float) - blurred.astype(float)

            # Analyze noise uniformity across image
            h, w = noise.shape
            block_size = 32

            noise_stds = []
            for i in range(0, h - block_size, block_size):
                for j in range(0, w - block_size, block_size):
                    block = noise[i:i+block_size, j:j+block_size]
                    noise_stds.append(np.std(block))

            if len(noise_stds) > 10:
                # Real cameras have varying noise across image
                # AI has TOO UNIFORM noise
                noise_variation = np.std(noise_stds) / (np.mean(noise_stds) + 1e-10)

                if noise_variation < 0.10:  # Too uniform (снижаем порог с 0.15 до 0.10)
                    red_flags.append(f"Unnaturally uniform noise (variation: {noise_variation:.3f})")
                    score += 20  # Снижаем с 30 до 20

            return {
                'has_anomalies': score > 20,
                'score': score,
                'red_flags': red_flags
            }

        except Exception as e:
            logger.debug(f"Noise pattern check error: {e}")
            return {'has_anomalies': False, 'score': 0, 'error': str(e)}

    def _check_visual_artifacts(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Check for AI-specific visual artifacts

        - Unnatural smoothness
        - Suspicious patterns
        - Gradient inconsistencies
        """

        if not self.opencv_available:
            return {'has_artifacts': False, 'score': 0}

        red_flags = []
        score = 0

        try:
            import cv2

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Check 1: Unnatural smoothness
            # Calculate local variance
            h, w = gray.shape
            window_size = 16

            variance_values = []
            for i in range(0, h - window_size, window_size):
                for j in range(0, w - window_size, window_size):
                    window = gray[i:i+window_size, j:j+window_size]
                    variance_values.append(np.var(window))

            if len(variance_values) > 0:
                # AI often has regions that are TOO smooth
                low_variance_ratio = np.sum(np.array(variance_values) < 50) / len(variance_values)

                if low_variance_ratio > 0.4:  # >40% very smooth (было 30%)
                    red_flags.append(f"Excessive smooth regions ({low_variance_ratio:.1%})")
                    score += 20  # Снижаем с 25 до 20

            # Check 2: Edge analysis
            # AI edges often have different characteristics
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            # Too many or too few edges can indicate AI
            if edge_density > 0.20:  # Повышаем порог с 0.15 до 0.20
                red_flags.append(f"Excessive edges ({edge_density:.2%})")
                score += 15  # Снижаем с 20 до 15
            elif edge_density < 0.01:  # Снижаем порог с 0.02 до 0.01
                red_flags.append(f"Insufficient edges ({edge_density:.2%})")
                score += 15  # Снижаем с 20 до 15

            return {
                'has_artifacts': score > 20,
                'score': score,
                'red_flags': red_flags
            }

        except Exception as e:
            logger.debug(f"Visual artifact check error: {e}")
            return {'has_artifacts': False, 'score': 0, 'error': str(e)}

    def _check_gan_fingerprints(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Check for GAN fingerprints in frequency domain

        GANs leave distinctive patterns in frequency spectrum:
        - Periodic artifacts in high frequencies
        - Unnatural frequency distribution
        - Checkerboard patterns (upsampling artifacts)

        Uses FFT (Fast Fourier Transform) to analyze frequency domain
        """

        if not self.opencv_available:
            return {'has_fingerprints': False, 'score': 0}

        red_flags = []
        score = 0

        try:
            import cv2

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Resize for performance (max 512x512)
            h, w = gray.shape
            if max(h, w) > 512:
                scale = 512 / max(h, w)
                new_h, new_w = int(h * scale), int(w * scale)
                gray = cv2.resize(gray, (new_w, new_h))

            # Apply FFT
            f_transform = np.fft.fft2(gray.astype(float))
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)

            # Log scale for better visualization/analysis
            magnitude_spectrum = np.log1p(magnitude_spectrum)

            # Analyze frequency distribution
            h, w = magnitude_spectrum.shape
            center_y, center_x = h // 2, w // 2

            # Check 1: High-frequency energy (GANs often have excessive high-freq content)
            # Create masks for different frequency bands
            y, x = np.ogrid[:h, :w]
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)

            # Low freq: center 10%
            # Mid freq: 10-40%
            # High freq: 40%+
            max_dist = np.sqrt(center_x**2 + center_y**2)

            low_freq_mask = distance < (max_dist * 0.1)
            mid_freq_mask = (distance >= max_dist * 0.1) & (distance < max_dist * 0.4)
            high_freq_mask = distance >= (max_dist * 0.4)

            low_energy = np.mean(magnitude_spectrum[low_freq_mask])
            mid_energy = np.mean(magnitude_spectrum[mid_freq_mask])
            high_energy = np.mean(magnitude_spectrum[high_freq_mask])

            total_energy = low_energy + mid_energy + high_energy

            if total_energy > 0:
                high_ratio = high_energy / total_energy

                # Real photos: high_ratio typically 0.15-0.30
                # AI images: often > 0.35 (too much high-frequency detail)
                if high_ratio > 0.40:  # Повышаем порог с 0.35 до 0.40
                    red_flags.append(f"Excessive high-frequency energy ({high_ratio:.2%})")
                    score += 25  # Снижаем с 30 до 25

                # Also check if too low (overly smooth)
                elif high_ratio < 0.08:  # Снижаем порог с 0.10 до 0.08
                    red_flags.append(f"Insufficient high-frequency detail ({high_ratio:.2%})")
                    score += 15  # Снижаем с 20 до 15

            # Check 2: Periodic patterns (GAN upsampling artifacts)
            # Look for regular patterns in frequency domain
            # Real images have irregular spectrum, AI has periodic peaks

            # Sample radial profile
            angles = np.linspace(0, 2*np.pi, 360)
            radius = int(max_dist * 0.7)

            radial_values = []
            for angle in angles[::10]:  # Sample every 10 degrees
                px = int(center_x + radius * np.cos(angle))
                py = int(center_y + radius * np.sin(angle))

                if 0 <= px < w and 0 <= py < h:
                    radial_values.append(magnitude_spectrum[py, px])

            if len(radial_values) > 10:
                # Check for periodicity using autocorrelation
                radial_values = np.array(radial_values)
                radial_values = radial_values - np.mean(radial_values)

                autocorr = np.correlate(radial_values, radial_values, mode='full')
                autocorr = autocorr[len(autocorr)//2:]

                # Normalize
                if autocorr[0] > 0:
                    autocorr = autocorr / autocorr[0]

                    # Look for periodic peaks (skip first value)
                    if len(autocorr) > 5:
                        max_autocorr = np.max(autocorr[2:min(10, len(autocorr))])

                        # Real images: max_autocorr < 0.3
                        # AI images: often > 0.4 (periodic patterns)
                        if max_autocorr > 0.5:  # Повышаем порог с 0.4 до 0.5
                            red_flags.append(f"Periodic frequency patterns detected ({max_autocorr:.2f})")
                            score += 25  # Снижаем с 35 до 25

            # Check 3: Azimuthal uniformity
            # Real photos have directional bias (edges along certain orientations)
            # AI images often too uniform across all directions

            azimuthal_profile = []
            for angle in angles[::5]:  # Every 5 degrees
                # Sample along this angle from center to edge
                samples = []
                for r in range(10, int(max_dist * 0.8), 10):
                    px = int(center_x + r * np.cos(angle))
                    py = int(center_y + r * np.sin(angle))

                    if 0 <= px < w and 0 <= py < h:
                        samples.append(magnitude_spectrum[py, px])

                if samples:
                    azimuthal_profile.append(np.mean(samples))

            if len(azimuthal_profile) > 20:
                azimuthal_std = np.std(azimuthal_profile)
                azimuthal_mean = np.mean(azimuthal_profile)

                if azimuthal_mean > 0:
                    azimuthal_variation = azimuthal_std / azimuthal_mean

                    # Real photos: variation typically > 0.15
                    # AI images: often < 0.10 (too uniform)
                    if azimuthal_variation < 0.06:  # Снижаем порог с 0.08 до 0.06
                        red_flags.append(f"Unnaturally uniform frequency distribution ({azimuthal_variation:.3f})")
                        score += 20  # Снижаем с 25 до 20

            return {
                'has_fingerprints': score > 25,
                'score': min(score, 40),  # Cap at 40 points
                'red_flags': red_flags,
                'details': {
                    'high_freq_ratio': high_ratio if 'high_ratio' in locals() else None,
                    'periodic_score': max_autocorr if 'max_autocorr' in locals() else None,
                    'azimuthal_variation': azimuthal_variation if 'azimuthal_variation' in locals() else None
                }
            }

        except Exception as e:
            logger.debug(f"GAN fingerprint check error: {e}")
            return {'has_fingerprints': False, 'score': 0, 'error': str(e)}
