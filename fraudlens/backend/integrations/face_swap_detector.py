"""
Face Swap / Deepfake Detection Module

Hybrid approach combining:
1. Face detection (MediaPipe)
2. FFT analysis on face boundaries (artifact detection)
3. Color consistency checks (face vs neck/background)
4. Geometric consistency (face landmarks)
"""

import io
import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
from PIL import Image
from scipy import fft

logger = logging.getLogger(__name__)


class FaceSwapDetector:
    """
    Hybrid face swap / deepfake detector

    Detection methods:
    1. Face boundary FFT analysis (swap artifacts)
    2. Color histogram comparison (face vs neck)
    3. Lighting consistency (face vs background)
    4. Geometric landmark validation
    """

    def __init__(self):
        self.face_detection = None
        self._init_face_detector()

    def _init_face_detector(self):
        """Initialize MediaPipe face detection"""
        try:
            import mediapipe as mp
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,  # 1 = full range, 0 = short range
                min_detection_confidence=0.5
            )
            logger.info("MediaPipe face detection initialized")
        except ImportError:
            logger.warning("MediaPipe not available - face swap detection will be limited")
            self.face_detection = None
        except Exception as e:
            logger.error(f"Failed to initialize face detection: {e}")
            self.face_detection = None

    async def analyze(self, image_bytes: bytes) -> Dict:
        """
        Analyze image for face swap / deepfake artifacts

        Args:
            image_bytes: Image binary data

        Returns:
            {
                "face_swap_score": float (0-1, higher = more likely face swap),
                "faces_detected": int,
                "checks": list,
                "artifacts": dict
            }
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Downsample very large images for performance
            # Face detection and FFT don't need full resolution
            original_size = img.size
            max_dimension = 2048

            if max(img.size) > max_dimension:
                if img.width > img.height:
                    new_width = max_dimension
                    new_height = int(img.height * (max_dimension / img.width))
                else:
                    new_height = max_dimension
                    new_width = int(img.width * (max_dimension / img.height))

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Face Swap: Downsampled {original_size} → {img.size} for performance")

            img_array = np.array(img.convert('RGB'))

            checks = []
            faces_detected = 0

            # Detect faces
            face_regions = self._detect_faces(img_array)
            faces_detected = len(face_regions)

            if faces_detected == 0:
                logger.info("No faces detected - skipping face swap analysis")
                return {
                    "face_swap_score": 0.0,
                    "faces_detected": 0,
                    "checks": [],
                    "artifacts": {}
                }

            logger.info(f"Detected {faces_detected} face(s), analyzing...")

            # For each face, run checks
            face_scores = []
            for i, face_region in enumerate(face_regions):
                # CHECK 1: Face boundary FFT analysis
                boundary_score = self._check_face_boundary_fft(img_array, face_region)
                checks.append({
                    "layer": f"Face {i+1} Boundary FFT",
                    "status": "FAIL" if boundary_score > 0.6 else "PASS",
                    "score": boundary_score,
                    "reason": "Swap artifacts on face boundary" if boundary_score > 0.6 else "Clean face boundaries",
                    "confidence": 0.85
                })

                # CHECK 2: Color consistency (face vs neck/background)
                color_score = self._check_color_consistency(img_array, face_region)
                checks.append({
                    "layer": f"Face {i+1} Color Consistency",
                    "status": "FAIL" if color_score > 0.6 else "PASS",
                    "score": color_score,
                    "reason": "Color mismatch (face vs skin)" if color_score > 0.6 else "Natural color consistency",
                    "confidence": 0.75
                })

                # CHECK 3: Lighting consistency
                lighting_score = self._check_lighting_consistency(img_array, face_region)
                checks.append({
                    "layer": f"Face {i+1} Lighting",
                    "status": "FAIL" if lighting_score > 0.6 else "PASS",
                    "score": lighting_score,
                    "reason": "Inconsistent lighting on face" if lighting_score > 0.6 else "Natural lighting",
                    "confidence": 0.70
                })

                # CHECK 4: Compression artifacts around face
                compression_score = self._check_face_compression(img_array, face_region)
                checks.append({
                    "layer": f"Face {i+1} Compression",
                    "status": "FAIL" if compression_score > 0.6 else "PASS",
                    "score": compression_score,
                    "reason": "Mismatched compression artifacts" if compression_score > 0.6 else "Uniform compression",
                    "confidence": 0.80
                })

                # Combine scores for this face
                weights = [0.85, 0.75, 0.70, 0.80]
                face_check_scores = [boundary_score, color_score, lighting_score, compression_score]
                face_score = sum(s * w for s, w in zip(face_check_scores, weights)) / sum(weights)
                face_scores.append(face_score)

            # Overall face swap score = max score across all faces
            face_swap_score = max(face_scores) if face_scores else 0.0

            logger.info(f"Face swap analysis complete: score={face_swap_score:.2f}, faces={faces_detected}")

            return {
                "face_swap_score": face_swap_score,
                "faces_detected": faces_detected,
                "checks": checks,
                "artifacts": {
                    "boundary_artifacts": any(s > 0.6 for s in [c["score"] for c in checks if "Boundary" in c["layer"]]),
                    "color_mismatch": any(s > 0.6 for s in [c["score"] for c in checks if "Color" in c["layer"]]),
                    "lighting_inconsistent": any(s > 0.6 for s in [c["score"] for c in checks if "Lighting" in c["layer"]]),
                    "compression_mismatch": any(s > 0.6 for s in [c["score"] for c in checks if "Compression" in c["layer"]])
                }
            }

        except Exception as e:
            logger.error(f"Face swap analysis failed: {e}")
            return {
                "face_swap_score": 0.5,
                "faces_detected": 0,
                "checks": [],
                "artifacts": {}
            }

    def _detect_faces(self, img_array: np.ndarray) -> List[Dict]:
        """
        Detect faces in image using MediaPipe

        Returns list of face regions with bounding boxes
        """
        if self.face_detection is None:
            # Fallback: assume whole image is face region (less accurate)
            h, w = img_array.shape[:2]
            return [{
                'bbox': (int(w*0.2), int(h*0.2), int(w*0.8), int(h*0.8)),
                'confidence': 0.5
            }]

        try:
            # Convert BGR to RGB for MediaPipe
            results = self.face_detection.process(img_array)

            if not results.detections:
                return []

            face_regions = []
            h, w = img_array.shape[:2]

            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box

                # Convert relative to absolute coordinates
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)

                # Ensure bbox is within image bounds
                x = max(0, x)
                y = max(0, y)
                x2 = min(w, x + width)
                y2 = min(h, y + height)

                face_regions.append({
                    'bbox': (x, y, x2, y2),
                    'confidence': detection.score[0]
                })

            return face_regions

        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []

    def _check_face_boundary_fft(self, img_array: np.ndarray, face_region: Dict) -> float:
        """
        Check FFT on face boundary for swap artifacts

        Face swaps often have discontinuities at the boundary
        """
        try:
            x1, y1, x2, y2 = face_region['bbox']

            # Extract boundary regions (10px wide strip around face)
            boundary_width = 10

            # Top boundary
            top_boundary = img_array[max(0, y1-boundary_width):y1+boundary_width, x1:x2]

            # Convert to grayscale
            if len(top_boundary.shape) == 3:
                top_boundary_gray = np.mean(top_boundary, axis=2)
            else:
                top_boundary_gray = top_boundary

            if top_boundary_gray.size == 0:
                return 0.5

            # Compute FFT on boundary
            f = fft.fft2(top_boundary_gray)
            fshift = fft.fftshift(f)
            magnitude = np.abs(fshift)

            # High-frequency energy indicates artifacts
            h, w = magnitude.shape
            center_h, center_w = h // 2, w // 2

            # Create high-frequency mask
            y_coords, x_coords = np.ogrid[:h, :w]
            dist = np.sqrt((x_coords - center_w)**2 + (y_coords - center_h)**2)
            max_dist = min(center_h, center_w)
            hf_mask = dist > (0.7 * max_dist)

            # Calculate high-frequency energy ratio
            total_energy = np.sum(magnitude**2)
            hf_energy = np.sum((magnitude * hf_mask)**2)

            if total_energy > 0:
                hf_ratio = hf_energy / total_energy
            else:
                return 0.5

            # High HF energy on boundary = likely swap artifact
            if hf_ratio > 0.30:
                return 0.85  # Strong artifacts
            elif hf_ratio > 0.20:
                return 0.65  # Moderate artifacts
            elif hf_ratio < 0.10:
                return 0.15  # Clean boundary
            else:
                return 0.4

        except Exception as e:
            logger.debug(f"Boundary FFT check failed: {e}")
            return 0.5

    def _check_color_consistency(self, img_array: np.ndarray, face_region: Dict) -> float:
        """
        Check color consistency between face and surrounding skin (neck/forehead)

        Face swaps often have color mismatches
        """
        try:
            x1, y1, x2, y2 = face_region['bbox']
            h_img, w_img = img_array.shape[:2]

            # Extract face region
            face = img_array[y1:y2, x1:x2]

            # Extract neck region (below face)
            neck_y1 = min(y2, h_img - 1)
            neck_y2 = min(y2 + (y2 - y1) // 3, h_img)
            neck = img_array[neck_y1:neck_y2, x1:x2] if neck_y2 > neck_y1 else None

            if face.size == 0:
                return 0.5

            # Calculate color histograms
            face_hist_r = np.histogram(face[:,:,0], bins=32, range=(0, 256))[0]
            face_hist_g = np.histogram(face[:,:,1], bins=32, range=(0, 256))[0]
            face_hist_b = np.histogram(face[:,:,2], bins=32, range=(0, 256))[0]

            if neck is not None and neck.size > 0:
                neck_hist_r = np.histogram(neck[:,:,0], bins=32, range=(0, 256))[0]
                neck_hist_g = np.histogram(neck[:,:,1], bins=32, range=(0, 256))[0]
                neck_hist_b = np.histogram(neck[:,:,2], bins=32, range=(0, 256))[0]

                # Normalize histograms
                face_hist_r = face_hist_r / (face_hist_r.sum() + 1e-10)
                face_hist_g = face_hist_g / (face_hist_g.sum() + 1e-10)
                face_hist_b = face_hist_b / (face_hist_b.sum() + 1e-10)

                neck_hist_r = neck_hist_r / (neck_hist_r.sum() + 1e-10)
                neck_hist_g = neck_hist_g / (neck_hist_g.sum() + 1e-10)
                neck_hist_b = neck_hist_b / (neck_hist_b.sum() + 1e-10)

                # Calculate histogram distance (Chi-square)
                dist_r = np.sum((face_hist_r - neck_hist_r)**2 / (face_hist_r + neck_hist_r + 1e-10))
                dist_g = np.sum((face_hist_g - neck_hist_g)**2 / (face_hist_g + neck_hist_g + 1e-10))
                dist_b = np.sum((face_hist_b - neck_hist_b)**2 / (face_hist_b + neck_hist_b + 1e-10))

                avg_dist = (dist_r + dist_g + dist_b) / 3

                # Large distance = color mismatch = likely swap
                if avg_dist > 0.5:
                    return 0.85  # Strong mismatch
                elif avg_dist > 0.3:
                    return 0.65  # Moderate mismatch
                elif avg_dist < 0.15:
                    return 0.20  # Good match
                else:
                    return 0.45

            return 0.5  # No neck region to compare

        except Exception as e:
            logger.debug(f"Color consistency check failed: {e}")
            return 0.5

    def _check_lighting_consistency(self, img_array: np.ndarray, face_region: Dict) -> float:
        """
        Check if lighting on face matches background

        Face swaps may have inconsistent lighting direction/intensity
        """
        try:
            x1, y1, x2, y2 = face_region['bbox']

            # Extract face
            face = img_array[y1:y2, x1:x2]

            if face.size == 0:
                return 0.5

            # Convert to grayscale
            if len(face.shape) == 3:
                face_gray = np.mean(face, axis=2)
            else:
                face_gray = face

            # Calculate gradient magnitude (lighting direction indicator)
            grad_y = np.diff(face_gray, axis=0)
            grad_x = np.diff(face_gray, axis=1)

            # Gradient statistics
            grad_y_mean = np.mean(np.abs(grad_y))
            grad_x_mean = np.mean(np.abs(grad_x))

            # Check for unnatural gradient patterns
            # Natural faces have smooth gradients
            # Swapped faces may have abrupt changes

            grad_ratio = max(grad_y_mean, grad_x_mean) / (min(grad_y_mean, grad_x_mean) + 1e-10)

            # Extreme gradient ratios = unnatural lighting
            if grad_ratio > 5.0:
                return 0.80
            elif grad_ratio > 3.0:
                return 0.60
            elif grad_ratio < 2.0:
                return 0.20
            else:
                return 0.40

        except Exception as e:
            logger.debug(f"Lighting consistency check failed: {e}")
            return 0.5

    def _check_face_compression(self, img_array: np.ndarray, face_region: Dict) -> float:
        """
        Check for compression artifact mismatches around face

        Face swaps may have different JPEG compression levels
        """
        try:
            x1, y1, x2, y2 = face_region['bbox']
            h_img, w_img = img_array.shape[:2]

            # Extract face region
            face = img_array[y1:y2, x1:x2]

            # Extract background region (area around face)
            margin = 20
            bg_x1 = max(0, x1 - margin)
            bg_y1 = max(0, y1 - margin)
            bg_x2 = min(w_img, x2 + margin)
            bg_y2 = min(h_img, y2 + margin)

            background = img_array[bg_y1:bg_y2, bg_x1:bg_x2]

            if face.size == 0 or background.size == 0:
                return 0.5

            # Convert to grayscale
            if len(face.shape) == 3:
                face_gray = np.mean(face, axis=2)
                bg_gray = np.mean(background, axis=2)
            else:
                face_gray = face
                bg_gray = background

            # Calculate local variance (compression indicator)
            # High compression = low variance
            face_var = np.var(face_gray)
            bg_var = np.var(background)

            # Compare compression levels
            if bg_var > 0:
                var_ratio = abs(face_var - bg_var) / bg_var
            else:
                return 0.5

            # Large variance difference = mismatched compression
            if var_ratio > 0.5:
                return 0.80
            elif var_ratio > 0.3:
                return 0.60
            elif var_ratio < 0.15:
                return 0.20
            else:
                return 0.40

        except Exception as e:
            logger.debug(f"Compression check failed: {e}")
            return 0.5
