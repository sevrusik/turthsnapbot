"""
Image Metadata Analyzer

Extracts and analyzes EXIF, XMP, and other metadata
"""

import asyncio
from typing import Dict, Optional, Tuple
import logging
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io

logger = logging.getLogger(__name__)


class MetadataAnalyzer:
    """
    Analyzes image metadata for manipulation signs
    """

    def _get_gps_coordinates(self, exif: Dict) -> Optional[Dict]:
        """
        Extract GPS coordinates from EXIF data

        Args:
            exif: Raw EXIF data from PIL (dict with tag_id as keys)

        Returns:
            {
                "latitude": float,
                "longitude": float,
                "altitude": float (optional)
            }
            or None if no GPS data found
        """
        try:
            # Get GPS IFD tag (34853)
            gps_ifd = exif.get(34853)
            if not gps_ifd:
                logger.debug("No GPS IFD found in EXIF (tag 34853)")
                return None

            # Parse GPS data - handle both dict and IFD object formats
            gps_data = {}
            if hasattr(gps_ifd, 'items'):
                # Dict format (modern getexif())
                for tag_id, value in gps_ifd.items():
                    tag = GPSTAGS.get(tag_id, tag_id)
                    gps_data[tag] = value
            else:
                # IFD object format
                for tag_id in gps_ifd.keys():
                    tag = GPSTAGS.get(tag_id, tag_id)
                    gps_data[tag] = gps_ifd[tag_id]

            logger.debug(f"GPS data found: {list(gps_data.keys())}")

            # Extract latitude
            lat = gps_data.get('GPSLatitude')
            lat_ref = gps_data.get('GPSLatitudeRef')

            # Extract longitude
            lon = gps_data.get('GPSLongitude')
            lon_ref = gps_data.get('GPSLongitudeRef')

            if not all([lat, lat_ref, lon, lon_ref]):
                logger.debug(f"Incomplete GPS data: lat={lat}, lat_ref={lat_ref}, lon={lon}, lon_ref={lon_ref}")
                return None

            # Convert from degrees/minutes/seconds to decimal
            def dms_to_decimal(dms, ref):
                """Convert degrees, minutes, seconds to decimal degrees"""
                try:
                    # Handle both tuple and list formats
                    if isinstance(dms, (tuple, list)) and len(dms) >= 3:
                        degrees = float(dms[0])
                        minutes = float(dms[1])
                        seconds = float(dms[2])
                    else:
                        logger.warning(f"Invalid DMS format: {dms}")
                        return None

                    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

                    # Apply direction (N/S for lat, E/W for lon)
                    if ref in ['S', 'W']:
                        decimal = -decimal

                    return decimal
                except (TypeError, ValueError, IndexError) as e:
                    logger.warning(f"Failed to convert DMS {dms}: {e}")
                    return None

            latitude = dms_to_decimal(lat, lat_ref)
            longitude = dms_to_decimal(lon, lon_ref)

            if latitude is None or longitude is None:
                logger.warning(f"Failed to convert GPS coordinates: lat={lat}, lon={lon}")
                return None

            result = {
                "latitude": latitude,
                "longitude": longitude
            }

            # Extract altitude if available
            altitude = gps_data.get('GPSAltitude')
            if altitude:
                try:
                    result["altitude"] = float(altitude)
                except (TypeError, ValueError):
                    logger.debug(f"Failed to parse altitude: {altitude}")

            logger.info(f"📍 GPS extracted successfully: {latitude:.6f}, {longitude:.6f}")
            return result

        except Exception as e:
            logger.warning(f"Failed to extract GPS coordinates: {e}", exc_info=True)
            return None

    async def analyze(self, image_bytes: bytes) -> Dict:
        """
        Extract and analyze image metadata

        Args:
            image_bytes: Image binary data

        Returns:
            {
                "exif": {...},
                "manipulation_detected": bool,
                "anomalies": [...]
            }
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))

            # Extract EXIF data using modern getexif() method
            exif_data = {}
            raw_exif_obj = image.getexif()

            # Convert to dict for compatibility
            raw_exif = {}
            if raw_exif_obj:
                for tag_id, value in raw_exif_obj.items():
                    tag = TAGS.get(tag_id, tag_id)
                    raw_exif[tag_id] = value  # Keep raw format for GPS extraction
                    # Skip GPS IFD (we'll parse it separately)
                    if tag_id == 34853:
                        continue
                    try:
                        exif_data[tag] = str(value)
                    except:
                        pass

            # Extract GPS coordinates
            gps_coordinates = None
            if raw_exif:
                gps_coordinates = self._get_gps_coordinates(raw_exif)

            # Check for manipulation signs
            anomalies = []

            # Missing EXIF (suspicious for real photos)
            if not exif_data:
                anomalies.append("No EXIF data found")

            # Check for AI software signatures
            software = exif_data.get("Software", "").lower()
            if any(ai_tool in software for ai_tool in ["midjourney", "dalle", "stable diffusion", "photoshop generative"]):
                anomalies.append(f"AI software detected: {software}")

            return {
                "exif": exif_data,
                "gps": gps_coordinates,
                "manipulation_detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "format": image.format,
                "size": image.size,
                "mode": image.mode
            }

        except Exception as e:
            logger.error(f"Metadata analysis failed: {e}")
            return {
                "exif": {},
                "gps": None,
                "manipulation_detected": False,
                "anomalies": [],
                "error": str(e)
            }
