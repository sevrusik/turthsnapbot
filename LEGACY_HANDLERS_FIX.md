# Legacy Handlers Fix - /start Issue

## Problem

After implementing scenario-based flow, `/start` command was still showing:
```
📸 Please send the blackmail photo.

💡 Send as FILE for best results (preserves metadata)
```

Even after multiple `/start` commands, the bot remained stuck in old state.

## Root Cause

**Old handlers in `photo.py` were still active:**

```python
# OLD: These handlers listened to AnalysisStates.waiting_for_photo
@router.message(F.photo, AnalysisStates.waiting_for_photo)
async def handle_photo(...)

@router.message(F.document, AnalysisStates.waiting_for_photo)
async def handle_document(...)

@router.message(AnalysisStates.waiting_for_photo)
async def handle_other(...)
```

**Problem:** When user somehow got into `AnalysisStates.waiting_for_photo` state, they couldn't escape because:
1. `/start` set new state (`ScenarioStates.selecting_scenario`)
2. But `handle_other` handler caught ALL messages in old state
3. It showed "Please send photo" message
4. User was stuck in loop

## Solution

### 1. Clear State in /start Handler

**File:** `bot/handlers/start.py:44`

```python
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # ...

    # Clear any existing state first
    await state.clear()

    # Welcome message with scenario selection
    await message.answer(...)

    # Set scenario selection state
    await state.set_state(ScenarioStates.selecting_scenario)
```

**Why:** Ensures old state is completely wiped before setting new one.

### 2. Convert Legacy Handlers to Redirects

**File:** `bot/handlers/photo.py`

**Changed all three legacy handlers:**

#### 2a. Photo Handler (line 26)

```python
@router.message(F.photo, AnalysisStates.waiting_for_photo)
async def handle_photo(message: Message, state: FSMContext):
    """LEGACY HANDLER - Redirects to scenario selection"""

    # Redirect to scenario selection
    await state.clear()

    await message.answer(
        "👋 Welcome to TruthSnap\n\n"
        "Please choose your scenario first:",
        reply_markup=get_scenario_selection_keyboard()
    )

    await state.set_state(ScenarioStates.selecting_scenario)
    return

    # OLD CODE BELOW (never executed)
```

#### 2b. Document Handler (line 193)

```python
@router.message(F.document, AnalysisStates.waiting_for_photo)
async def handle_document(message: Message, state: FSMContext):
    """LEGACY HANDLER - Redirects to scenario selection"""

    # Redirect to scenario selection
    await state.clear()

    await message.answer(
        "👋 Welcome to TruthSnap\n\n"
        "Please choose your scenario first:",
        reply_markup=get_scenario_selection_keyboard()
    )

    await state.set_state(ScenarioStates.selecting_scenario)
    return
```

#### 2c. Text Handler (line 313)

```python
@router.message(AnalysisStates.waiting_for_photo)
async def handle_other(message: Message, state: FSMContext):
    """LEGACY HANDLER - Redirects to scenario selection"""

    # Redirect to scenario selection
    await state.clear()

    await message.answer(
        "👋 Welcome to TruthSnap\n\n"
        "Please choose your scenario:",
        reply_markup=get_scenario_selection_keyboard()
    )

    await state.set_state(ScenarioStates.selecting_scenario)
```

## Why Not Delete Legacy Handlers?

**Reason:** Backward compatibility and safety

- Users might have old state in Redis from previous sessions
- Deleting handlers would cause unhandled message errors
- Redirecting is safer - gracefully guides users to new flow

**Old code is kept below `return` statement for reference:**
```python
async def handle_photo(...):
    # Redirect logic
    return

    # OLD CODE BELOW (kept for reference, never executed)
    user_id = message.from_user.id
    ...
```

## Testing

### Test 1: /start from clean state

```
User: /start
Bot: [Shows scenario selection with buttons]
✅ PASS
```

### Test 2: /start from stuck state

```
# Simulate old state in Redis
User: /start
Bot: [Clears state, shows scenario selection]
✅ PASS
```

### Test 3: Photo upload in legacy state

```
# User somehow in AnalysisStates.waiting_for_photo
User: [Uploads photo]
Bot: "👋 Welcome to TruthSnap\n\nPlease choose your scenario first:"
Bot: [Shows scenario selection buttons]
✅ PASS
```

### Test 4: Multiple /start commands

```
User: /start
User: /start
User: /start
Bot: [Each time shows scenario selection, no stuck state]
✅ PASS
```

## User Flow After Fix

### Before:
```
/start → Stuck in legacy state → "Please send photo" → Can't escape
```

### After:
```
/start → State cleared → Scenario selection → Choose scenario → Upload photo
```

**OR if in legacy state:**
```
[Old state] → Upload photo → Redirected to scenario selection → Choose scenario
```

## Files Changed

| File | Lines | Change |
|------|-------|--------|
| `bot/handlers/start.py` | 44 | Added `await state.clear()` |
| `bot/handlers/photo.py` | 26-51 | Converted `handle_photo` to redirect |
| `bot/handlers/photo.py` | 193-217 | Converted `handle_document` to redirect |
| `bot/handlers/photo.py` | 313-335 | Converted `handle_other` to redirect |

## Deployment

```bash
# Restart bot
docker-compose restart truthsnap-bot

# No worker restart needed (no task changes)
```

## Success Criteria

✅ `/start` always shows scenario selection (never stuck state)
✅ Legacy state handlers redirect to scenario selection
✅ Old code preserved for reference (below `return`)
✅ No unhandled message errors

## Rollback Plan

If issues occur:

```bash
# Revert changes
git checkout HEAD^ -- bot/handlers/start.py bot/handlers/photo.py

# Restart
docker-compose restart truthsnap-bot
```

## Summary

**Problem:** Users stuck in legacy `AnalysisStates.waiting_for_photo` state

**Root cause:** Old handlers in `photo.py` still active

**Solution:**
1. Clear state in `/start` handler
2. Convert legacy handlers to redirects
3. Preserve old code for reference

**Result:** No more stuck states, graceful migration to scenario-based flow

✅ **Status:** Ready for deployment
