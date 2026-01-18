# Scenario Flow Testing Guide

## Changes Made

### 1. Scenario Context Propagation

**Flow:**
```
User selects scenario → Photo uploaded → Queue job (with scenario) → Worker processes →
Result sent with scenario-specific keyboard → User sees proper buttons
```

**Files Updated:**
- `services/queue.py` - Added `scenario` parameter
- `workers/tasks.py` - Added `scenario` parameter, passes to notifier
- `services/notifications.py` - Scenario-aware keyboards
- `bot/handlers/scenarios.py` - All enqueue calls now pass scenario
- `bot/handlers/parent_support.py` - Fetches latest analysis_id
- `bot/handlers/counter_measures.py` - Fetches latest analysis_id

### 2. Result Keyboards by Scenario

#### Adult Blackmail Result:
```
📄 Get Forensic PDF
🛡️ Counter-measures
🔙 Back to Main Menu
```

#### Teenager SOS Result:
```
📄 Get PDF Report
🤝 How to tell my parents
🚫 Stop the Spread
📚 What is sextortion?
🔙 Back to Main Menu
```

#### Legacy (no scenario):
```
📄 Get PDF Report
📤 Share Result
🔙 Back to Main Menu
```

### 3. Main Menu Return

All results now have `🔙 Back to Main Menu` button that:
- Returns to scenario selection screen
- Clears current state
- Shows welcome message with scenario buttons

---

## Testing Steps

### Test 1: Adult Blackmail Flow

```
1. /start
2. Click "👤 I'm being blackmailed"
3. Upload photo (or send as file)
4. Wait for analysis result
5. Verify buttons appear:
   ✅ 📄 Get Forensic PDF
   ✅ 🛡️ Counter-measures
   ✅ 🔙 Back to Main Menu

6. Click "🛡️ Counter-measures"
7. Verify menu shows:
   ✅ 💬 Generate Safe Response
   ✅ 🚫 Report to StopNCII (link)
   ✅ 🚨 Report to FBI IC3 (link)
   ✅ 📄 Download PDF Report (with analysis_id)

8. Click "💬 Generate Safe Response"
9. Verify 4 templates displayed

10. Click "🔙 Back to Main Menu"
11. Verify scenario selection screen appears
```

### Test 2: Teenager SOS Flow

```
1. /start
2. Click "🆘 I need help (Teenager)"
3. Verify calming message: "Breathe. You are safe."
4. Upload photo
5. Wait for analysis result
6. Verify buttons appear:
   ✅ 📄 Get PDF Report
   ✅ 🤝 How to tell my parents
   ✅ 🚫 Stop the Spread
   ✅ 📚 What is sextortion?
   ✅ 🔙 Back to Main Menu

7. Click "🤝 How to tell my parents"
8. Verify guide shows:
   ✅ Why tell them
   ✅ What to say
   ✅ What evidence to show
   ✅ PDF download button (with analysis_id)

9. Click "💬 See conversation script"
10. Verify step-by-step script

11. Click "🚫 Stop the Spread"
12. Verify Take It Down explanation + links

13. Click "📚 What is sextortion?"
14. Verify educational content

15. Click "🔙 Back to Main Menu"
16. Verify scenario selection screen
```

### Test 3: Legacy Flow (Direct Photo Upload)

```
1. /start
2. Click any scenario, then go back
3. Upload photo directly (without scenario selection)
4. Verify buttons appear:
   ✅ 📄 Get PDF Report
   ✅ 📤 Share Result
   ✅ 🔙 Back to Main Menu

5. Click "🔙 Back to Main Menu"
6. Verify scenario selection appears
```

### Test 4: Main Menu Navigation

```
1. From any result screen, click "🔙 Back to Main Menu"
2. Verify welcome message shows:
   👋 Welcome to TruthSnap
   🛡️ AI Deepfake Detection & Blackmail Protection
   ...
   Choose your scenario:
   [ 👤 I'm being blackmailed ]
   [ 🆘 I need help (Teenager) ]
   [ 📚 Knowledge Base ]

3. Click different scenario
4. Verify correct flow starts
```

### Test 5: PDF Download with Analysis ID

```
1. Complete Adult or Teenager flow
2. Click "📄 Get Forensic PDF" (or "Get PDF Report")
3. Verify PDF generates successfully
4. Check PDF filename includes analysis_id
5. Verify PDF content shows correct verdict

From Counter-measures or Parent Help:
6. Click "📄 Download PDF Report"
7. Verify same PDF is generated
8. Confirm analysis_id matches
```

---

## Expected Behaviors

### Scenario Persistence

✅ **Scenario context is maintained through:**
- Queue job (scenario parameter)
- Worker task (scenario parameter)
- Result notification (scenario parameter)
- Keyboard generation (scenario-aware)

✅ **State is cleared when:**
- User clicks "🔙 Back to Main Menu"
- User sends /start
- User selects new scenario

### Analysis ID Tracking

✅ **Analysis ID is fetched from:**
- Database query (latest analysis for user)
- Used in PDF generation callbacks
- Used in "Tell Parents" keyboard
- Used in "Counter-measures" keyboard

⚠️ **Known limitation:**
- If user has multiple analyses, "latest" is used
- Better approach: Store in FSM state (future enhancement)

### Error Handling

✅ **Graceful fallbacks:**
- If analysis_id not found → Shows "unknown"
- If PDF generation fails → Error message
- If database query fails → Logs error, continues

---

## Common Issues & Fixes

### Issue 1: State Stuck in Scenario

**Symptom:** After analysis, /start shows "Please send photo"

**Fix:** ✅ FIXED - Added "Back to Main Menu" button
- Clears state
- Returns to scenario selection

### Issue 2: Wrong Keyboard After Analysis

**Symptom:** Generic keyboard instead of scenario-specific

**Cause:** Scenario not passed through queue/worker

**Fix:** ✅ FIXED - All scenario handlers now pass `scenario` parameter

### Issue 3: PDF Button Shows "latest"

**Symptom:** PDF filename or callback shows "latest" instead of real ID

**Cause:** Analysis ID not fetched from database

**Fix:** ✅ FIXED - Added database query in parent_support.py and counter_measures.py

---

## Performance Notes

### Database Queries

Each time user clicks "Tell Parents" or "Counter-measures":
```sql
SELECT analysis_id FROM analyses
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 1
```

**Performance:** O(1) with index on (user_id, created_at)

**Optimization (future):**
Store analysis_id in FSM state during analysis:
```python
await state.update_data(
    latest_analysis_id=analysis_id,
    scenario="adult_blackmail"
)
```

---

## Deployment

### 1. Restart Bot

```bash
# If running locally
cd truthsnap-bot
python -m app.bot.main

# If using Docker
docker-compose restart truthsnap-bot
```

### 2. Restart Worker

```bash
# Worker must be restarted to pick up new task signature
docker-compose restart worker

# Or if running locally
cd truthsnap-bot
python -m app.workers.worker
```

### 3. Verify

```bash
# Check logs
docker-compose logs -f truthsnap-bot
docker-compose logs -f worker

# Look for:
[Worker] Enqueued job ... scenario=adult_blackmail
[Worker] Sent result to Telegram ... scenario=adult_blackmail
```

---

## Summary

✅ Scenario context flows: User → Queue → Worker → Notifier → Keyboard
✅ Each scenario gets unique buttons after analysis
✅ "Back to Main Menu" works from all states
✅ Analysis ID properly fetched for PDF downloads
✅ Graceful error handling throughout

**Ready for testing!**
