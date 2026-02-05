"""
Social Media Platform EXIF/Metadata Profiles
Криптографические отпечатки метаданных для детекции платформы
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Профили платформ - что ожидаем увидеть в метаданных
PLATFORM_PROFILES = {
    "linkedin": {
        "name": "LinkedIn",
        "description": "LinkedIn applies compression and sometimes adds Adobe processing markers",

        # Положительные индикаторы (REQUIRED для match)
        "required_markers": {
            "software_keywords": ["linkedin", "adobe"],  # Software field содержит эти слова
            "exif_stripped": False,  # Часто оставляет частичный EXIF
        },

        # Отрицательные индикаторы (если есть, НЕ LinkedIn)
        "exclusion_markers": {
            "software_keywords": ["whatsapp", "instagram", "facebook", "telegram"],
            "has_thumbnails": False,  # LinkedIn обычно удаляет thumbnails
        },

        # Характеристики метаданных
        "metadata_characteristics": {
            "exif_present": True,  # Обычно есть частичный EXIF
            "gps_stripped": True,  # GPS всегда удаляется
            "camera_info_preserved": False,  # Make/Model обычно удаляются
            "timestamp_preserved": False,  # DateTime часто сбрасывается
            "color_profile_preserved": True,  # sRGB обычно сохраняется
        },

        # XMP/IPTC маркеры
        "xmp_markers": [],  # LinkedIn не добавляет специфических XMP

        # Структурные характеристики
        "structural_markers": {
            "has_embedded_thumbnail": False,  # Обычно нет встроенных миниатюр
            "progressive_jpeg": False,  # Обычно baseline JPEG
        },

        # 🔬 SMOKING GUN: JFIF маркеры для детекции AI на LinkedIn
        # Реальное фото: JFIF присутствует, есть Encoding Process
        # AI фото: нет JFIF, часто PNG, нет Encoding Process
        "jfif_markers": {
            "real_photo": {
                "jfif_version": "1.01",  # Должна быть версия JFIF
                "has_resolution": True,  # X/Y Resolution должны присутствовать
                "encoding_process": True,  # Encoding Process присутствует
                "bits_per_sample": 8,  # Обычно 8 бит
                "color_components": 3,  # RGB = 3 компонента
                "file_type": "JPEG",  # Должен быть JPEG
                "ycbcr_subsampling": "YCbCr4:2:0 (2 2)",  # Стандартный для камер
            },
            "ai_photo": {
                "jfif_version": None,  # JFIF отсутствует!
                "has_resolution": False,  # Нет X/Y Resolution
                "encoding_process": False,  # Нет Encoding Process
                "bits_per_sample": None,  # Отсутствует
                "color_components": None,  # Отсутствует
                "file_type": "PNG",  # Часто PNG вместо JPEG
                "ycbcr_subsampling": None,  # Может отсутствовать
            }
        },

        "confidence_threshold": 0.6,  # Минимальная уверенность для match
    },

    "instagram": {
        "name": "Instagram",
        "description": "Instagram/Meta aggressively strips EXIF and adds proprietary markers",

        "required_markers": {
            "software_keywords": [],  # Instagram часто не оставляет Software field
            "exif_stripped": True,  # Почти полное удаление EXIF
        },

        "exclusion_markers": {
            "software_keywords": ["linkedin", "whatsapp", "telegram"],
            "has_camera_info": True,  # Если есть камера - не Instagram
        },

        "metadata_characteristics": {
            "exif_present": False,  # Обычно полностью удален
            "gps_stripped": True,
            "camera_info_preserved": False,
            "timestamp_preserved": False,
            "color_profile_preserved": True,
        },

        # Instagram добавляет IPTC/XMP метки
        "xmp_markers": ["xmp:creatortool=instagram", "meta", "facebook"],

        "structural_markers": {
            "has_embedded_thumbnail": True,  # Instagram пересобирает thumbnails
            "progressive_jpeg": False,
        },

        "confidence_threshold": 0.7,
    },

    "facebook": {
        "name": "Facebook",
        "description": "Facebook uses custom quantization tables and aggressive compression",

        "required_markers": {
            "software_keywords": [],  # Facebook не добавляет Software field
            "exif_stripped": True,  # Полное удаление EXIF
        },

        "exclusion_markers": {
            "software_keywords": ["linkedin", "whatsapp", "instagram", "telegram"],
            "has_camera_info": True,  # Если есть камера - не Facebook
            "has_gps": True,  # Если есть GPS - не Facebook
        },

        "metadata_characteristics": {
            "exif_present": False,  # Полностью удален
            "gps_stripped": True,  # GPS всегда удаляется
            "camera_info_preserved": False,  # Make/Model удаляются
            "timestamp_preserved": False,  # DateTime сбрасывается
            "color_profile_preserved": True,  # sRGB иногда сохраняется
        },

        "xmp_markers": ["facebook", "meta"],

        "structural_markers": {
            "has_embedded_thumbnail": True,  # Facebook пересоздает thumbnails
            "progressive_jpeg": False,  # Baseline JPEG, не progressive
        },

        # Compression characteristics
        "compression": {
            "max_dimension": 2048,  # Profile photos: max 2048×2048
            "jpeg_quality": 85,  # Приблизительное качество JPEG
            "converts_png_to_jpeg": True,  # PNG → JPEG conversion
            "ycbcr_subsampling": "YCbCr4:2:0 (2 2)",  # Стандартный chroma subsampling
            "custom_quantization": True,  # Facebook использует свои таблицы квантования
        },

        # 🔬 SMOKING GUN: JFIF маркеры для детекции AI на Facebook
        # Facebook конвертирует PNG → JPEG, но сохраняет JFIF структуру
        "jfif_markers": {
            "real_photo": {
                "jfif_version": "1.01",  # JFIF версия присутствует
                "has_resolution": True,  # X/Y Resolution (обычно 72 dpi)
                "encoding_process": True,  # Encoding Process: Baseline DCT
                "bits_per_sample": 8,  # 8 бит на канал
                "color_components": 3,  # RGB = 3 компонента
                "file_type": "JPEG",  # Всегда JPEG после обработки
                "ycbcr_subsampling": "YCbCr4:2:0 (2 2)",
            },
            "ai_photo": {
                # AI фото после Facebook conversion:
                # Если оригинал был PNG без JFIF → после конвертации могут отсутствовать маркеры
                "jfif_version": "1.01",  # Может присутствовать (Facebook добавляет)
                "has_resolution": True,  # Facebook добавляет resolution
                "encoding_process": True,  # Facebook добавляет encoding process
                "bits_per_sample": 8,
                "color_components": 3,
                "file_type": "JPEG",
                "ycbcr_subsampling": "YCbCr4:2:0 (2 2)",
                # NOTE: На Facebook JFIF markers менее надежны для детекции AI,
                # так как Facebook нормализует все изображения
                # Используйте intrinsic detection (PRNU, quantization tables)
            }
        },

        # Facebook quantization fingerprint
        # Facebook использует пользовательские таблицы квантования для снижения размера
        "jpeg_quantization": {
            "custom_tables": True,  # Не стандартные JPEG tables
            "luminance_table_sum": None,  # Переменная (зависит от содержимого)
            "chrominance_table_sum": None,
            "quality_estimate_range": [80, 90],  # Оценка качества JPEG
        },

        "confidence_threshold": 0.65,
    },

    "whatsapp": {
        "name": "WhatsApp",
        "description": "WhatsApp strips ALL metadata and resets timestamp to send date",

        "required_markers": {
            "software_keywords": [],  # WhatsApp не добавляет Software
            "exif_stripped": True,  # Полное удаление
        },

        "exclusion_markers": {
            "software_keywords": ["linkedin", "instagram", "facebook", "telegram"],
            "has_camera_info": True,
            "has_gps": True,
        },

        "metadata_characteristics": {
            "exif_present": False,  # Идеально чистый файл
            "gps_stripped": True,
            "camera_info_preserved": False,
            "timestamp_preserved": False,  # Timestamp = дата пересылки
            "color_profile_preserved": False,  # Часто удаляется
        },

        "xmp_markers": [],  # Полностью чистый

        "structural_markers": {
            "has_embedded_thumbnail": False,  # Thumbnails удаляются
            "progressive_jpeg": True,  # WhatsApp использует progressive JPEG
            "sterile_structure": True,  # Идеально чистая структура
        },

        "confidence_threshold": 0.8,  # Высокая уверенность для WhatsApp
    },

    "telegram": {
        "name": "Telegram",
        "description": "Telegram preserves more metadata than most platforms",

        "required_markers": {
            "software_keywords": [],
            "exif_stripped": False,  # Часто сохраняет частичный EXIF
        },

        "exclusion_markers": {
            "software_keywords": ["whatsapp", "instagram", "linkedin"],
        },

        "metadata_characteristics": {
            "exif_present": True,  # Может сохранять EXIF
            "gps_stripped": True,  # GPS обычно удаляется
            "camera_info_preserved": True,  # Может сохранять Make/Model
            "timestamp_preserved": True,  # Часто сохраняет DateTime
            "color_profile_preserved": True,
        },

        "xmp_markers": [],

        "structural_markers": {
            "has_embedded_thumbnail": False,
            "progressive_jpeg": False,
        },

        "confidence_threshold": 0.55,
    },

    "twitter": {
        "name": "Twitter/X",
        "description": "Twitter strips most EXIF but preserves some metadata",

        "required_markers": {
            "software_keywords": [],
            "exif_stripped": False,
        },

        "exclusion_markers": {
            "software_keywords": ["whatsapp", "instagram", "linkedin", "telegram"],
        },

        "metadata_characteristics": {
            "exif_present": True,  # Частичный EXIF
            "gps_stripped": True,
            "camera_info_preserved": False,
            "timestamp_preserved": False,
            "color_profile_preserved": True,
        },

        "xmp_markers": [],

        "structural_markers": {
            "has_embedded_thumbnail": True,
            "progressive_jpeg": False,
        },

        "confidence_threshold": 0.6,
    },
}


class SocialMediaProfileMatcher:
    """
    Сопоставление метаданных изображения с профилями социальных платформ
    Использует криптографический подход к анализу структуры EXIF/XMP
    """

    def __init__(self):
        self.profiles = PLATFORM_PROFILES

    def match_platform(
        self,
        raw_exif: Optional[Dict[str, Any]],
        image_path: str,
        has_thumbnails: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Сопоставить метаданные изображения с профилями платформ

        Args:
            raw_exif: Словарь EXIF метаданных (из PIL)
            image_path: Путь к изображению для дополнительного анализа
            has_thumbnails: Есть ли встроенные thumbnails

        Returns:
            Dict с результатами сопоставления:
            {
                'platform': 'linkedin',
                'confidence': 0.85,
                'matched_markers': [...],
                'profile': {...}
            }
            или None если нет совпадений
        """
        if not raw_exif:
            raw_exif = {}

        # Извлекаем ключевые поля для анализа
        software = str(raw_exif.get('Software', '')).lower()
        make = str(raw_exif.get('Make', '')).lower()
        model = str(raw_exif.get('Model', '')).lower()
        datetime_original = raw_exif.get('DateTimeOriginal', raw_exif.get('DateTime'))
        gps_info = raw_exif.get('GPSInfo')

        has_exif = bool(raw_exif)
        has_camera_info = bool(make or model)
        has_gps = bool(gps_info)
        has_timestamp = bool(datetime_original)

        logger.info(f"🔍 Platform matching - Software: '{software}', EXIF: {has_exif}, Camera: {has_camera_info}, GPS: {has_gps}")

        # Проверяем каждую платформу
        best_match = None
        best_confidence = 0.0

        for platform_name, profile in self.profiles.items():
            confidence, matched_markers = self._calculate_match_confidence(
                profile,
                software=software,
                has_exif=has_exif,
                has_camera_info=has_camera_info,
                has_gps=has_gps,
                has_timestamp=has_timestamp,
                has_thumbnails=has_thumbnails,
                raw_exif=raw_exif
            )

            logger.debug(f"  - {platform_name}: confidence={confidence:.2f}, markers={len(matched_markers)}")

            # Проверяем threshold
            if confidence >= profile['confidence_threshold'] and confidence > best_confidence:
                best_confidence = confidence
                best_match = {
                    'platform': platform_name,
                    'confidence': confidence,
                    'matched_markers': matched_markers,
                    'profile': profile
                }

        if best_match:
            logger.info(
                f"✅ Platform match: {best_match['platform']} "
                f"(confidence={best_match['confidence']:.2f}, "
                f"markers={len(best_match['matched_markers'])})"
            )
        else:
            logger.info("❌ No platform match found")

        return best_match

    def _calculate_match_confidence(
        self,
        profile: Dict,
        software: str,
        has_exif: bool,
        has_camera_info: bool,
        has_gps: bool,
        has_timestamp: bool,
        has_thumbnails: bool,
        raw_exif: Dict
    ) -> tuple[float, List[str]]:
        """
        Рассчитать уверенность совпадения с профилем платформы

        Returns:
            (confidence, matched_markers)
        """
        confidence = 0.0
        matched_markers = []

        # 1. EXCLUSION MARKERS - если есть, сразу 0.0
        exclusions = profile.get('exclusion_markers', {})

        # Проверка exclusion keywords в Software
        for keyword in exclusions.get('software_keywords', []):
            if keyword in software:
                logger.debug(f"    ❌ Exclusion: software contains '{keyword}'")
                return 0.0, []

        # Проверка exclusion camera info
        if exclusions.get('has_camera_info') and has_camera_info:
            logger.debug(f"    ❌ Exclusion: has camera info")
            return 0.0, []

        # Проверка exclusion GPS
        if exclusions.get('has_gps') and has_gps:
            logger.debug(f"    ❌ Exclusion: has GPS")
            return 0.0, []

        # 2. REQUIRED MARKERS - проверяем соответствие
        required = profile.get('required_markers', {})

        # Software keywords (вес 30%)
        software_keywords = required.get('software_keywords', [])
        if software_keywords:
            # Должен содержать хотя бы один keyword
            if any(kw in software for kw in software_keywords):
                confidence += 0.3
                matched_markers.append(f"Software keyword match: {software}")
        else:
            # Нет требуемых keywords - проверяем что Software пустой (для WhatsApp/Instagram)
            if not software or software == '':
                confidence += 0.2
                matched_markers.append("Software field empty (expected)")

        # EXIF stripped check (вес 25%)
        exif_stripped_required = required.get('exif_stripped', False)
        if exif_stripped_required == (not has_exif):
            confidence += 0.25
            matched_markers.append(f"EXIF presence matches: stripped={exif_stripped_required}")

        # 3. METADATA CHARACTERISTICS (вес 45%)
        characteristics = profile.get('metadata_characteristics', {})
        char_score = 0.0
        char_count = 0

        # EXIF present
        if characteristics.get('exif_present') == has_exif:
            char_score += 1
            char_count += 1

        # GPS stripped
        gps_stripped = characteristics.get('gps_stripped', True)
        if gps_stripped == (not has_gps):
            char_score += 1
            char_count += 1

        # Camera info preserved
        camera_preserved = characteristics.get('camera_info_preserved', False)
        if camera_preserved == has_camera_info:
            char_score += 1
            char_count += 1

        # Timestamp preserved
        timestamp_preserved = characteristics.get('timestamp_preserved', False)
        if timestamp_preserved == has_timestamp:
            char_score += 1
            char_count += 1

        if char_count > 0:
            char_confidence = (char_score / char_count) * 0.45
            confidence += char_confidence
            matched_markers.append(f"Characteristics match: {char_score}/{char_count}")

        # 4. JFIF MARKERS CHECK (LinkedIn specific - SMOKING GUN для детекции AI)
        jfif_markers = profile.get('jfif_markers')
        if jfif_markers and raw_exif:
            jfif_score = self._check_jfif_markers(raw_exif, jfif_markers)

            if jfif_score > 0:
                # Positive match: реальное фото на LinkedIn
                confidence += jfif_score * 0.15  # Бонус до 15%
                matched_markers.append(f"JFIF markers match real photo (bonus: +{jfif_score*0.15:.2f})")
                logger.info(f"    ✅ JFIF markers indicate REAL photo on LinkedIn")
            elif jfif_score < 0:
                # Negative match: AI фото на LinkedIn
                confidence += jfif_score * 0.20  # Штраф до -20%
                matched_markers.append(f"JFIF markers match AI photo (penalty: {jfif_score*0.20:.2f})")
                logger.warning(f"    🚨 JFIF markers indicate AI photo on LinkedIn")

        return confidence, matched_markers

    def _check_jfif_markers(self, raw_exif: Dict, jfif_markers: Dict) -> float:
        """
        Проверить JFIF маркеры для детекции AI на LinkedIn

        Args:
            raw_exif: EXIF данные изображения
            jfif_markers: Профиль JFIF маркеров из конфигурации

        Returns:
            float: +1.0 если совпадает с real_photo
                   -1.0 если совпадает с ai_photo
                    0.0 если не определено
        """
        real_pattern = jfif_markers.get('real_photo', {})
        ai_pattern = jfif_markers.get('ai_photo', {})

        real_score = 0
        ai_score = 0
        total_checks = 0

        # Извлекаем JFIF данные из EXIF
        jfif_version = raw_exif.get('JFIFVersion') or raw_exif.get('JFIF')
        x_resolution = raw_exif.get('XResolution')
        y_resolution = raw_exif.get('YResolution')
        encoding_process = raw_exif.get('EncodingProcess')
        bits_per_sample = raw_exif.get('BitsPerSample')
        color_components = raw_exif.get('ColorComponents')
        ycbcr_subsampling = raw_exif.get('YCbCrSubSampling')

        # Определяем File Type через format или расширение
        file_type = None
        if 'FileType' in raw_exif:
            file_type = raw_exif['FileType']
        elif 'format' in raw_exif:
            file_type = raw_exif['format']

        # CHECK 1: JFIF Version
        total_checks += 1
        if jfif_version:
            # Версия присутствует - признак реального фото
            real_score += 1
            logger.debug(f"      JFIF Version present: {jfif_version} → real photo")
        else:
            # Версия отсутствует - признак AI
            ai_score += 1
            logger.debug(f"      JFIF Version missing → AI photo")

        # CHECK 2: Resolution
        total_checks += 1
        if x_resolution and y_resolution:
            real_score += 1
            logger.debug(f"      Resolution present: {x_resolution}x{y_resolution} → real photo")
        else:
            ai_score += 1
            logger.debug(f"      Resolution missing → AI photo")

        # CHECK 3: Encoding Process
        total_checks += 1
        if encoding_process:
            real_score += 1
            logger.debug(f"      Encoding Process present: {encoding_process} → real photo")
        else:
            ai_score += 1
            logger.debug(f"      Encoding Process missing → AI photo")

        # CHECK 4: File Type
        total_checks += 1
        if file_type:
            if file_type.upper() == 'JPEG' or file_type.upper() == 'JPG':
                real_score += 1
                logger.debug(f"      File Type JPEG → real photo")
            elif file_type.upper() == 'PNG':
                ai_score += 1
                logger.debug(f"      File Type PNG → AI photo")

        # CHECK 5: Bits Per Sample (опционально)
        if bits_per_sample:
            if bits_per_sample == real_pattern.get('bits_per_sample'):
                real_score += 0.5
                logger.debug(f"      Bits Per Sample matches real pattern: {bits_per_sample}")

        # CHECK 6: Color Components (опционально)
        if color_components:
            if color_components == real_pattern.get('color_components'):
                real_score += 0.5
                logger.debug(f"      Color Components matches real pattern: {color_components}")

        # Нормализуем score
        if total_checks == 0:
            return 0.0

        real_ratio = real_score / total_checks
        ai_ratio = ai_score / total_checks

        logger.debug(f"      JFIF Check: real={real_score}/{total_checks} ({real_ratio:.2f}), ai={ai_score}/{total_checks} ({ai_ratio:.2f})")

        # Если > 75% маркеров указывают на реальное фото
        if real_ratio >= 0.75:
            return 1.0
        # Если > 75% маркеров указывают на AI фото
        elif ai_ratio >= 0.75:
            return -1.0
        # Если 50-75% - частичное совпадение
        elif real_ratio >= 0.5:
            return real_ratio
        elif ai_ratio >= 0.5:
            return -ai_ratio
        else:
            # Не определено
            return 0.0
