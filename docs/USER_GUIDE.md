# 📱 TruthSnap Bot - User Guide

**Instant AI Image Detection in Telegram**

Verify if photos are real or AI-generated in seconds. Fight deepfake blackmail and revenge porn with cutting-edge detection technology.

---

## 🚀 Getting Started

### Step 1: Find the Bot

1. Open Telegram
2. Search for `@TruthSnapBot` (or your custom bot name)
3. Click "START"

### Step 2: Choose Your Scenario

After `/start`, you'll see two scenarios:

**👤 I'm being blackmailed** - For adults facing blackmail with alleged intimate photos
- Professional, legal-focused approach
- Forensic evidence and PDF reports
- Counter-measures and response templates

**🆘 I need help (Teenager)** - For teenagers facing sextortion
- Empathetic, supportive approach
- How to tell parents
- Emergency protection resources

### Step 3: Send Your Photo

1. Tap the 📎 attachment button
2. Select "Photo" (not "File")
3. Choose the suspicious photo
4. Send it!

### Step 4: Get Results

Wait 20-30 seconds. You'll receive:
- ✅ **Verdict**: Real, AI-Generated, Manipulated, or Inconclusive
- 📊 **Confidence**: How certain the analysis is (0-100%)
- ⏱️ **Analysis Time**: How long it took
- 📄 **PDF Report**: Legal-grade forensic evidence
- 🛡️ **Next Actions**: Scenario-specific guidance

---

## 💡 How to Use

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/help` | Show all commands and features |
| `/status` | Check your plan and remaining checks |
| `/subscribe` | Upgrade to Pro for unlimited checks |
| `/cancel` | Cancel current operation |

### Sending Photos

**✅ Correct Way:**
- Use the photo attachment button
- Send as photo (not file)
- One photo at a time

**❌ Incorrect Way:**
- Don't send as document/file
- Don't send multiple photos at once
- Don't send videos (coming soon)

---

## 🎯 Understanding Results

### Verdict Types

#### ✅ **REAL**
Your photo appears to be a genuine photograph taken with a camera.

**What it means:**
- Natural compression artifacts detected
- Authentic EXIF metadata
- No AI generation signs

**Example message:**
```
✅ VERDICT: REAL

This photo appears to be a genuine photograph.

Confidence: 94%
Analysis time: 2.8s
```

#### 🤖 **AI-GENERATED**
Your photo was likely created by AI (Midjourney, DALL-E, Stable Diffusion, etc.)

**What it means:**
- Missing camera metadata
- Unusual frequency patterns
- Characteristic AI fingerprints

**Example message:**
```
🤖 VERDICT: AI-GENERATED

This image shows signs of AI generation.

Red flags:
- Missing JPEG compression artifacts
- Unnatural high-frequency patterns
- Suspicious metadata

Confidence: 87%
Analysis time: 3.2s
```

#### ⚠️ **MANIPULATED**
A real photo that has been digitally edited or altered.

**What it means:**
- Photo was genuine but modified
- May include:
  - Photoshop edits
  - Face swaps
  - Object removal
  - Color adjustments

**Example message:**
```
⚠️ VERDICT: MANIPULATED

This photo has been digitally altered.

Detected:
- Editing software traces
- Inconsistent compression
- Modified metadata

Confidence: 76%
Analysis time: 3.5s
```

#### ❓ **INCONCLUSIVE**
Cannot determine with confidence.

**What it means:**
- Image quality too low
- Heavily compressed
- Unusual format
- Need more analysis

**Example message:**
```
❓ VERDICT: INCONCLUSIVE

Unable to determine with confidence.

Reasons:
- Image quality insufficient
- Conflicting indicators

Try:
- Higher resolution image
- Less compressed version

Confidence: 45%
```

---

## 💎 Subscription Plans

### 🆓 FREE Plan

**Includes:**
- ✅ 3 checks per day
- ✅ Basic verdict & confidence
- ✅ 20-30 second processing
- ✅ Standard queue

**Daily Reset:**
- Resets every 24 hours at midnight UTC
- Check `/status` to see remaining checks

### 👑 PRO Plan - $9.99/month

**Everything in Free, plus:**
- ✅ **Unlimited checks**
- ✅ **Detailed forensic reports**
- ✅ **Priority processing** (10-15 seconds)
- ✅ **PDF downloads**
- ✅ **Detection layer breakdown**
- ✅ **Priority support**

**To upgrade:**
1. Send `/subscribe`
2. Click "Subscribe Pro"
3. Complete payment
4. Instant activation!

---

## 🔒 Privacy & Security

### Your Privacy Matters

**We automatically:**
- ✅ Delete photos after analysis
- ✅ Don't store images permanently
- ✅ Encrypt all data in transit
- ✅ Don't share your data

**You control:**
- Your account data
- Analysis history
- Subscription status

### GDPR Compliant

- Right to access your data
- Right to delete your data
- Right to data portability
- Contact: privacy@truthsnap.ai

---

## 🛡️ Best Practices

### For Best Results

**DO:**
- ✅ Use high-quality images
- ✅ Upload original files (not screenshots)
- ✅ Wait for each analysis to complete
- ✅ Check suspicious photos from unknown sources

**DON'T:**
- ❌ Send heavily compressed images
- ❌ Upload the same photo repeatedly
- ❌ Spam the bot (rate limited to 5 messages/minute)
- ❌ Send personal/private photos you don't own

### Fighting Deepfake Blackmail

If you're a victim of deepfake blackmail:

1. **Don't panic** - AI-generated images can be proven fake
2. **Choose your scenario** - Adult or Teenager flow
3. **Upload the photo** - Get forensic proof
4. **Download PDF report** - Legal-grade evidence
5. **Use counter-measures**:
   - Safe Response Templates (don't engage emotionally)
   - Report to StopNCII (prevent online spread)
   - Report to FBI IC3 (US) or local authorities
6. **Never pay** - Payment increases demands

**For Teenagers:**
- Use "How to tell my parents" guide
- Show them the PDF report as proof
- Use Take It Down to prevent spread
- Report to NCMEC CyberTipline

**Emergency contacts:**
- **FBI IC3**: https://www.ic3.gov
- **StopNCII**: https://stopncii.org
- **NCMEC (under 18)**: https://report.cybertip.org
- **Support**: support@truthsnap.ai (24/7)

---

## ❓ FAQ

### Q: How accurate is the detection?
**A:** 95%+ accuracy on our test dataset. Combines multiple detection methods including FFT analysis, metadata validation, and AI fingerprinting.

### Q: What image formats are supported?
**A:** JPEG, PNG, WebP. Maximum size: 20MB.

### Q: How long does analysis take?
**A:**
- Free users: 20-30 seconds
- Pro users: 10-15 seconds (priority queue)

### Q: Can I analyze videos?
**A:** Coming soon! Currently photo-only.

### Q: What if I run out of daily checks?
**A:**
- Wait until midnight UTC for reset
- OR upgrade to Pro for unlimited

### Q: Can I get a refund?
**A:** Yes, 30-day money-back guarantee. Contact support@truthsnap.ai

### Q: Is my data safe?
**A:** Yes! Photos are deleted immediately after analysis. We're GDPR compliant.

### Q: Can I use this for commercial purposes?
**A:** Pro plan includes commercial use. Enterprise plans available for high volume.

### Q: What AI models can you detect?
**A:**
- Midjourney
- DALL-E 2/3
- Stable Diffusion
- Firefly
- And many more...

### Q: How do I cancel my subscription?
**A:** Send `/cancel` anytime. No questions asked.

### Q: What's the difference between the two scenarios?
**A:**
- **Adult Blackmail**: Professional, legal-focused. Includes forensic reports, counter-measures, and response templates.
- **Teenager SOS**: Empathetic, supportive. Includes parent communication scripts, Take It Down service, and educational resources.

### Q: Can I switch between scenarios?
**A:** Yes! Click "🔙 Back to Main Menu" anytime to return to scenario selection.

### Q: What is "Safe Response Generator"?
**A:** AI-crafted response templates that cite your forensic evidence and legal rights. Use these to respond to blackmailers ONCE, then block them. Never engage in conversation.

### Q: What is "Take It Down"?
**A:** A free, anonymous service by NCMEC that removes intimate images from major platforms (Facebook, Instagram, TikTok, Snapchat, etc.) without requiring you to file a police report.

### Q: Is the PDF report legally valid?
**A:** The PDF includes:
- SHA-256 hash (cryptographic proof)
- Report ID with timestamp
- Forensic analysis details
- Official disclaimer

While acceptable as supporting evidence, it's not a certified legal document. Consult with law enforcement or legal counsel.

---

## 🐛 Troubleshooting

### "Daily limit reached"
**Problem:** Used all 3 free checks today

**Solution:**
- Wait until midnight UTC
- OR upgrade to Pro (`/subscribe`)

### "Too many requests"
**Problem:** Sending messages too quickly (>5/minute)

**Solution:**
- Wait 1 minute
- Don't spam the bot

### "Upload failed"
**Problem:** Photo couldn't be uploaded

**Solutions:**
- Check internet connection
- Try smaller file (<20MB)
- Send as photo, not file
- Restart Telegram

### "Analysis failed"
**Problem:** Processing error occurred

**Solutions:**
- Try different photo
- Wait a few minutes and retry
- Contact support if persists

### Bot not responding
**Problem:** No reply from bot

**Solutions:**
- Check bot is not blocked
- Try `/start` command
- Check @TruthSnapStatus for outages
- Contact support

---

## 📞 Support

### Get Help

**In-App:**
- Send `/help` for quick help
- Send `/status` to check account

**Contact:**
- Email: support@truthsnap.ai
- Telegram: @TruthSnapSupport
- Twitter: @TruthSnapBot
- Status Page: status.truthsnap.ai

**Response Times:**
- Free users: 24-48 hours
- Pro users: 4-8 hours
- Enterprise: 1 hour

### Report a Bug

1. Send `/help`
2. Click "Report Bug"
3. Describe the issue
4. Include screenshot if possible

---

## 🎓 Learn More

### Resources

- **Blog**: blog.truthsnap.ai
  - How AI detection works
  - Fighting deepfakes
  - Privacy guides

- **Video Tutorials**: youtube.com/@truthsnap
  - Getting started
  - Understanding results
  - Advanced tips

- **Community**: t.me/TruthSnapCommunity
  - User discussions
  - Tips & tricks
  - Latest updates

### About AI Detection

**How it works:**
1. **FFT Analysis** - Analyzes frequency patterns (31.5 images/second!)
2. **Metadata Validation** - Checks EXIF data for inconsistencies
3. **Watermark Detection** - Looks for SynthID, C2PA, Meta watermarks
4. **Ensemble Voting** - Combines multiple detectors for accuracy

**Limitations:**
- Very high-quality AI images can fool detection
- Heavy compression reduces accuracy
- Screenshots may be inconclusive

---

## 🔄 Updates

### Latest Version: 1.0.0 (January 2026)

**New:**
- ✅ Initial release
- ✅ FFT detection (177x optimized)
- ✅ Free & Pro tiers
- ✅ Metadata analysis

**Coming Soon:**
- 🔜 Video analysis
- 🔜 Batch processing
- 🔜 Browser extension
- 🔜 Mobile app

**Follow updates:**
- Telegram: @TruthSnapNews
- Twitter: @TruthSnapBot

---

## 📜 Terms & Privacy

By using TruthSnap, you agree to:
- [Terms of Service](https://truthsnap.ai/terms)
- [Privacy Policy](https://truthsnap.ai/privacy)
- [Acceptable Use Policy](https://truthsnap.ai/acceptable-use)

**Key points:**
- Photos deleted after analysis
- No permanent storage
- GDPR compliant
- Commercial use allowed (Pro+)

---

**Thank you for using TruthSnap! Together we fight deepfakes. 💪**

*Questions? support@truthsnap.ai*
