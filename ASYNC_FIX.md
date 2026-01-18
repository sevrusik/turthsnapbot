# 🔧 Async Event Loop Fix

## Problem

**Error**:
```
RuntimeError: Event loop is closed
asyncpg.exceptions._base.InterfaceError: cannot perform operation: another operation is in progress
```

**Root Cause**: Multiple `asyncio.run()` calls in a single synchronous function

---

## Background

In RQ worker tasks (synchronous functions), each `asyncio.run()` call:
1. Creates a new event loop
2. Runs the async function
3. **Closes the event loop**

When you call `asyncio.run()` multiple times, the second call tries to use the already-closed event loop from the first call, causing the error.

---

## The Issue

**Original code in `tasks.py`**:
```python
# Multiple asyncio.run() calls in one function
def analyze_photo_task(...):
    # Call 1: Download from S3
    photo_bytes = asyncio.run(s3.download(photo_s3_key))  # Creates + closes loop

    # Call 2: Call FraudLens API
    result = asyncio.run(fraudlens.verify_photo(...))     # Creates + closes loop

    # Call 3: Save to DB
    analysis_id = asyncio.run(analysis_repo.create_analysis(...))  # Creates + closes loop

    # Call 4: Get user tier (NEW - caused the error!)
    user = asyncio.run(user_repo.get_user(user_id))       # ❌ FAILS - event loop conflict!
```

**Error occurred at Call 4** because PostgreSQL connection pool was still in use from Call 3.

---

## Solution

**Combine multiple async operations into a single `asyncio.run()` call**

### Before (Broken):
```python
# STAGE 4: Save to DB
analysis_id = asyncio.run(
    analysis_repo.create_analysis(...)
)

# Get user tier (separate asyncio.run - FAILS!)
user = asyncio.run(user_repo.get_user(user_id))
user_tier = user.get('subscription_tier', 'free') if user else 'free'
```

### After (Fixed):
```python
# STAGE 4: Save to DB + get user tier (combined async operation)
async def save_and_get_tier():
    from database.repositories.user_repo import UserRepository

    # Create analysis
    analysis_repo = AnalysisRepository()
    analysis_id = await analysis_repo.create_analysis(...)

    # Get user tier
    user_repo = UserRepository()
    user = await user_repo.get_user(user_id)
    user_tier = user.get('subscription_tier', 'free') if user else 'free'

    return analysis_id, user_tier

# Single asyncio.run() for both operations
analysis_id, user_tier = asyncio.run(save_and_get_tier())
```

---

## Key Principles

### ✅ DO:
1. **Combine async operations** into a single `asyncio.run()` call
2. **Use a wrapper async function** to group related operations
3. **Return multiple values** from the wrapper function

### ❌ DON'T:
1. **Call `asyncio.run()` multiple times** in the same function
2. **Mix event loops** - one `asyncio.run()` per synchronous context
3. **Reuse closed connections** from previous async calls

---

## Pattern: Multiple Async Operations in Sync Context

```python
# ❌ WRONG - Multiple event loops
def sync_function():
    result1 = asyncio.run(async_func1())  # Loop 1: create → close
    result2 = asyncio.run(async_func2())  # Loop 2: FAIL - previous loop closed!

# ✅ CORRECT - Single event loop
def sync_function():
    async def combined():
        result1 = await async_func1()
        result2 = await async_func2()
        return result1, result2

    result1, result2 = asyncio.run(combined())
```

---

## Why This Happens in RQ Workers

**RQ workers run tasks synchronously**, so:
- Worker calls `analyze_photo_task()` (sync function)
- Inside, we need async operations (DB, API calls)
- Solution: Use `asyncio.run()` to bridge sync → async

**But**: `asyncio.run()` is designed for **single entry point** per program
- CLI scripts: One `asyncio.run(main())` at the end
- Web servers: Event loop runs continuously
- **RQ workers**: Each task needs its own event loop context

---

## Impact of Fix

**Before**:
- ❌ Worker crashed with `RuntimeError: Event loop is closed`
- ❌ User received error message instead of analysis result
- ❌ Analysis saved to DB, but notification failed

**After**:
- ✅ Worker completes successfully
- ✅ User receives analysis with correct tier-based message
- ✅ Both DB operations (save analysis + get tier) work together

---

## Testing the Fix

```bash
# 1. Restart workers
docker-compose restart truthsnap-worker

# 2. Send photo to bot
# Expected: No errors in logs

# 3. Check worker logs
docker-compose logs truthsnap-worker | grep "STAGE 4"

# Expected output:
# [Worker] ⏱️  STAGE 4/6: Saved analysis to DB in 25ms | analysis_id=ANL-... | user_tier=pro
```

---

## Related Files

- **Fixed**: `/truthsnap-bot/app/workers/tasks.py` (lines 98-127)
- **Pattern used**: Wrapper async function + single `asyncio.run()`

---

## Lessons Learned

1. **Event loops are expensive** - don't create multiple per task
2. **Group related async operations** into single context
3. **PostgreSQL connections** are tied to event loops
4. **Test with multiple async DB calls** to catch this issue

---

**Status**: ✅ Fixed (2026-01-16)

**Commit message**:
```
fix: combine DB operations in single async context

- Fixes RuntimeError: Event loop is closed
- Combines create_analysis + get_user in one asyncio.run()
- Prevents asyncpg connection conflicts
```
