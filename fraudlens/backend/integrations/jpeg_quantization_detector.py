"""
JPEG Quantization Pattern Analysis
Detects image manipulation by analyzing JPEG compression "fingerprints"

🎯 Principle:
Each camera processor (ISP) uses unique JPEG quantization tables.
These tables are like a "signature" - impossible to fake without deep knowledge.

Detection:
- Extract quantization tables from JPEG
- Compare with known camera fingerprints
- Detect mismatches (AI, editing, different camera)
- Identify double compression (re-saved images)

References:
- "JPEG Compression History Estimation for Color Images" (IEEE, 2006)
- "Exposing Digital Forgeries by Detecting Traces of Recompression" (2005)
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import io
import struct
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class JPEGQuantizationDetector:
    """
    Analyze JPEG quantization tables to detect manipulation

    JPEG Compression Basics:
    - Image divided into 8x8 blocks
    - DCT (Discrete Cosine Transform) applied
    - Coefficients divided by quantization table
    - Each camera has unique quantization patterns

    Detection Methods:
    1. Camera Fingerprint Matching
    2. Double Compression Detection
    3. Quality Level Analysis
    4. AI Generation Patterns
    """

    def __init__(self):
        self.name = "JPEG Quantization Detector"

        # Path to quantization database
        self.database_path = Path(__file__).parent.parent / 'data' / 'camera_quantization_database.json'

        # Load database
        self.database = self._load_database()

        # Load known camera quantization patterns
        self.camera_patterns = self._load_camera_patterns()

        # Common AI/editing software patterns
        self.ai_patterns = self._load_ai_patterns()


    async def detect(self, image_path: str, claimed_camera: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze JPEG quantization patterns

        Args:
            image_path: Path to JPEG image
            claimed_camera: Camera model from EXIF (e.g., "iPhone 15 Pro")

        Returns:
            Dict with:
            - has_anomalies: bool
            - fraud_score: int (0-100)
            - details: dict with findings
            - camera_match: bool (if claimed_camera provided)
        """

        results = {
            'has_anomalies': False,
            'fraud_score': 0,
            'confidence': 0.0,
            'red_flags': [],
            'details': {},
            'camera_match': None
        }

        try:
            # Check if JPEG
            with Image.open(image_path) as img:
                if img.format != 'JPEG':
                    logger.info(f"Not JPEG format: {img.format} - skipping quantization analysis")
                    return results

            # Extract quantization tables
            qtables = self._extract_quantization_tables(image_path)

            if not qtables:
                results['red_flags'].append("Cannot extract quantization tables")
                results['fraud_score'] += 20
                return results

            results['details']['qtables_count'] = len(qtables)

            # Check 1: Camera fingerprint matching
            if claimed_camera:
                match_result = self._match_camera_fingerprint(qtables, claimed_camera)
                results['details']['camera_match'] = match_result

                if not match_result['matches']:
                    results['red_flags'].append(
                        f"Quantization tables don't match {claimed_camera}"
                    )
                    results['fraud_score'] += 40
                    results['has_anomalies'] = True

            # Check 2: AI generation patterns
            ai_result = self._check_ai_patterns(qtables)
            results['details']['ai_pattern_check'] = ai_result

            if ai_result['likely_ai']:
                results['red_flags'].append(
                    f"AI generation pattern detected: {ai_result['pattern_name']}"
                )
                results['fraud_score'] += 50
                results['has_anomalies'] = True

            # Check 3: Double compression (re-saved image)
            double_comp = self._detect_double_compression(qtables)
            results['details']['double_compression'] = double_comp

            if double_comp['detected']:
                results['red_flags'].append(
                    f"Double JPEG compression detected (re-saved {double_comp['times']}x)"
                )
                results['fraud_score'] += 30
                results['has_anomalies'] = True

            # Check 4: Quality level analysis
            quality = self._estimate_quality(qtables)
            results['details']['estimated_quality'] = quality

            # Unusual quality levels can indicate manipulation
            if quality < 60:
                results['red_flags'].append(f"Low JPEG quality ({quality}%) - suspicious")
                results['fraud_score'] += 15
            elif quality > 98:
                results['red_flags'].append(f"Unusually high quality ({quality}%) - suspicious")
                results['fraud_score'] += 10

            # Final scoring
            results['fraud_score'] = min(results['fraud_score'], 100)
            results['confidence'] = results['fraud_score'] / 100
            results['has_anomalies'] = results['fraud_score'] > 30

            if results['has_anomalies']:
                logger.info(
                    f"🔍 JPEG quantization anomalies detected: "
                    f"score={results['fraud_score']}, flags={len(results['red_flags'])}"
                )

            return results

        except Exception as e:
            logger.error(f"JPEG quantization analysis error: {e}", exc_info=True)
            return {
                'has_anomalies': False,
                'fraud_score': 0,
                'confidence': 0.0,
                'red_flags': [],
                'details': {'error': str(e)}
            }


    def _extract_quantization_tables(self, image_path: str) -> Optional[List[np.ndarray]]:
        """
        Extract JPEG quantization tables from image file

        JPEG File Structure:
        - Starts with FFD8 (SOI - Start of Image)
        - Contains DQT segments (Define Quantization Table) - FFDB
        - Each DQT has 8x8 table (64 values)

        Returns:
            List of quantization tables (typically 2: one for luminance, one for chrominance)
        """
        try:
            with open(image_path, 'rb') as f:
                data = f.read()

            # Check JPEG signature
            if data[:2] != b'\xff\xd8':
                logger.warning("Not a JPEG file (invalid signature)")
                return None

            qtables = []
            pos = 2  # Skip SOI marker

            # Parse JPEG segments
            while pos < len(data) - 1:
                # Find marker
                if data[pos] != 0xFF:
                    pos += 1
                    continue

                marker = data[pos:pos+2]
                pos += 2

                # Check if this is DQT (Define Quantization Table) marker
                if marker == b'\xff\xdb':
                    # Read segment length
                    if pos + 2 > len(data):
                        break

                    length = struct.unpack('>H', data[pos:pos+2])[0]
                    pos += 2

                    # Read DQT data
                    segment_data = data[pos:pos+length-2]
                    pos += length - 2

                    # Parse quantization table(s) in this segment
                    seg_pos = 0
                    while seg_pos < len(segment_data):
                        # First byte: precision (high 4 bits) and table ID (low 4 bits)
                        if seg_pos >= len(segment_data):
                            break

                        qt_info = segment_data[seg_pos]
                        precision = (qt_info >> 4) & 0x0F  # 0 = 8-bit, 1 = 16-bit
                        table_id = qt_info & 0x0F
                        seg_pos += 1

                        # Read 64 values (8x8 table)
                        table_size = 64 * (2 if precision else 1)

                        if seg_pos + table_size > len(segment_data):
                            break

                        if precision == 0:  # 8-bit values
                            qtable = np.frombuffer(
                                segment_data[seg_pos:seg_pos+64],
                                dtype=np.uint8
                            )
                        else:  # 16-bit values
                            qtable = np.frombuffer(
                                segment_data[seg_pos:seg_pos+128],
                                dtype='>u2'  # Big-endian uint16
                            )

                        # Reshape to 8x8
                        qtable = qtable.reshape(8, 8)
                        qtables.append(qtable)

                        seg_pos += table_size

                        logger.debug(f"Extracted quantization table {table_id}: shape={qtable.shape}")

                # Stop at Start of Scan (SOS)
                elif marker == b'\xff\xda':
                    break

                # Skip other segments
                elif marker[1] >= 0xC0:
                    if pos + 2 > len(data):
                        break
                    length = struct.unpack('>H', data[pos:pos+2])[0]
                    pos += length

            if qtables:
                logger.info(f"✅ Extracted {len(qtables)} quantization table(s)")
                return qtables
            else:
                logger.warning("⚠️ No quantization tables found in JPEG")
                return None

        except Exception as e:
            logger.error(f"Error extracting quantization tables: {e}")
            return None


    def _match_camera_fingerprint(
        self,
        qtables: List[np.ndarray],
        camera_model: str
    ) -> Dict[str, Any]:
        """
        Compare quantization tables with known camera fingerprints

        Uses multi-level matching:
        1. Exact match (case-insensitive)
        2. Partial match (substring)
        3. Fuzzy match (brand + model number)

        Args:
            qtables: Extracted quantization tables
            camera_model: Camera model from EXIF

        Returns:
            Dict with match results
        """
        if len(qtables) < 1:
            return {'matches': False, 'reason': 'No quantization tables found'}

        # Normalize camera model
        camera_key = camera_model.lower().strip()

        # Try exact match first
        if camera_key in self.camera_patterns:
            expected_pattern = self.camera_patterns[camera_key]
            similarity = self._calculate_table_similarity(qtables[0], expected_pattern['luminance'])
            matches = similarity > 0.85

            return {
                'matches': matches,
                'similarity': similarity,
                'expected_pattern': camera_key,
                'match_type': 'exact',
                'reason': f'Similarity: {similarity:.2%}' if not matches else 'Pattern matches (exact)'
            }

        # Try partial match (e.g., "iPhone 15 Pro Max" -> "iPhone 15")
        best_match = None
        best_similarity = 0.0

        for known_camera, pattern_data in self.camera_patterns.items():
            # Check if known camera name is substring of claimed camera
            # e.g., "iphone 15" in "iphone 15 pro max"
            if known_camera in camera_key:
                similarity = self._calculate_table_similarity(qtables[0], pattern_data['luminance'])

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (known_camera, pattern_data, 'partial')

            # Check reverse: claimed camera in known camera
            # e.g., "galaxy s23" in "samsung galaxy s23"
            elif camera_key in known_camera:
                similarity = self._calculate_table_similarity(qtables[0], pattern_data['luminance'])

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (known_camera, pattern_data, 'partial')

        # Try fuzzy brand matching (e.g., extract "iphone" + "15" from "iPhone 15 Pro Max")
        if not best_match:
            # Extract brand keywords
            brands = {
                'iphone': 'apple',
                'samsung': 'samsung',
                'galaxy': 'samsung',
                'pixel': 'google',
                'canon': 'canon',
                'nikon': 'nikon',
                'sony': 'sony'
            }

            detected_brand = None
            for keyword, brand in brands.items():
                if keyword in camera_key:
                    detected_brand = brand
                    break

            if detected_brand:
                # Try to match within same brand
                for known_camera, pattern_data in self.camera_patterns.items():
                    if pattern_data.get('brand') == detected_brand:
                        similarity = self._calculate_table_similarity(qtables[0], pattern_data['luminance'])

                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = (known_camera, pattern_data, 'fuzzy_brand')

        # Return best match if found
        if best_match:
            camera_name, pattern_data, match_type = best_match
            matches = best_similarity > 0.85

            return {
                'matches': matches,
                'similarity': best_similarity,
                'expected_pattern': camera_name,
                'match_type': match_type,
                'reason': (f'Similarity: {best_similarity:.2%}' if not matches
                          else f'Pattern matches ({match_type})')
            }

        # No match found
        return {
            'matches': None,
            'reason': f'No fingerprint in database for {camera_model}'
        }


    def _check_ai_patterns(self, qtables: List[np.ndarray]) -> Dict[str, Any]:
        """
        Check if quantization tables match AI generation patterns

        AI generators often use:
        - Standard JPEG library defaults (IJG, libjpeg)
        - Unusual quality levels
        - Simplified quantization patterns
        """
        if not qtables:
            return {'likely_ai': False}

        luminance_table = qtables[0]

        # Check against known AI patterns
        for pattern_name, pattern_data in self.ai_patterns.items():
            similarity = self._calculate_table_similarity(
                luminance_table,
                pattern_data['table']
            )

            if similarity > 0.95:  # Very high match
                return {
                    'likely_ai': True,
                    'pattern_name': pattern_name,
                    'similarity': similarity
                }

        return {'likely_ai': False}


    def _detect_double_compression(self, qtables: List[np.ndarray]) -> Dict[str, Any]:
        """
        Detect if image has been re-saved (double JPEG compression)

        Method:
        - Check for periodic artifacts in DCT coefficients
        - Look for quantization table inconsistencies
        - Analyze histogram of DCT coefficients

        Note: This is a simplified check. Full analysis requires DCT coefficient access.
        """
        # Simplified check based on quantization table patterns
        # Real double compression detection requires DCT coefficient analysis

        if not qtables or len(qtables) < 1:
            return {'detected': False}

        luminance = qtables[0]

        # Check for unusual patterns that suggest double compression
        # 1. Very uniform values (multiple compressions smooth out variations)
        std_dev = np.std(luminance)

        if std_dev < 5:  # Too uniform
            return {
                'detected': True,
                'times': '2+',
                'method': 'uniform_table',
                'confidence': 0.7
            }

        # 2. Check if table matches multiple quality levels
        # (This happens when image is saved at different qualities)
        # TODO: Implement full double compression detection

        return {'detected': False}


    def _estimate_quality(self, qtables: List[np.ndarray]) -> int:
        """
        Estimate JPEG quality level from quantization table

        Uses IJG (Independent JPEG Group) formula:
        - Quality 50: standard quantization table
        - Quality > 50: table values reduced
        - Quality < 50: table values increased

        Returns:
            Quality estimate (0-100)
        """
        if not qtables or len(qtables) < 1:
            return 75  # Default assumption

        luminance = qtables[0]

        # Standard IJG luminance quantization table (quality 50)
        ijg_baseline = np.array([
            [16, 11, 10, 16,  24,  40,  51,  61],
            [12, 12, 14, 19,  26,  58,  60,  55],
            [14, 13, 16, 24,  40,  57,  69,  56],
            [14, 17, 22, 29,  51,  87,  80,  62],
            [18, 22, 37, 56,  68, 109, 103,  77],
            [24, 35, 55, 64,  81, 104, 113,  92],
            [49, 64, 78, 87, 103, 121, 120, 101],
            [72, 92, 95, 98, 112, 100, 103,  99]
        ])

        # Calculate scaling factor
        # quality > 50: scale < 1 (smaller table values)
        # quality < 50: scale > 1 (larger table values)

        # Use center values for estimation (more stable)
        actual_center = luminance[2:6, 2:6].mean()
        baseline_center = ijg_baseline[2:6, 2:6].mean()

        scale = actual_center / baseline_center

        # Convert scale to quality
        if scale <= 0:
            quality = 100
        elif scale < 1:
            quality = int(50 + (1 - scale) * 50)
        else:
            quality = int(50 / scale)

        # Clamp to valid range
        quality = max(1, min(100, quality))

        return quality


    def _calculate_table_similarity(
        self,
        table1: np.ndarray,
        table2: np.ndarray
    ) -> float:
        """
        Calculate similarity between two quantization tables

        Uses cosine similarity on flattened arrays

        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Flatten tables
            v1 = table1.flatten().astype(float)
            v2 = table2.flatten().astype(float)

            # Cosine similarity
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            return max(0.0, min(1.0, similarity))

        except Exception as e:
            logger.error(f"Error calculating table similarity: {e}")
            return 0.0


    def _load_database(self) -> Dict[str, Any]:
        """
        Load quantization database from JSON file

        Returns:
            Database dict with cameras and AI generators
        """
        try:
            if not self.database_path.exists():
                logger.warning(f"Database not found at {self.database_path}, using fallback patterns")
                return {'cameras': {}, 'ai_generators': {}}

            with open(self.database_path, 'r') as f:
                database = json.load(f)

            total_cameras = sum(len(brand) for brand in database.get('cameras', {}).values())
            total_ai = len(database.get('ai_generators', {}))

            logger.info(f"✅ Loaded quantization database: {total_cameras} cameras, {total_ai} AI generators")

            return database

        except Exception as e:
            logger.error(f"Error loading quantization database: {e}")
            return {'cameras': {}, 'ai_generators': {}}


    def _load_camera_patterns(self) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Load camera patterns from database and create lookup dict

        Returns:
            Dict mapping camera model names to their quantization patterns
        """
        patterns = {}

        cameras = self.database.get('cameras', {})

        # Iterate through all brands (apple, samsung, google, etc.)
        for brand, models in cameras.items():
            # Iterate through each model (iphone_11, galaxy_s23, etc.)
            for model_key, model_data in models.items():
                # Get all possible names for this camera
                model_names = model_data.get('model_names', [])

                # Convert luminance/chrominance arrays to numpy
                luminance = np.array(model_data['luminance'])
                chrominance = np.array(model_data.get('chrominance', []))

                # Add pattern for each possible name (normalized to lowercase)
                for name in model_names:
                    normalized_name = name.lower().strip()
                    patterns[normalized_name] = {
                        'luminance': luminance,
                        'chrominance': chrominance,
                        'brand': brand,
                        'model_key': model_key,
                        'notes': model_data.get('notes', '')
                    }

        logger.debug(f"Loaded {len(patterns)} camera fingerprint patterns")

        return patterns


    def _load_ai_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Load AI generation patterns from database

        Returns:
            Dict mapping AI generator names to their quantization patterns
        """
        patterns = {}

        ai_generators = self.database.get('ai_generators', {})

        for generator_key, generator_data in ai_generators.items():
            # Convert luminance array to numpy
            luminance = np.array(generator_data['luminance'])
            chrominance = np.array(generator_data.get('chrominance', []))

            patterns[generator_key] = {
                'table': luminance,  # Luminance table (main detection)
                'chrominance': chrominance,
                'description': generator_data.get('notes', ''),
                'model_names': generator_data.get('model_names', [])
            }

        logger.debug(f"Loaded {len(patterns)} AI generator patterns")

        return patterns


    def format_results_for_report(self, results: Dict[str, Any]) -> str:
        """
        Format quantization analysis results for PDF report

        Returns:
            Formatted text for inclusion in report
        """
        if not results.get('has_anomalies'):
            return "✅ JPEG quantization tables appear normal"

        text = "🔍 JPEG Quantization Analysis:\n\n"

        for flag in results.get('red_flags', []):
            text += f"  ⚠️  {flag}\n"

        details = results.get('details', {})

        if 'estimated_quality' in details:
            text += f"\n  Quality Level: {details['estimated_quality']}%\n"

        if 'camera_match' in details and details['camera_match']:
            match_info = details['camera_match']
            if match_info.get('matches') is False:
                text += f"\n  Camera Mismatch: {match_info.get('reason', 'Unknown')}\n"

        if 'double_compression' in details:
            dc = details['double_compression']
            if dc.get('detected'):
                text += f"\n  Re-saved: {dc.get('times', 'multiple')} times\n"

        return text


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        detector = JPEGQuantizationDetector()

        # Test with a sample image
        result = await detector.detect(
            "/path/to/test.jpg",
            claimed_camera="iPhone 15 Pro"
        )

        print(f"Has anomalies: {result['has_anomalies']}")
        print(f"Fraud score: {result['fraud_score']}")
        print(f"Red flags: {result['red_flags']}")
        print(f"\nDetails: {result['details']}")

    asyncio.run(test())
