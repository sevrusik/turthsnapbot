# 📡 API Reference - FraudLens Detection API

**Version**: 1.0.0
**Base URL**: `http://localhost:8000/api/v1`
**Production URL**: `https://api.truthsnap.ai/api/v1`

---

## Overview

FraudLens API provides AI-powered image authenticity detection through a simple REST API. It analyzes images for signs of AI generation, manipulation, and deepfakes.

---

## Authentication

**MVP**: No authentication required for localhost
**Production**: Bearer token authentication

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/consumer/verify
```

---

## Endpoints

### 1. Health Check

Check API status and availability.

**Endpoint**: `GET /health`

**Request**:
```bash
curl http://localhost:8000/api/v1/health
```

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-14T12:00:00Z"
}
```

---

### 2. Verify Image (Consumer Endpoint)

Analyze an image for AI generation and manipulation.

**Endpoint**: `POST /consumer/verify`

**Content-Type**: `multipart/form-data`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | file | Yes | Image file (JPEG, PNG, WebP) |
| `detail_level` | string | No | `basic` or `detailed` (default: `basic`) |

**Request Example**:
```bash
curl -X POST http://localhost:8000/api/v1/consumer/verify \
  -F "image=@photo.jpg" \
  -F "detail_level=detailed"
```

**Response** `200 OK`:
```json
{
  "verdict": "ai_generated",
  "confidence": 0.87,
  "watermark_detected": false,
  "watermark_details": null,
  "metadata_analysis": {
    "camera": null,
    "software": "Adobe Photoshop 2024",
    "gps_location": null,
    "creation_date": "2024-01-10T15:30:00Z",
    "suspicious_metadata": true
  },
  "detection_layers": [
    {
      "layer": "JPEG Artifacts",
      "status": "FAIL",
      "score": 0.85,
      "reason": "Missing JPEG compression patterns",
      "confidence": 0.85
    },
    {
      "layer": "High-Frequency Analysis",
      "status": "FAIL",
      "score": 0.78,
      "reason": "Unnatural high-frequency patterns",
      "confidence": 0.80
    },
    {
      "layer": "Power Spectrum",
      "status": "FAIL",
      "score": 0.92,
      "reason": "Anomalous spectral distribution",
      "confidence": 0.75
    },
    {
      "layer": "Periodic Patterns",
      "status": "PASS",
      "score": 0.15,
      "reason": "No artificial periodicities",
      "confidence": 0.70
    }
  ],
  "processing_time_ms": 35,
  "api_version": "1.0.0"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `verdict` | string | `real`, `ai_generated`, `manipulated`, or `inconclusive` |
| `confidence` | float | 0.0-1.0, higher = more confident |
| `watermark_detected` | boolean | True if SynthID/C2PA/Meta watermark found |
| `watermark_details` | object | Details about detected watermark (if any) |
| `metadata_analysis` | object | EXIF/metadata analysis results |
| `detection_layers` | array | Individual detector results (detailed mode only) |
| `processing_time_ms` | integer | Processing time in milliseconds |
| `api_version` | string | API version |

**Error Responses**:

**400 Bad Request** - Invalid input:
```json
{
  "detail": "Image file is required"
}
```

**413 Payload Too Large** - File too large:
```json
{
  "detail": "Image size exceeds 20MB limit"
}
```

**422 Unprocessable Entity** - Unsupported format:
```json
{
  "detail": "Unsupported image format. Supported: JPEG, PNG, WebP"
}
```

**500 Internal Server Error** - Processing error:
```json
{
  "detail": "Image analysis failed",
  "error": "FFT computation error"
}
```

---

## Verdict Types

| Verdict | Description | Typical Confidence |
|---------|-------------|-------------------|
| `real` | Appears to be a genuine photograph | 0.7-0.95 |
| `ai_generated` | Likely created by AI (Midjourney, DALL-E, etc.) | 0.75-0.98 |
| `manipulated` | Real photo but digitally altered | 0.65-0.90 |
| `inconclusive` | Cannot determine with confidence | 0.0-0.60 |

---

## Detection Layers

When `detail_level=detailed`, the response includes individual detector results:

### 1. **JPEG Artifacts**
- Analyzes 8x8 DCT block compression patterns
- Real photos show characteristic JPEG artifacts
- AI images often lack these patterns

### 2. **High-Frequency Analysis**
- Examines high-frequency content distribution
- AI images are often over-smoothed or have unnatural HF patterns

### 3. **Power Spectrum**
- Checks if image follows natural 1/f² power law
- AI-generated images often deviate from this

### 4. **Periodic Patterns**
- Detects GAN fingerprints and periodic artifacts
- Some AI models leave characteristic frequency signatures

### 5. **Metadata Analysis**
- EXIF data validation
- Camera/software detection
- Timestamp consistency checks

### 6. **Watermark Detection** (Coming Soon)
- SynthID detection
- C2PA verification
- Meta invisible watermarks

---

## Rate Limits

**Development** (localhost):
- No rate limits

**Production**:
- Free tier: 100 requests/day
- Pro tier: 10,000 requests/day
- Enterprise: Custom limits

---

## Performance

| Metric | Value |
|--------|-------|
| **Average Response Time** | 30-50ms |
| **p95 Response Time** | 100ms |
| **p99 Response Time** | 200ms |
| **Throughput** | 30+ images/second |
| **Uptime SLA** | 99.9% |

**Performance after FFT optimization**:
- FFT detection: **31.5 images/second**
- 177x faster than original implementation

---

## Example Use Cases

### Basic Photo Verification

```python
import requests

def verify_photo(image_path):
    with open(image_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/consumer/verify',
            files={'image': f}
        )
    return response.json()

result = verify_photo('suspect_photo.jpg')
print(f"Verdict: {result['verdict']}")
print(f"Confidence: {result['confidence']:.0%}")
```

### Detailed Analysis

```python
def detailed_analysis(image_path):
    with open(image_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/consumer/verify',
            files={'image': f},
            data={'detail_level': 'detailed'}
        )

    result = response.json()

    print(f"Overall: {result['verdict']} ({result['confidence']:.0%})")
    print("\nDetection Layers:")
    for layer in result['detection_layers']:
        status_emoji = "✅" if layer['status'] == 'PASS' else "❌"
        print(f"{status_emoji} {layer['layer']}: {layer['reason']}")

    return result

detailed_analysis('photo.jpg')
```

### Batch Processing

```python
import asyncio
import aiohttp

async def verify_batch(image_paths):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for path in image_paths:
            task = verify_image_async(session, path)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

async def verify_image_async(session, image_path):
    with open(image_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('image', f, filename=image_path)

        async with session.post(
            'http://localhost:8000/api/v1/consumer/verify',
            data=data
        ) as resp:
            return await resp.json()

# Process 100 images in parallel
images = [f'photo_{i}.jpg' for i in range(100)]
results = asyncio.run(verify_batch(images))
```

---

## cURL Examples

### Basic Verification

```bash
curl -X POST http://localhost:8000/api/v1/consumer/verify \
  -F "image=@photo.jpg"
```

### Detailed Analysis

```bash
curl -X POST http://localhost:8000/api/v1/consumer/verify \
  -F "image=@photo.jpg" \
  -F "detail_level=detailed" \
  | jq '.'
```

### Save Response to File

```bash
curl -X POST http://localhost:8000/api/v1/consumer/verify \
  -F "image=@photo.jpg" \
  -F "detail_level=detailed" \
  -o result.json
```

### Check Multiple Images

```bash
for img in *.jpg; do
  echo "Analyzing $img..."
  curl -X POST http://localhost:8000/api/v1/consumer/verify \
    -F "image=@$img" \
    | jq '.verdict, .confidence'
done
```

---

## SDKs

### Python

```python
from fraudlens import FraudLensClient

client = FraudLensClient(api_key='your_api_key')
result = client.verify_image('photo.jpg', detail_level='detailed')
print(result.verdict, result.confidence)
```

### Node.js

```javascript
const FraudLens = require('fraudlens-sdk');

const client = new FraudLens({ apiKey: 'your_api_key' });
const result = await client.verifyImage('photo.jpg', { detailLevel: 'detailed' });
console.log(result.verdict, result.confidence);
```

### Go

```go
import "github.com/fraudlens/go-sdk"

client := fraudlens.NewClient("your_api_key")
result, err := client.VerifyImage("photo.jpg", fraudlens.DetailedAnalysis)
fmt.Println(result.Verdict, result.Confidence)
```

---

## Webhooks (Coming Soon)

Subscribe to real-time notifications for async processing.

**Endpoint**: `POST /webhooks/subscribe`

```json
{
  "url": "https://your-app.com/webhook",
  "events": ["analysis.complete", "analysis.failed"]
}
```

---

## Changelog

### v1.0.0 (January 14, 2026)
- ✅ Initial release
- ✅ FFT-based detection (177x optimized)
- ✅ Metadata analysis
- ✅ JPEG artifact detection
- ✅ Consumer endpoint
- ✅ Health check endpoint

### Upcoming Features
- 🔜 Watermark detection (SynthID, C2PA, Meta)
- 🔜 Real-time ML model integration
- 🔜 Batch processing endpoint
- 🔜 Webhook support
- 🔜 Video analysis
- 🔜 API authentication

---

## Support

- **Documentation**: https://docs.truthsnap.ai
- **API Status**: https://status.truthsnap.ai
- **Issues**: https://github.com/truthsnap/fraudlens/issues
- **Email**: api@truthsnap.ai

---

## License

Proprietary - All rights reserved
© 2026 TruthSnap
