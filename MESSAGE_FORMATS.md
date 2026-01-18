# 📱 Message Format Comparison - Free vs Pro

## Overview

TruthSnapBot now has **two message formats**:
- **Free Tier**: Simple verdict with basic guidance
- **Pro Tier**: Detailed forensic analysis with digital footprint data

---

## Free Tier Message Format

### Example 1: AI-Generated (90%)

```
🤖 AI-GENERATED

Confidence: 90.0%

⏱ Analysis time: 1.5s

⚠️ This image appears to be AI-generated.

If you're being blackmailed with this photo:
1. DO NOT pay the blackmailer
2. Save this analysis as evidence
3. Report to authorities
4. Block the sender

💎 Want detailed analysis? /subscribe
```

**Buttons**:
- 📄 Get PDF Report
- 📤 Share Result

---

### Example 2: Real Photo

```
✅ REAL PHOTO

Confidence: 85.0%

⏱ Analysis time: 1.2s

✅ This appears to be a real photograph.

Our AI did not detect manipulation or generation patterns.

💎 Want detailed analysis? /subscribe
```

---

### Example 3: Manipulated

```
⚠️ MANIPULATED

Confidence: 75.0%

⏱ Analysis time: 1.8s

⚠️ This image shows signs of manipulation.

If you're being blackmailed, contact authorities immediately.

💎 Want detailed analysis? /subscribe
```

---

## Pro Tier Message Format

### Example 1: AI-Generated with High Fraud Score

```
🤖 AI-GENERATED (90.0%)

⏱ Analysis time: 1.5s

🗂 DIGITAL FOOTPRINT:
📅 Captured: No timestamp (suspicious)
🛠 Created with: Unknown/Stripped
📱 Device: No Camera Data (AI Signature)
📍 GPS: None Detected

⚠️ RED FLAGS:
• AI Pattern: Strong (GAN/Diffusion)
• Metadata: Stripped/Manipulated (90/100)
• GPS data missing
• Missing timestamps

🛡 WHAT TO DO:
• DO NOT pay the blackmailer
• Save this analysis as evidence
• Report to authorities immediately
• Block the sender

This image shows strong AI generation signatures.

📄 Analysis ID: ANL-20260116-dbbb0eed
```

**Buttons**:
- 📄 Get PDF Report
- 📤 Share Result

---

### Example 2: AI-Generated with Photoshop Detection

```
🤖 AI-GENERATED (98.0%)

⏱ Analysis time: 0.6s

🗂 DIGITAL FOOTPRINT:
📅 Captured: 2024-01-14 14:30:15
🛠 Created with: Adobe Photoshop 2024 (Generative Fill) ⚠️ (AI Signature)
📱 Device: No Camera Data (AI Signature)
📍 GPS: None Detected

⚠️ RED FLAGS:
• AI Pattern: Strong (GAN/Diffusion)
• Metadata: Stripped/Manipulated (85/100)
• Watermark: Adobe Content Credentials detected
• Software: Adobe Photoshop detected

🛡 WHAT TO DO:
• DO NOT pay the blackmailer
• Save this analysis as evidence
• Report to authorities immediately
• Block the sender

This image shows strong AI generation signatures.

📄 Analysis ID: ANL-20260116-a1b2c3d4
```

---

### Example 3: AI-Generated with Visual Watermark (OCR)

```
🤖 AI-GENERATED (98.0%)

⏱ Analysis time: 2.1s

🗂 DIGITAL FOOTPRINT:
📅 Captured: No timestamp (suspicious)
🛠 Created with: Unknown/Stripped
📱 Device: No Camera Data (AI Signature)
📍 GPS: None Detected

⚠️ RED FLAGS:
• AI Pattern: Strong (GAN/Diffusion)
• Metadata: Stripped/Manipulated (90/100)
• Visual Mark: "made with google ai" (google)
• Frequency Analysis: AI artifacts detected

🛡 WHAT TO DO:
• DO NOT pay the blackmailer
• Save this analysis as evidence
• Report to authorities immediately
• Block the sender

This image shows strong AI generation signatures.

📄 Analysis ID: ANL-20260116-e5f6g7h8
```

---

### Example 4: Real Photo from iPhone

```
✅ REAL PHOTO (85.0%)

⏱ Analysis time: 1.2s

🗂 DIGITAL FOOTPRINT:
📅 Captured: 2024-01-16 10:23:45
🛠 Created with: 17.1.2
📱 Device: Apple iPhone 14 Pro
📍 GPS: 37.7749, -122.4194

🛡 WHAT TO DO:
• This appears to be an authentic photo
• Consider context and source
• If threatened, still report to authorities

No AI or manipulation detected.

📄 Analysis ID: ANL-20260116-i9j0k1l2
```

---

### Example 5: Manipulated with Face Swap

```
⚠️ MANIPULATED (82.0%)

⏱ Analysis time: 2.8s

🗂 DIGITAL FOOTPRINT:
📅 Captured: 2024-01-15 18:30:12
🛠 Created with: PhotoApp Pro
📱 Device: Samsung Galaxy S23
📍 GPS: None Detected

⚠️ RED FLAGS:
• Face Integrity: Artifacts detected (2 faces)
• Metadata: Suspicious (65/100)
• GPS data missing
• Frequency Analysis: AI artifacts detected

🛡 WHAT TO DO:
• This image has been altered
• DO NOT pay if being blackmailed
• Save as evidence and report

Detected manipulation/editing patterns.

📄 Analysis ID: ANL-20260116-m3n4o5p6
```

---

### Example 6: Inconclusive Analysis

```
❓ INCONCLUSIVE (55.0%)

⏱ Analysis time: 1.0s

🗂 DIGITAL FOOTPRINT:
📅 Captured: No timestamp (suspicious)
🛠 Created with: Unknown/Stripped
📱 Device: Not available
📍 GPS: None Detected

⚠️ RED FLAGS:
• Metadata: Suspicious (60/100)
• Missing timestamps

🛡 WHAT TO DO:
• Analysis inconclusive
• Request manual review
• Report if being threatened

Unable to determine with high confidence.

📄 Analysis ID: ANL-20260116-q7r8s9t0
```

---

## Key Differences: Free vs Pro

| Feature | Free Tier | Pro Tier |
|---------|-----------|----------|
| **Verdict** | Simple label | Label + confidence in header |
| **Processing Time** | ✅ Shown | ✅ Shown |
| **Digital Footprint** | ❌ Not shown | ✅ Full metadata breakdown |
| **Date/Time** | ❌ Not shown | ✅ Capture timestamp |
| **Software Info** | ❌ Not shown | ✅ Creator/editing software |
| **Camera/Device** | ❌ Not shown | ✅ Make and model |
| **GPS Location** | ❌ Not shown | ✅ Coordinates if available |
| **Red Flags** | ❌ Not shown | ✅ Detailed list of issues |
| **AI Pattern** | ❌ Not shown | ✅ Strength level |
| **Metadata Score** | ❌ Not shown | ✅ Fraud score /100 |
| **Specific Flags** | ❌ Not shown | ✅ Top 2 issues listed |
| **FFT Analysis** | ❌ Not shown | ✅ Frequency domain check |
| **Face Swap** | ❌ Not shown | ✅ Deepfake detection |
| **Watermarks** | Basic info | ✅ Full details (C2PA, OCR) |
| **Analysis ID** | ❌ Not shown | ✅ Unique tracking ID |
| **PDF Report** | ✅ Available | ✅ Available |
| **Upgrade CTA** | ✅ Shown | ❌ Not shown |

---

## Implementation Details

### File: `/truthsnap-bot/app/services/notifications.py`

**Two message builders**:

1. `_build_free_message()` - Simple format for free users
2. `_build_pro_message()` - Enhanced format with forensic data

**Tier Detection**:
```python
if tier == 'pro':
    message = self._build_pro_message(...)
else:
    message = self._build_free_message(...)
```

**Data Sources**:
- `result['verdict']` - ai_generated/real/manipulated/inconclusive
- `result['confidence']` - 0.0-1.0
- `result['metadata']` - EXIF/GPS/camera data
- `result['metadata_validation']` - Fraud score + red flags
- `result['ai_signatures']` - AI pattern detection
- `result['fft_analysis']` - Frequency domain analysis
- `result['face_swap_analysis']` - Deepfake detection
- `result['watermark_detected']` - C2PA watermarks
- `result['visual_watermark']` - OCR text watermarks

---

## Testing

### Test with Free User
```python
# User tier: free
await notifier.send_analysis_result(
    chat_id=644554733,
    message_id=123,
    result=fraudlens_result,
    tier='free',
    analysis_id='ANL-20260116-test'
)
```

**Expected**: Simple message + "Want detailed analysis? /subscribe"

### Test with Pro User
```python
# User tier: pro
await notifier.send_analysis_result(
    chat_id=644554733,
    message_id=123,
    result=fraudlens_result,
    tier='pro',
    analysis_id='ANL-20260116-test'
)
```

**Expected**: Detailed message with Digital Footprint + Red Flags sections

---

## User Experience Flow

### Free User Flow
1. 📸 Upload photo → Simple verdict
2. 💎 See "Want detailed analysis?" CTA
3. 📄 Can still get PDF report
4. 💳 Click /subscribe to upgrade

### Pro User Flow
1. 📸 Upload photo → Detailed forensic analysis
2. 🗂 See full digital footprint
3. ⚠️ See specific red flags
4. 📄 Get comprehensive PDF report
5. 🔍 Track analysis via unique ID

---

## Benefits of Enhanced Pro Format

### For Users
✅ **Transparency**: See exactly what was analyzed
✅ **Evidence**: Detailed data for authorities
✅ **Education**: Understand AI detection signals
✅ **Confidence**: Know why verdict was reached

### For Support
✅ **Tracking**: Unique analysis IDs
✅ **Debugging**: Full metadata in message
✅ **Quality**: Users can verify data accuracy

### For Monetization
✅ **Value Proposition**: Clear difference vs free tier
✅ **Professional**: Forensic-grade analysis
✅ **Trust**: Shows comprehensive checking

---

## Future Enhancements

### Planned Features
- [ ] Clickable GPS coordinates (Google Maps link)
- [ ] Software detection with AI tool logos
- [ ] Expandable red flags (show all on request)
- [ ] Comparison with known AI generators
- [ ] Timeline of photo modifications
- [ ] Blockchain verification for analysis ID

---

**Status**: ✅ Implemented (2026-01-16)

**Related Files**:
- `/truthsnap-bot/app/services/notifications.py` - Message formatter
- `/fraudlens/backend/api/routes/consumer.py` - API response structure
- `/truthsnap-bot/app/workers/tasks.py` - Analysis worker

---

**Made with ❤️ for fighting deepfake blackmail**
