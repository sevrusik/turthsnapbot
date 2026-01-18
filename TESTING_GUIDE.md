# 🧪 Testing Guide - Enhanced Message Formats

## Quick Start

### 1. Set User to Pro Tier

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U truthsnap -d truthsnap

# Set user to pro tier
UPDATE users SET subscription_tier = 'pro' WHERE id = YOUR_TELEGRAM_ID;

# Verify
SELECT id, username, subscription_tier FROM users WHERE id = YOUR_TELEGRAM_ID;

# Exit
\q
```

**Or use SQL script**:
```bash
# Edit update_user_tier.sql to set your Telegram ID
docker-compose exec -T postgres psql -U truthsnap -d truthsnap < update_user_tier.sql
```

---

### 2. Test Free User Message

```bash
# Set user back to free
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "UPDATE users SET subscription_tier = 'free' WHERE id = YOUR_TELEGRAM_ID;"
```

**Then send a photo to the bot** and observe the simple message format.

---

### 3. Test Pro User Message

```bash
# Set user to pro
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "UPDATE users SET subscription_tier = 'pro' WHERE id = YOUR_TELEGRAM_ID;"
```

**Then send a photo to the bot** and observe the enhanced message format with:
- 🗂 DIGITAL FOOTPRINT section
- ⚠️ RED FLAGS section
- 🛡 WHAT TO DO section
- 📄 Analysis ID

---

## Test Scenarios

### Scenario 1: AI-Generated Image (High Fraud Score)

**Test Image**: Gemini AI generated image (PNG, no EXIF)

**Expected Free User Message**:
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

**Expected Pro User Message**:
```
🤖 AI-GENERATED (98.0%)

⏱ Analysis time: 0.6s

🗂 DIGITAL FOOTPRINT:
📅 Captured: No timestamp (suspicious)
🛠 Created with: Unknown/Stripped
📱 Device: No Camera Data (AI Signature)
📍 GPS: None Detected

⚠️ RED FLAGS:
• AI Pattern: Strong (GAN/Diffusion)
• Metadata: Stripped/Manipulated (100/100)
• Missing camera info (possible screenshot)
• GPS data missing

🛡 WHAT TO DO:
• DO NOT pay the blackmailer
• Save this analysis as evidence
• Report to authorities immediately
• Block the sender

This image shows strong AI generation signatures.

📄 Analysis ID: ANL-20260116-xxxxxxxx
```

---

### Scenario 2: Real Photo from Camera

**Test Image**: Photo taken with smartphone camera (JPEG, full EXIF)

**Expected Free User Message**:
```
✅ REAL PHOTO

Confidence: 85.0%

⏱ Analysis time: 1.2s

✅ This appears to be a real photograph.

Our AI did not detect manipulation or generation patterns.

💎 Want detailed analysis? /subscribe
```

**Expected Pro User Message**:
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

📄 Analysis ID: ANL-20260116-xxxxxxxx
```

---

### Scenario 3: Image with Adobe Photoshop AI

**Test Image**: Photo edited with Photoshop Generative Fill

**Expected Pro User Message**:
```
🤖 AI-GENERATED (98.0%)

⏱ Analysis time: 0.8s

🗂 DIGITAL FOOTPRINT:
📅 Captured: 2024-01-14 14:30:15
🛠 Created with: Adobe Photoshop 2024 (Generative Fill) ⚠️ (AI Signature)
📱 Device: Canon EOS R5
📍 GPS: None Detected

⚠️ RED FLAGS:
• AI Pattern: Strong (GAN/Diffusion)
• Metadata: Suspicious (75/100)
• Software: Adobe Photoshop detected
• GPS data missing

🛡 WHAT TO DO:
• DO NOT pay the blackmailer
• Save this analysis as evidence
• Report to authorities immediately
• Block the sender

This image shows strong AI generation signatures.

📄 Analysis ID: ANL-20260116-xxxxxxxx
```

---

## Monitoring Logs

### Watch Worker Logs for Tier Detection

```bash
# Watch all workers
docker-compose logs -f truthsnap-worker

# Watch specific worker
docker-compose logs -f truthsnap-worker-1

# Filter for tier detection
docker-compose logs -f truthsnap-worker | grep "user_tier"
```

**Expected log output**:
```
[Worker] ⏱️  STAGE 5/6: Sent result to Telegram in 316ms | user_tier=pro
```

---

### Watch FraudLens API for Fraud Score

```bash
docker-compose logs -f fraudlens-api | grep "HIGH FRAUD SCORE"
```

**Expected log output**:
```
[Verdict] 🚨 HIGH FRAUD SCORE: 90 → ai_generated @ 90.00%
[Verdict] 🚨 HIGH FRAUD SCORE: 100 → ai_generated @ 98.00%
```

---

## Database Queries

### Check User Tier

```sql
SELECT id, username, first_name, subscription_tier, created_at
FROM users
ORDER BY created_at DESC
LIMIT 10;
```

### Check Recent Analyses

```sql
SELECT
    id,
    user_id,
    verdict,
    confidence,
    created_at
FROM analyses
ORDER BY created_at DESC
LIMIT 10;
```

### Update Multiple Users

```sql
-- Set all users to pro (testing)
UPDATE users SET subscription_tier = 'pro';

-- Reset all to free
UPDATE users SET subscription_tier = 'free';

-- Set specific users to pro
UPDATE users SET subscription_tier = 'pro'
WHERE id IN (644554733, 123456789);
```

---

## Troubleshooting

### Issue: Message Still Shows Free Format for Pro User

**Check 1**: Verify tier in database
```bash
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "SELECT id, subscription_tier FROM users WHERE id = YOUR_ID;"
```

**Check 2**: Check worker logs for tier detection
```bash
docker-compose logs truthsnap-worker | grep "user_tier"
```

**Fix**: Restart workers after tier update
```bash
docker-compose restart truthsnap-worker
```

---

### Issue: Pro Message Missing DIGITAL FOOTPRINT

**Check**: Verify FraudLens returns metadata
```bash
docker-compose logs fraudlens-api | grep "Metadata:"
```

**Possible Causes**:
1. Photo uploaded as compressed photo (not document)
2. EXIF stripped by Telegram
3. Photo has no EXIF data

**Solution**: Upload photo as **document** (not photo) to preserve EXIF

---

### Issue: RED FLAGS Section Empty

**Check**: Verify fraud score
```bash
docker-compose logs fraudlens-api | grep "Validation: score"
```

**Expected**: For AI images, fraud score should be 80-100

**Note**: Real photos with low fraud scores won't show RED FLAGS (this is correct behavior)

---

## Expected Confidence Levels

| Image Type | Fraud Score | Confidence | Verdict |
|------------|-------------|------------|---------|
| Gemini AI (PNG, no EXIF) | 90-100 | 90-98% | ai_generated |
| Photoshop AI | 75-90 | 75-95% | ai_generated |
| Screenshot | 40-80 | 60-80% | manipulated |
| Real Camera Photo | 0-30 | 70-90% | real |
| Stock Photo | 50-70 | 70-85% | real |

---

## Performance Benchmarks

**Free User**:
- Message generation: ~10ms
- Total time: 1-2s (includes FraudLens API)

**Pro User**:
- Message generation: ~15-20ms (more data processing)
- Total time: 1-2s (same FraudLens API time)

**Overhead**: Pro format adds only ~5-10ms vs Free format

---

## Reset Testing Environment

```bash
# 1. Reset all users to free
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "UPDATE users SET subscription_tier = 'free';"

# 2. Clear recent analyses (optional)
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "DELETE FROM analyses WHERE created_at < NOW() - INTERVAL '1 hour';"

# 3. Restart all services
docker-compose restart
```

---

## Quick Commands Reference

```bash
# Set user to pro
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "UPDATE users SET subscription_tier = 'pro' WHERE id = 644554733;"

# Set user to free
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "UPDATE users SET subscription_tier = 'free' WHERE id = 644554733;"

# Check user tier
docker-compose exec postgres psql -U truthsnap -d truthsnap -c "SELECT id, username, subscription_tier FROM users WHERE id = 644554733;"

# Watch worker logs
docker-compose logs -f truthsnap-worker | grep "user_tier\|STAGE 5"

# Watch fraud scores
docker-compose logs -f fraudlens-api | grep "HIGH FRAUD SCORE"

# Restart workers
docker-compose restart truthsnap-worker
```

---

**Status**: ✅ Ready for testing (2026-01-16)

**Current User**: ID 644554733 (rusmishyn) → **pro tier**

Now send a photo to the bot and check the enhanced message format! 🚀
