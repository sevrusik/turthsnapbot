# 🚀 Quick Test: OCR Watermark Detection

## Быстрый тест интеграции

### 1. Запустить FraudLens API

```bash
cd /Volumes/KINGSTON/Projects/FraudLensAI
python -m uvicorn backend.api.main:app --reload --port 8000
```

Проверить health:
```bash
curl http://localhost:8000/api/v1/health
```

---

### 2. Протестировать OCR детектор напрямую

```bash
cd /Volumes/KINGSTON/Projects/TruthSnapBot

# Тест с Gemini изображением (если есть)
python test_ocr_simple.py /path/to/gemini_image.png

# Или любым другим AI изображением с watermark
python test_ocr_simple.py /path/to/ai_image.jpg
```

**Ожидаемый результат** (если watermark найден):
```
🧪 Testing Visual Watermark Detector
================================================================================
✅ Visual Watermark Detection Result:
   Has Watermark: True
   Confidence: 90.00%
   Type: Google Gemini/Imagen
   Method: ocr_text_detection
   Text Found: 'made with google ai'
   Location: bottom_right
================================================================================
```

---

### 3. Протестировать через FraudLens API

```bash
# Тест полной интеграции
python test_watermark_integration.py /path/to/ai_image.jpg
```

**Ожидаемый результат**:
```
📡 STEP 1: Calling FraudLens API...
✅ FraudLens API Response:
   Verdict: ai_generated
   Confidence: 98.00%
   Watermark Detected: True
   Processing Time: 1234ms

🔍 Watermark Analysis:
   Type: Google Gemini/Imagen
   Confidence: 90.00%
   Method: ocr_text_detection
   Text Found: 'made with google ai'
   Location: bottom_right

📊 SUMMARY:
✅ AI Watermark DETECTED via ocr_text_detection
```

---

### 4. Тест через Telegram бота

```bash
cd /Volumes/KINGSTON/Projects/TruthSnapBot
docker-compose up -d
```

Отправить изображение с AI watermark в бота как **документ** (чтобы сохранить EXIF и качество для OCR):

1. Открыть бота в Telegram
2. Прикрепить файл → выбрать "Send as Document"
3. Отправить

**Ожидаемый ответ**:
```
📸 Анализ завершён

🔴 AI-сгенерированное изображение
Уверенность: 90%

🔍 Детали:
• Обнаружен watermark: Google Gemini/Imagen
• Метод: OCR текст
• Найдено: "made with google ai"
• Расположение: правый нижний угол

⚠️ Это изображение было создано ИИ
```

---

## Где найти тестовые изображения

### Создать тестовое изображение

1. **Google Gemini** (https://gemini.google.com)
   - Запросить: "Generate an image of a sunset"
   - Скачать изображение
   - У некоторых версий есть watermark "made with google ai"

2. **DALL-E** (https://openai.com/dall-e)
   - Генерировать изображение
   - Часто имеет цветные квадраты в углу

3. **Midjourney** (https://midjourney.com)
   - Некоторые версии добавляют "Midjourney" текст

---

## Troubleshooting

### OCR не находит текст

**Причины**:
1. Изображение было сжато (Telegram сжимает фото)
   - **Решение**: Отправлять как документ, не как фото

2. Tesseract не установлен
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu
   apt-get install tesseract-ocr
   ```

3. Watermark слишком маленький/размытый
   - **Решение**: OCR работает лучше на оригинальных изображениях

### FraudLens API не отвечает

```bash
# Проверить что API запущен
curl http://localhost:8000/api/v1/health

# Проверить логи
docker-compose logs fraudlens-api
```

### Watermark не детектируется

**Проверьте**:
1. Изображение действительно имеет текстовый watermark?
2. Tesseract установлен и доступен?
   ```bash
   tesseract --version
   ```
3. Watermark в поддерживаемом формате?
   - Текст должен быть в углах изображения
   - Поддерживаемые паттерны: "gemini", "dall-e", "midjourney", "ai generated"

---

## Логи для дебага

### Включить DEBUG логи

```bash
# В .env
LOG_LEVEL=DEBUG
```

Пример логов:
```
[INFO] 🔍 Starting OCR watermark detection on 1920x1080 image
[INFO] 📝 OCR bottom_right: 'made with google ai'
[INFO] 🎯 Watermark found via OCR: 'made with google ai' in bottom_right
[INFO] ✅ AI watermark detected: Google Gemini/Imagen
```

---

## Что дальше?

После успешного теста OCR watermark detection:

1. ✅ Интеграция готова и работает
2. ✅ FraudLens API автоматически детектирует watermarks
3. ✅ TruthSnapBot получает результаты и показывает пользователю

**Нет дополнительных действий не требуется!**

Watermark detection работает автоматически при каждой проверке фото.
