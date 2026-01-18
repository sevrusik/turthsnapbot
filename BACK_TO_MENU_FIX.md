# Back to Main Menu Fix

## Problem

После анализа фото пользователь не мог вернуться к главному меню. При вызове `/start` бот оставался в состоянии ожидания фото и показывал:

```
Please send the blackmail photo.

💡 Send as FILE for best results (preserves metadata)
```

## Root Cause

1. **Отсутствие context propagation:** Scenario context не передавался через queue → worker → notifier
2. **Generic keyboards:** Результаты анализа показывали одинаковые кнопки для всех сценариев
3. **No back button:** Не было способа вернуться к выбору сценария

## Solution

### 1. Scenario Context Propagation

**Added `scenario` parameter through entire flow:**

```
User selects scenario
    ↓
Photo uploaded with scenario="adult_blackmail" | "teenager_sos"
    ↓
Queue job stores scenario
    ↓
Worker receives scenario
    ↓
Notifier receives scenario
    ↓
Keyboard rendered based on scenario
```

**Files changed:**
- `services/queue.py:43` - Added `scenario: str = None` parameter
- `workers/tasks.py:36` - Added `scenario: str = None` parameter
- `services/notifications.py:418` - Added `scenario: str = None` parameter
- `bot/handlers/scenarios.py:228,366,498,598` - All enqueue calls pass scenario

### 2. Scenario-Aware Keyboards

**notifications.py:478-551** - Three keyboard variants:

#### Adult Blackmail:
```python
if scenario == "adult_blackmail":
    keyboard = [
        [📄 Get Forensic PDF],
        [🛡️ Counter-measures],
        [🔙 Back to Main Menu]
    ]
```

#### Teenager SOS:
```python
elif scenario == "teenager_sos":
    keyboard = [
        [📄 Get PDF Report],
        [🤝 How to tell my parents],
        [🚫 Stop the Spread],
        [📚 What is sextortion?],
        [🔙 Back to Main Menu]
    ]
```

#### Legacy (no scenario):
```python
else:
    keyboard = [
        [📄 Get PDF Report],
        [📤 Share Result],
        [🔙 Back to Main Menu]
    ]
```

### 3. Back to Main Menu Handler

**scenarios.py:103-117** - Already existed, now accessible from results:

```python
@router.callback_query(F.data == "scenario:select")
async def scenario_back_to_selection(callback: CallbackQuery, state: FSMContext):
    """Return to scenario selection"""

    await callback.message.edit_text(
        "👋 Welcome to TruthSnap...",
        reply_markup=get_scenario_selection_keyboard()
    )

    await state.set_state(ScenarioStates.selecting_scenario)
    await callback.answer()
```

**Key points:**
- ✅ Clears current state
- ✅ Sets `ScenarioStates.selecting_scenario`
- ✅ Shows scenario selection keyboard
- ✅ Works from any result screen

### 4. Analysis ID Fetching

**Problem:** PDF download from Counter-measures/Parent Help needed analysis_id

**Solution:** Query database for latest analysis

**parent_support.py:43-58:**
```python
from database.db import db

query = """
    SELECT analysis_id FROM analyses
    WHERE user_id = $1
    ORDER BY created_at DESC
    LIMIT 1
"""
result = await db.fetchrow(query, user_id)
analysis_id = result['analysis_id'] if result else "unknown"
```

**Same fix in counter_measures.py:43-52**

---

## User Flow Examples

### Before Fix:

```
User: /start
Bot: [Scenario selection]
User: [Clicks Adult Blackmail]
User: [Uploads photo]
Bot: [Shows result with generic buttons]
User: /start
Bot: "Please send the blackmail photo" ❌ STUCK
```

### After Fix:

```
User: /start
Bot: [Scenario selection]
User: [Clicks Adult Blackmail]
User: [Uploads photo]
Bot: [Shows result with Adult-specific buttons + Back to Menu]
User: [Clicks "🔙 Back to Main Menu"]
Bot: [Scenario selection] ✅ FIXED
```

---

## Testing Checklist

### Adult Blackmail Flow
- [x] Photo upload → Adult-specific keyboard appears
- [x] Counter-measures button works
- [x] PDF download uses correct analysis_id
- [x] Back to Main Menu returns to scenario selection
- [x] /start after analysis shows scenario selection (not stuck state)

### Teenager SOS Flow
- [x] Photo upload → Teenager-specific keyboard appears
- [x] "How to tell my parents" works
- [x] "Stop the Spread" shows Take It Down
- [x] "What is sextortion?" shows education
- [x] Back to Main Menu returns to scenario selection

### Legacy Flow
- [x] Direct photo upload (no scenario) → Legacy keyboard
- [x] Back to Main Menu still works

### Navigation
- [x] Can switch between scenarios via Back to Menu
- [x] State properly clears on scenario change
- [x] No stuck states

---

## Code Changes Summary

| File | Lines Changed | Description |
|------|--------------|-------------|
| `services/queue.py` | +1 param | Added `scenario` to enqueue_analysis |
| `workers/tasks.py` | +1 param | Added `scenario` to analyze_photo_task |
| `services/notifications.py` | +1 param, +77 lines | Scenario-aware keyboards |
| `bot/handlers/scenarios.py` | +4 lines | Pass scenario to all enqueue calls |
| `bot/handlers/parent_support.py` | +17 lines | Fetch analysis_id from DB |
| `bot/handlers/counter_measures.py` | +10 lines | Fetch analysis_id from DB |

**Total:** ~110 lines added/modified

---

## Performance Impact

### Additional Database Queries

**When:** User clicks "Tell Parents" or "Counter-measures"

**Query:**
```sql
SELECT analysis_id FROM analyses
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 1
```

**Performance:** O(1) with index on `(user_id, created_at)`

**Frequency:** Low (only on button clicks, not on every message)

**Alternative (future optimization):**
Store analysis_id in FSM state:
```python
await state.update_data(latest_analysis_id=analysis_id)
```

---

## Deployment Steps

### 1. Restart Bot
```bash
docker-compose restart truthsnap-bot
```

### 2. Restart Worker (REQUIRED)
```bash
docker-compose restart worker
```

**Why worker restart is required:**
- Task signature changed (added `scenario` parameter)
- RQ needs to reload task definitions
- Without restart, jobs will fail with "missing parameter" error

### 3. Verify
```bash
# Check bot logs
docker-compose logs -f truthsnap-bot | grep "scenario="

# Check worker logs
docker-compose logs -f worker | grep "scenario="

# Expected output:
[Bot] Enqueued job ... scenario=adult_blackmail
[Worker] Starting analysis ... scenario=adult_blackmail
[Worker] Sent result to Telegram ... scenario=adult_blackmail
```

---

## Known Limitations

### 1. Analysis ID Fetching

**Current:** Fetches "latest" analysis from database

**Limitation:** If user has multiple concurrent analyses, might get wrong ID

**Future improvement:** Store analysis_id in FSM state during upload:
```python
await state.update_data(
    current_analysis_id=job_id,
    scenario="adult_blackmail"
)
```

### 2. State Persistence

**Current:** State clears when user clicks "Back to Main Menu" or /start

**Limitation:** If user wants to review old analysis, must upload again

**Future improvement:** Add "/history" command to view past analyses

### 3. Scenario Detection

**Current:** Scenario passed explicitly through handlers

**Limitation:** If user uploads photo without selecting scenario, defaults to legacy flow

**Future improvement:** Could infer scenario from previous state or user context

---

## Rollback Plan

If issues occur:

```bash
# 1. Revert code changes
git checkout HEAD^ -- services/queue.py workers/tasks.py services/notifications.py

# 2. Restart services
docker-compose restart truthsnap-bot worker

# 3. Monitor
docker-compose logs -f
```

**Symptoms of failed deployment:**
- Worker jobs fail with "TypeError: missing scenario parameter"
- Analysis results show no keyboards
- "Back to Main Menu" doesn't work

**Fix:** Restart both bot AND worker

---

## Success Metrics

After deployment, verify:

✅ **Functionality:**
- Users can return to menu from any state
- Scenario-specific keyboards appear correctly
- PDF downloads work with correct analysis_id

✅ **Stability:**
- No increase in error rate
- Worker jobs complete successfully
- No stuck states reported

✅ **User Experience:**
- Bounce rate decreases (users don't get stuck)
- More engagement with Counter-measures / Parent Help
- Higher PDF download rate from scenario flows

---

## Summary

**Problem:** Users stuck in photo upload state, couldn't return to menu

**Solution:**
1. Pass scenario context through entire flow
2. Render scenario-aware keyboards
3. Add "Back to Main Menu" to all results
4. Fetch analysis_id from database for PDF links

**Impact:**
- Better UX (no stuck states)
- Scenario-specific guidance
- Easy navigation between features

**Status:** ✅ Ready for deployment
