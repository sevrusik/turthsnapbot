# 🧪 TruthSnap Bot - Testing Guide

Complete testing checklist for MVP validation.

---

## 🚀 Pre-Testing Setup

### 1. Get Telegram Bot Token
```bash
# On Telegram:
# 1. Open @BotFather
# 2. Send /newbot
# 3. Choose name: "TruthSnap Test Bot"
# 4. Choose username: "truthsnap_test_bot"
# 5. Copy token
```

### 2. Configure Environment
```bash
cp .env.example .env
nano .env  # Add your TELEGRAM_BOT_TOKEN
```

### 3. Start Services
```bash
make start

# Wait 30 seconds for all services to initialize

# Verify all services running:
make status

# Expected output:
# fraudlens-api      running
# truthsnap-bot      running
# truthsnap-worker   running (3 instances)
# redis              running
# minio              running
# rq-dashboard       running
```

---

## ✅ Test Suite 1: Basic Functionality

### Test 1.1: Bot Startup
```
Action: Send /start to bot
Expected:
  ✓ Welcome message appears
  ✓ Contains "Welcome to TruthSnap"
  ✓ Contains usage instructions
  ✓ Bot responds within 2 seconds
```

### Test 1.2: Help Command
```
Action: Send /help
Expected:
  ✓ Help message appears
  ✓ Lists all commands
  ✓ Explains Free vs Pro tiers
```

### Test 1.3: Status Command
```
Action: Send /status
Expected:
  ✓ Shows user plan (FREE)
  ✓ Shows checks remaining (3/3)
  ✓ Shows total checks (0)
```

---

## 📸 Test Suite 2: Photo Analysis (Free User)

### Test 2.1: First Photo Upload
```
Action: Upload any photo
Expected:
  ✓ Bot responds: "Your photo is in the queue!"
  ✓ Shows job ID
  ✓ After 20-30 seconds: Analysis result arrives
  ✓ Result contains:
    - Verdict (REAL/AI-GENERATED/MANIPULATED/INCONCLUSIVE)
    - Confidence percentage
    - Analysis time
  ✓ Send /status → Shows 2/3 checks remaining
```

### Test 2.2: Second Photo Upload
```
Action: Upload another photo
Expected:
  ✓ Same flow as Test 2.1
  ✓ Send /status → Shows 1/3 checks remaining
```

### Test 2.3: Third Photo Upload
```
Action: Upload third photo
Expected:
  ✓ Same flow as Test 2.1
  ✓ Send /status → Shows 0/3 checks remaining
```

### Test 2.4: Rate Limit Check
```
Action: Upload fourth photo (same day)
Expected:
  ✓ Bot responds: "Daily limit reached"
  ✓ Shows upgrade CTA
  ✓ Photo NOT analyzed
```

---

## ⚡ Test Suite 3: Rate Limiting

### Test 3.1: Message Spam Protection
```
Action: Send 10 text messages rapidly (< 10 seconds)
Expected:
  ✓ After 5 messages: "Too many requests"
  ✓ Bot stops responding temporarily
  ✓ After 1 minute: Bot responds normally again
```

---

## 🔒 Test Suite 4: Security

### Test 4.1: Adversarial Protection
```
Action: Upload same photo 5 times in a row
Expected:
  ✓ First upload: Works normally
  ✓ After 5th upload: "Suspicious Activity Detected"
  ✓ Account flagged warning
```

### Test 4.2: Invalid File Upload
```
Action: Send a PDF file
Expected:
  ✓ Bot responds: "Please send photos as photos, not as files"
  ✓ Helpful instructions shown
```

### Test 4.3: Oversized Photo
```
Action: Upload 25MB photo (>20MB limit)
Expected:
  ✓ Bot responds: "Photo too large"
  ✓ Shows maximum size limit
```

---

## 💎 Test Suite 5: Subscription Flow

### Test 5.1: View Subscription Options
```
Action: Send /subscribe
Expected:
  ✓ Shows Pro features list
  ✓ Shows pricing ($9.99/mo)
  ✓ Shows buttons:
    - Subscribe Pro
    - Pay per use
    - Cancel
```

### Test 5.2: Click Subscribe Pro
```
Action: Click "Subscribe Pro" button
Expected:
  ✓ Shows: "Payment integration coming soon"
  ✓ Shows support contact
  ✓ Shows user ID for manual upgrade
```

### Test 5.3: Manual Pro Upgrade (Dev Test)
```
Action: Manually upgrade user in code:
  # In user_repo.py, add:
  # user['subscription_tier'] = 'pro'

Then:
  1. Send /status
  2. Upload 5 photos

Expected:
  ✓ /status shows "Plan: PRO"
  ✓ /status shows "Checks today: Unlimited"
  ✓ All 5 photos analyzed successfully
  ✓ No rate limit hit
```

---

## 🔧 Test Suite 6: Error Handling

### Test 6.1: API Down
```
Action:
  1. Stop FraudLens API: docker-compose stop fraudlens-api
  2. Upload photo

Expected:
  ✓ Photo queued successfully
  ✓ Worker attempts analysis
  ✓ After timeout: Error message sent to user
  ✓ Error logged in worker logs
```

### Test 6.2: Redis Down
```
Action:
  1. Stop Redis: docker-compose stop redis
  2. Upload photo

Expected:
  ✓ Bot fails to queue job
  ✓ User sees: "Upload failed. Please try again."
```

### Test 6.3: MinIO Down
```
Action:
  1. Stop MinIO: docker-compose stop minio
  2. Upload photo

Expected:
  ✓ Upload fails
  ✓ User sees error message
```

---

## 📊 Test Suite 7: Monitoring

### Test 7.1: RQ Dashboard
```
Action:
  1. Open http://localhost:9181
  2. Upload 3 photos

Expected:
  ✓ Dashboard accessible
  ✓ Shows 3 jobs in "Finished" tab
  ✓ Shows worker count (3)
  ✓ Shows queue names (high, default, low)
```

### Test 7.2: MinIO Console
```
Action:
  1. Open http://localhost:9001
  2. Login: minioadmin / minioadmin
  3. Check buckets

Expected:
  ✓ Console accessible
  ✓ Bucket "truthsnap-photos" exists
  ✓ After analysis: Photos deleted (privacy)
```

---

## 🚀 Test Suite 8: Performance

### Test 8.1: Analysis Speed
```
Action: Upload 5 photos, measure time
Expected:
  ✓ Free users: 20-30 seconds per photo
  ✓ Pro users: 10-15 seconds per photo (priority queue)
```

### Test 8.2: Concurrent Users
```
Action: Simulate 10 users uploading simultaneously
Expected:
  ✓ All photos queued successfully
  ✓ Workers process in parallel (3 workers)
  ✓ All results delivered within 2 minutes
```

---

## 📝 Test Suite 9: API Direct Testing

### Test 9.1: Health Check
```bash
curl http://localhost:8000/api/v1/health

Expected: {"status": "healthy"}
```

### Test 9.2: Consumer Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/consumer/verify \
  -F "image=@test_photo.jpg" \
  -F "detail_level=basic"

Expected:
  {
    "verdict": "real|ai_generated|manipulated|inconclusive",
    "confidence": 0.0-1.0,
    "watermark_detected": false,
    "processing_time_ms": <number>
  }
```

---

## ✅ Test Results Checklist

Mark each test as you complete it:

**Basic Functionality**
- [ ] Test 1.1: Bot Startup
- [ ] Test 1.2: Help Command
- [ ] Test 1.3: Status Command

**Photo Analysis**
- [ ] Test 2.1: First Photo Upload
- [ ] Test 2.2: Second Photo Upload
- [ ] Test 2.3: Third Photo Upload
- [ ] Test 2.4: Rate Limit Check

**Rate Limiting**
- [ ] Test 3.1: Message Spam Protection

**Security**
- [ ] Test 4.1: Adversarial Protection
- [ ] Test 4.2: Invalid File Upload
- [ ] Test 4.3: Oversized Photo

**Subscription**
- [ ] Test 5.1: View Options
- [ ] Test 5.2: Click Subscribe
- [ ] Test 5.3: Pro Upgrade

**Error Handling**
- [ ] Test 6.1: API Down
- [ ] Test 6.2: Redis Down
- [ ] Test 6.3: MinIO Down

**Monitoring**
- [ ] Test 7.1: RQ Dashboard
- [ ] Test 7.2: MinIO Console

**Performance**
- [ ] Test 8.1: Analysis Speed
- [ ] Test 8.2: Concurrent Users

**API Direct**
- [ ] Test 9.1: Health Check
- [ ] Test 9.2: Consumer Endpoint

---

## 🐛 Common Issues & Solutions

### Issue: Bot not responding
```bash
# Check logs
docker-compose logs truthsnap-bot

# Restart bot
docker-compose restart truthsnap-bot
```

### Issue: Workers not processing
```bash
# Check RQ Dashboard
open http://localhost:9181

# Check worker logs
docker-compose logs truthsnap-worker

# Restart workers
docker-compose restart truthsnap-worker
```

### Issue: "Connection refused" errors
```bash
# Check all services running
docker-compose ps

# Restart all
docker-compose restart
```

---

## 📊 Test Report Template

After completing tests, document results:

```
# TruthSnap Bot - Test Report

Date: _____________
Tester: _____________
Bot Token: _____________

## Summary
- Tests Passed: __/27
- Tests Failed: __/27
- Critical Issues: __
- Minor Issues: __

## Failed Tests
1. Test X.X: [Name]
   - Error: [Description]
   - Logs: [Paste relevant logs]
   - Fix: [Proposed solution]

## Performance Metrics
- Avg analysis time (free): __ seconds
- Avg analysis time (pro): __ seconds
- Max concurrent users tested: __
- System uptime during tests: __%

## Recommendations
- [ ] Ready for beta
- [ ] Needs fixes before beta
- [ ] Critical issues found

## Notes
[Additional observations]
```

---

## ✅ Sign-Off Criteria

Bot is ready for beta when:
- [ ] All 27 tests pass
- [ ] No critical bugs
- [ ] Average analysis < 30 seconds
- [ ] Uptime > 99% during testing
- [ ] Documentation complete
- [ ] Monitoring working

---

**Happy Testing! 🚀**
