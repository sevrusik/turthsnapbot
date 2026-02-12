# Image Verification Flow - Полный анализ

## Проблема: Canon EOS 5D Mark III с Lightroom определяется как 95% AI

### EXIF фото:
- Make: **Canon**
- Model: **Canon EOS 5D Mark III**
- **SerialNumber: 182029011977** ← SMOKING GUN
- **LensSerialNumber: 00000409ab** ← SMOKING GUN
- LensModel: EF85mm f/1.8 USM
- Software: **Adobe Photoshop CS6 (Macintosh)**
- **CreatorTool (XMP): Adobe Photoshop Lightroom 5.3** ← НЕ ПРОВЕРЯЕТСЯ!
- DateTimeOriginal: 2016:02:03 19:08:51
- DateTime: 2019:10:21 20:42:02

---

## Процесс проверки изображений

### 1️⃣ TELEGRAM BOT FLOW (preserve_exif=False)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. БОТ (truthsnap-bot/app/bot/handlers/photo.py)              │
└─────────────────────────────────────────────────────────────────┘
         │
         │ image_bytes + preserve_exif=False
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. API ENDPOINT: /api/v1/verify                                │
│    (fraudlens/backend/api/routes/consumer.py:302)             │
└─────────────────────────────────────────────────────────────────┘
         │
         │ telegram_mode = True (because preserve_exif=False)
         │ source_platform = None
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ПАРАЛЛЕЛЬНЫЕ ДЕТЕКТОРЫ (7 штук)                             │
├─────────────────────────────────────────────────────────────────┤
│ ① fraud_detector.detect_ai_generation(image_bytes)             │
│    → AI heuristic score (0-1)                                   │
│                                                                  │
│ ② watermark_detector.detect(image_bytes)                       │
│    → C2PA watermark detection                                   │
│                                                                  │
│ ③ visual_watermark_detector.detect_watermark(temp_path)        │
│    → OCR-based watermark detection                              │
│                                                                  │
│ ④ metadata_analyzer.analyze(image_bytes)                       │
│    → EXIF extraction (GPS, Device, Software)                    │
│    ✅ USES: image.getexif() (MODERN)                           │
│                                                                  │
│ ⑤ metadata_validator.validate(image_bytes)                     │
│    → EXIF fraud detection (10 layers)                           │
│    ❌ USES: image._getexif() (DEPRECATED!)                     │
│    ❌ NOT CHECKING: CreatorTool, SerialNumber                   │
│                                                                  │
│ ⑥ fft_detector.analyze(image_bytes)                            │
│    → Frequency domain analysis                                  │
│                                                                  │
│ ⑦ face_swap_detector.analyze(image_bytes)                      │
│    → Deepfake detection                                         │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Results aggregated
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. VERDICT DETERMINATION                                        │
│    (consumer.py:629 - determine_consumer_verdict())            │
├─────────────────────────────────────────────────────────────────┤
│ Input:                                                           │
│  - detection (AI score)                                          │
│  - watermark                                                     │
│  - metadata                                                      │
│  - validation (fraud_score from validator)                      │
│  - fft_score                                                     │
│  - face_swap_score                                               │
│  - visual_watermark                                              │
│  - source_platform (None for bot)                               │
│                                                                  │
│ SMOKING GUNS (priority):                                        │
│  1. Visual watermark (AI generator) → ai_generated (98%)        │
│  2. C2PA watermark → ai_generated (95%)                         │
│  3. AI software in EXIF → ai_generated (98%)                    │
│  4. Screenshot detected → manipulated (95%)                     │
│  5. High fraud score (>=80) → ai_generated/manipulated          │
│                                                                  │
│ WEIGHTED SCORING:                                               │
│  score = (ai_heuristic × 0.35) +                               │
│          (fft_score × 0.30) +                                   │
│          (metadata_risk × 0.25) +                               │
│          (face_swap × 0.10)                                     │
│          - social_media_reduction                               │
│                                                                  │
│ SPECIAL CASES:                                                  │
│  - Trusted software (Lightroom) → reduce metadata_risk by 0.30 │
│    ❌ ПРОБЛЕМА: Проверяется только red_flags!                  │
│  - Stock photo → reduce AI heuristic                            │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2️⃣ LINKEDIN/FACEBOOK FLOW (source=linkedin)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BROWSER EXTENSION / API CALL                                │
│    source="linkedin" or "instagram" or "facebook"              │
└─────────────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. API ENDPOINT: /api/v1/analyze or /api/v1/verify            │
└─────────────────────────────────────────────────────────────────┘
         │
         │ telegram_mode = True (source is not None)
         │ source_platform = "linkedin"
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ПАРАЛЛЕЛЬНЫЕ ДЕТЕКТОРЫ (9 штук для social media)           │
├─────────────────────────────────────────────────────────────────┤
│ Same as above (7 detectors) +                                   │
│                                                                  │
│ ⑧ prnu_detector.detect(temp_path)                              │
│    → PRNU sensor noise detection                                │
│    ✅ SURVIVES LinkedIn/Instagram compression                   │
│    → has_prnu, prnu_strength, fraud_score                       │
│                                                                  │
│ ⑨ intrinsic_detector.detect(temp_path)                         │
│    → Intrinsic camera fingerprints                              │
│    → total_score, detection_methods, confidence                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. SOCIAL MEDIA NORMALIZATION (consumer.py:761-878)           │
├─────────────────────────────────────────────────────────────────┤
│ PRNU-BASED DECISION:                                            │
│                                                                  │
│ Case 1: PNG + FFT>0.65 + PRNU detected                         │
│  → AI with SYNTHETIC NOISE                                      │
│  → metadata_risk += 0.25 (BOOST)                               │
│  → Real cameras shoot JPEG, not PNG                             │
│                                                                  │
│ Case 2: JPEG + Strong PRNU + Low fraud score                   │
│  → Check intrinsic detector                                     │
│  → If high FFT (>0.75) → AI (social media converted PNG→JPEG)  │
│  → If low FFT → REAL PHOTO (aggressive normalization)          │
│     - fft_score × 0.4 (reduce by 60%)                          │
│     - ai_heuristic × 0.6 (reduce by 40%)                       │
│     - social_media_reduction = 0.20                             │
│                                                                  │
│ Case 3: No PRNU or weak PRNU                                   │
│  → Likely AI                                                    │
│  → No normalization                                             │
│                                                                  │
│ Case 4: Medium PRNU + high fraud score                         │
│  → MANIPULATED (splice/edit detected)                          │
│  → Minimal normalization                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚨 ПРОБЛЕМЫ В ТЕКУЩЕЙ СИСТЕМЕ

### Проблема #1: metadata_validator использует DEPRECATED метод

**Файл**: `fraudlens/backend/integrations/metadata_validator.py:222`

```python
# ❌ DEPRECATED METHOD:
exif = image._getexif()

# ✅ ДОЛЖНО БЫТЬ:
exif = image.getexif()
```

**Последствия:**
- Теряются некоторые EXIF поля
- GPS может не извлечься корректно
- Несовместимость с Pillow 10+

---

### Проблема #2: CreatorTool (XMP) НЕ ПРОВЕРЯЕТСЯ

**Текущий код проверяет:**
```python
software = exif_data.get("Software", "").lower()
# Software: "Adobe Photoshop CS6 (Macintosh)"
# → Находит "photoshop" → penalty_reduction = 30
```

**НЕ проверяется:**
```python
creator_tool = xmp_data.get("CreatorTool", "").lower()
# CreatorTool: "Adobe Photoshop Lightroom 5.3 (Macintosh)"
# → Должен находить "lightroom" → penalty_reduction = 50
```

**Результат:**
- Score = 85 - 30 = **55** (medium risk) ❌
- Должно быть: 85 - 50 = **35** (low risk) ✅

---

### Проблема #3: Serial Numbers НЕ ПРОВЕРЯЮТСЯ

**Есть в EXIF:**
- `SerialNumber: 182029011977` ← Camera body serial
- `LensSerialNumber: 00000409ab` ← Lens serial

**НЕ проверяется нигде в коде!**

**Это SMOKING GUN для реального фото:**
- AI не может создать валидные serial numbers
- Serial numbers уникальны для каждой камеры/объектива
- Наличие serial = -30 к fraud score (БОНУС)

---

### Проблема #4: exiftool данные НЕ ОБЪЕДИНЯЮТСЯ

**TruthSnapBot:**
```python
exif_data = self._extract_exif(image)        # deprecated _getexif()
exiftool_data = self._extract_exiftool(bytes) # exiftool

# ❌ НЕ ОБЪЕДИНЯЮТСЯ! Используются раздельно
apple_check = self._check_apple_runtime(exif_data, exiftool_data)
software_check = self._check_software_manipulation(exif_data)  # ← Только exif_data!
```

**FraudLensAI (правильно):**
```python
exif_data = self._extract_complete_exif(image_path)    # piexif
exiftool_data = self._extract_exiftool(image_path)     # exiftool

# ✅ ОБЪЕДИНЯЮТСЯ:
exif_data.update(exiftool_data)  # exiftool has priority

# Все проверки используют объединённые данные
```

---

### Проблема #5: Trusted software проверяется НЕПРАВИЛЬНО

**Текущий код** (consumer.py:739-748):
```python
# SPECIAL CASE: Trusted software detected (Lightroom, Capture One)
trusted_software_detected = False
for flag in red_flags:  # ← Проверка в RED FLAGS!
    if flag.get("trust_level") in ["high", "medium"]:
        trusted_software_detected = True
        metadata_risk = max(0, metadata_risk - 0.30)
        break
```

**ПРОБЛЕМА:**
- Lightroom НЕ является red flag!
- Lightroom - это ПОЗИТИВНЫЙ сигнал
- Но проверяется только если он попал в red_flags
- Для этого фото Lightroom не в red_flags (он в CreatorTool)

**РЕШЕНИЕ:**
```python
# Проверять ДО вычисления red_flags:
software = metadata.get("raw_exif", {}).get("Software", "").lower()
creator_tool = metadata.get("raw_exif", {}).get("CreatorTool", "").lower()

TRUSTED_SOFTWARE = {
    "lightroom": {"trust_level": "high", "bonus": -30},
    "capture one": {"trust_level": "high", "bonus": -30},
    "photoshop": {"trust_level": "medium", "bonus": -15},
}

for name, info in TRUSTED_SOFTWARE.items():
    if name in software or name in creator_tool:
        metadata_risk += info["bonus"] / 100.0  # Negative = bonus
        break
```

---

## 📊 ЧТО ПРОИСХОДИТ С CANON ФОТО

### Текущий флоу для Canon EOS 5D Mark III:

```
1. metadata_analyzer.analyze(bytes)
   ✅ Использует getexif()
   ✅ Извлекает: Make, Model, Software
   ⚠️  SerialNumber НЕ добавляется в raw_exif

2. metadata_validator.validate(bytes)
   ❌ Использует _getexif() (deprecated)
   ❌ НЕ проверяет CreatorTool (XMP)
   ❌ НЕ проверяет SerialNumber

   Software check:
   - Software: "Adobe Photoshop CS6"
   - Finds "photoshop" → score = 85 - 30 = 55
   - CreatorTool: "Lightroom" → NOT CHECKED

   Result: fraud_score = 55 (medium risk)

3. determine_consumer_verdict()
   - metadata_risk = 55 / 100.0 = 0.55

   Trusted software check:
   - Ищет в red_flags with trust_level
   - Photoshop есть, но trust_level = "medium"
   - Reduction: 0.30
   - metadata_risk = 0.55 - 0.30 = 0.25

   Weighted score:
   - ai_heuristic × 0.35 = 0.XX
   - fft_score × 0.30 = 0.XX
   - metadata_risk × 0.25 = 0.0625
   - face_swap × 0.10 = 0.XX

   Combined score = 0.XX (зависит от AI/FFT детекторов)

   ⚠️ Если AI detector даёт высокий score → verdict = "ai_generated"
   ⚠️ Если FFT detector даёт высокий score → verdict = "ai_generated"
```

---

## 🔧 ИСПРАВЛЕНИЯ

### Fix #1: Обновить _extract_exif() в metadata_validator.py

```python
def _extract_exif(self, image: Image.Image) -> Dict:
    """Extract EXIF data from image"""
    exif_data = {}

    try:
        # ✅ MODERN METHOD:
        exif = image.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                try:
                    exif_data[tag] = str(value)
                except:
                    pass
    except:
        pass

    return exif_data
```

### Fix #2: Проверять CreatorTool в _check_software_manipulation()

```python
def _check_software_manipulation(self, exif_data: Dict, exiftool_data: Dict) -> Dict:
    """Check both Software field (EXIF) and CreatorTool (XMP)"""

    software = exif_data.get("Software", "").lower()
    creator_tool = exiftool_data.get("XMP:CreatorTool", "").lower()

    # Check BOTH fields
    combined = software + " " + creator_tool

    # Check for Lightroom first (higher priority)
    for trusted_name, trust_info in self.TRUSTED_PHOTO_SOFTWARE.items():
        if trusted_name in combined:
            # Return highest trust level found
            ...
```

### Fix #3: Добавить проверку Serial Numbers

```python
def _check_camera_authenticity(self, exif_data: Dict, exiftool_data: Dict) -> Dict:
    """
    Layer 0: Camera Authenticity Check

    Serial numbers = SMOKING GUN for real photos
    AI cannot create valid camera/lens serials

    Returns negative score = BONUS for authentic cameras
    """
    camera_serial = exiftool_data.get("EXIF:SerialNumber") or \
                   exiftool_data.get("MakerNotes:SerialNumber")
    lens_serial = exiftool_data.get("EXIF:LensSerialNumber") or \
                 exiftool_data.get("MakerNotes:LensSerialNumber")

    if camera_serial and lens_serial:
        # Both serials present = highly authentic
        return {
            "layer": "Camera Authenticity",
            "status": "PASS",
            "score": -30,  # BONUS (negative score)
            "reason": f"Camera + Lens serials detected (Camera: {camera_serial})",
            "description": "Serial numbers = smoking gun for real camera"
        }
    elif camera_serial or lens_serial:
        # One serial = still good
        return {
            "layer": "Camera Authenticity",
            "status": "PASS",
            "score": -20,
            "reason": "Camera serial detected",
            "description": "Serial number indicates real camera"
        }

    return {"layer": "Camera Authenticity", "status": "N/A", "score": 0}
```

### Fix #4: Объединить exif_data и exiftool_data

```python
# В validate():
exif_data = self._extract_exif(image)
exiftool_data = self._extract_exiftool(image_bytes)

# ✅ MERGE DATA:
if exiftool_data:
    exif_data.update(exiftool_data)  # exiftool has priority

# Now all checks use combined data
```

---

## 🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ПОСЛЕ ИСПРАВЛЕНИЙ

### Для Canon EOS 5D Mark III + Lightroom + Photoshop:

```
1. Camera Authenticity Check:
   ✅ SerialNumber: 182029011977
   ✅ LensSerialNumber: 00000409ab
   → score = -30 (BONUS)

2. Software Check:
   ✅ CreatorTool: "Lightroom 5.3"
   ✅ Software: "Photoshop CS6"
   → Lightroom found first → penalty_reduction = 50
   → score = 85 - 50 = 35

3. Total metadata fraud_score:
   - Base: 0
   - Camera authenticity: -30
   - Software editing: +35
   - GPS missing: +0 (telegram_mode или допустимо для студийных фото)
   → Total = 5-10 (LOW RISK)

4. Verdict:
   - metadata_risk = 0.05-0.10
   - Combined score = LOW
   → verdict = "real" with high confidence ✅
```

---

## 🔍 СРАВНЕНИЕ: ДО vs ПОСЛЕ

| Параметр | ДО | ПОСЛЕ |
|----------|-----|--------|
| EXIF extraction | _getexif() ❌ | getexif() ✅ |
| CreatorTool check | NOT checked ❌ | Checked ✅ |
| Serial Numbers | NOT checked ❌ | Checked ✅ |
| Data merge | Separate ❌ | Merged ✅ |
| Canon fraud_score | ~55 (medium) ❌ | ~5-10 (low) ✅ |
| Final verdict | AI 95% ❌ | Real 90%+ ✅ |

---

## 📝 ПРИОРИТЕТЫ ИСПРАВЛЕНИЙ

### 🔴 CRITICAL (сейчас):
1. Fix #1: Обновить _extract_exif() → getexif()
2. Fix #4: Объединить exif_data + exiftool_data

### 🟡 HIGH (скоро):
3. Fix #2: Проверять CreatorTool
4. Fix #3: Добавить проверку Serial Numbers

### 🟢 MEDIUM (потом):
5. Рефакторинг trusted software logic
6. Добавить device profile validation

---

**Дата анализа**: 2026-02-12
**Версия**: TruthSnapBot commit 2891b01
