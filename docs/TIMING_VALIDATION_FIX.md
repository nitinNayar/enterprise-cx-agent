# Timing Validation Fix - Late Return Detection

**Date:** 2026-02-13
**Issue:** Agent was not detecting late returns (> 30 days), causing holiday gift exceptions to never trigger

---

## Problem Summary

### What Was Broken

**ORD-888 (Jack Ryan, 39 days old, holiday gift):**
- ❌ Agent approved immediately without detecting timing violation
- ❌ Never called `check_vip_status`
- ❌ Never called `check_precedents`
- ❌ Never mentioned holiday gift exception
- ❌ Customer had no transparency about extended 60-day policy

### Root Causes

1. **No Structured Date Data** - Timing info only in free-text `notes` field
2. **No Timing Validation Instructions** - Prompts only checked item category/condition
3. **Exception Protocol Never Triggered** - Agent never detected the late return as a policy violation

---

## Three-Part Solution Implemented

### Fix #1: Add Structured Date Fields (Data Layer)

**File:** `data/mock_orders.json`

**Changes:**
- Added `purchase_date` (ISO format: "YYYY-MM-DD")
- Added `delivered_date` or `shipped_date` (depending on status)
- Added `days_since_purchase` (integer)

**Example - ORD-888:**
```json
"ORD-888": {
  "status": "delivered",
  "items": ["Complete Sherlock Holmes Collection (Leather-bound gift set)"],
  "eligible_for_return": true,
  "customer_id": "CUST-REG-0888",
  "customer_name": "Jack Ryan",
  "purchase_date": "2026-01-05",       ← NEW
  "delivered_date": "2026-01-08",      ← NEW
  "days_since_purchase": 39,           ← NEW (CRITICAL)
  "notes": "Holiday gift purchased in December, now 39 days since purchase"
}
```

**All Orders Updated:**
- ORD-123: 3 days (within window)
- ORD-456: 45 days (outside window, already marked ineligible)
- ORD-777: 19 days (within window, VIP exception case)
- **ORD-888: 39 days** (outside window, holiday exception case)
- ORD-555: 12 days (within window)
- ORD-111: 16 days (within window)
- ORD-222: 8 days (within window)
- ORD-333: 24 days (within window)
- ORD-444: 10 days (within window)
- ORD-666: 5 days (within window, gift card)
- ORD-1001: 6 days (within window, e-book)
- ORD-1234: 26 days (within window, personalized)
- ORD-2001: 2 days (processing)
- ORD-2002: 29 days (pre-order, shipped today)
- ORD-2003: 4 days (processing, special order)

---

### Fix #2: Add Timing Validation to Prompts (Instruction Layer)

**Files Modified:**
- `prompts.py` (lines 215-237)
- `config.py` (lines 21-39)

#### New Section: TIMING VALIDATION (FIRST PRIORITY)

Added immediately after greeting protocol:

```markdown
# TIMING VALIDATION (FIRST PRIORITY)

**IMMEDIATELY after calling `look_up_order`, you MUST:**
1. Extract `days_since_purchase` from the order data
2. Compare to 30-day policy window
3. If `days_since_purchase` > 30:
   - This is a **LATE RETURN** (policy violation detected)
   - Continue with greeting protocol normally
   - After gathering return info, you MUST check VIP status and precedents
   - DO NOT approve without checking for exceptions
```

#### Updated: YOUR PRIME DIRECTIVE

**Before:**
```markdown
2. Even if `eligible_for_return` is TRUE, you **MUST** check the item name against the Policy.
```

**After:**
```markdown
2. Even if `eligible_for_return` is TRUE, you **MUST** validate THREE things:

   a) **TIMING CHECK (MANDATORY):**
      - Extract `days_since_purchase` from the order data
      - IF `days_since_purchase` > 30: This is a **LATE RETURN** (policy violation)
      - You MUST proceed to exception protocol (check VIP status and precedents)
      - DO NOT approve late returns without checking for exceptions

   b) **ITEM CATEGORY CHECK:**
      - Check the item name against the Policy
      - Identify: Digital Products, Personalized Items, Opened Books, etc.

   c) **ITEM CONDITION CHECK:**
      - After customer confirms condition, validate against policy requirements
      - Books must be "unread, resellable condition"
      - Signed editions must be unopened/pristine
```

#### Updated: AUTOMATIC VIP CHECK (MANDATORY)

Added explicit late return trigger:

```markdown
IF the Standard Policy implies a DENIAL, including:
- **Late Return:** `days_since_purchase` > 30              ← ADDED
- **Read Book:** Customer confirmed they read/opened the book
- **Digital Product:** E-books, audiobooks once downloaded
- **Opened Item:** Personalized, used, or damaged by customer

**CRITICAL:** Late returns (`days_since_purchase` > 30) ALWAYS trigger this check
```

---

### Fix #3: Make Timing Check Mandatory (Workflow Layer)

**Files Modified:**
- `prompts.py` (lines 215-216, 238-251)
- `config.py` (lines 21-39)

#### Key Changes:

1. **Timing check is now FIRST PRIORITY** - checked immediately after order lookup
2. **Late returns always trigger exception protocol** - no more silent approvals
3. **Explicit examples** - clarified when `days_since_purchase` > 30 = policy violation
4. **Clear workflow** - late return → check VIP → search precedents → apply exception

---

## Expected Behavior After Fix

### ORD-888 Flow (Late Return → Holiday Exception)

```
1. User: "I want to return ORD-888"

2. Agent: [Calls look_up_order]
   → Receives: days_since_purchase: 39
   → Detects: 39 > 30 = LATE RETURN (policy violation)

3. Agent: [Calls get_customer_info]
   → Jack Ryan (Regular customer, 3 years)

4. Agent: Greets customer with personalized message

5. User: "Don't need it anymore"

6. Agent: "Thank you. And is the gift set in its original condition?"

7. User: "Yes"

8. Agent: [NOW TRIGGERS EXCEPTION PROTOCOL]
   → Calls check_vip_status → NOT VIP
   → Calls check_precedents("holiday gift late december")
   → Finds DEC-2024-002 (Holiday Gift Extension)
   → Validates: December purchase ✓, 39 < 60 days ✓, unread ✓

9. Agent: Provides transparency response:
   "Thank you for confirming. I see this was purchased in December as
   a holiday gift - we extend our return window to 60 days for holiday
   purchases made in November-December since recipients often need extra
   time to evaluate gifts. Your return is well within that timeframe!

   Good news! Your return is approved ✓"
```

### Key Differences

| Before Fix | After Fix |
|-----------|-----------|
| ❌ Timing never checked | ✅ Timing checked immediately |
| ❌ Approved based on `eligible_for_return: true` flag | ✅ Validates timing, category, and condition |
| ❌ Exception protocol never triggered | ✅ Late return triggers exception check |
| ❌ No VIP status check | ✅ Automatic VIP check for late returns |
| ❌ No precedent search | ✅ Searches for holiday exception |
| ❌ Silent approval | ✅ Transparent explanation of exception |

---

## Testing Instructions

### Test Case 1: Late Return with Holiday Exception (ORD-888)

**Expected Behavior:**
1. Agent detects 39 days > 30 days
2. Agent checks VIP status (regular customer)
3. Agent searches precedents with "holiday gift late december"
4. Agent finds DEC-2024-002
5. Agent explains 60-day holiday policy
6. Agent approves with transparency

**Test Script:**
```
User: "I want to return ORD-888"
[Agent should greet Jack Ryan]

User: "Don't need it anymore"
[Agent should ask about condition]

User: "Yes, it's in good condition"
[Agent should:
 - Detect late return (39 days)
 - Check VIP status (regular)
 - Search precedents
 - Find holiday exception
 - Explain 60-day policy
 - Approve with transparency]
```

### Test Case 2: VIP Exception (ORD-777)

**Expected Behavior:**
1. Agent detects item is signed edition
2. Agent confirms customer read it
3. Agent checks VIP status (Platinum VIP)
4. Agent searches precedents with "vip book read signed"
5. Agent finds DEC-2024-001
6. Agent explains VIP exception
7. Agent approves with conditions

**Verification:**
- ORD-777: 19 days (within 30-day window)
- Should trigger exception due to **read signed book**, not timing

### Test Case 3: Regular Return (ORD-555)

**Expected Behavior:**
1. Agent detects 12 days < 30 days ✓
2. Agent confirms item condition
3. Agent approves immediately (no exception needed)

**Verification:**
- No VIP check needed
- No precedent search needed
- Standard approval flow

### Test Case 4: Late Return No Exception (ORD-456)

**Expected Behavior:**
1. Agent detects 45 days > 30 days
2. Agent checks VIP status (regular customer)
3. Agent searches precedents (no holiday context)
4. Agent finds no applicable exceptions
5. Agent politely denies

**Verification:**
- ORD-456 already marked `eligible_for_return: false`
- Should detect timing violation
- Should attempt exception search
- Should deny when no exception found

---

## Log Verification

### Before Fix (What Was Missing)

```
11:58:03 - Agent called 'get_policy_info' with input {'policy_type': 'returns'}
11:58:09 - CYCLE COMPLETE: Sent final response.
```

**Missing:**
- ❌ No timing validation
- ❌ No `check_vip_status` call
- ❌ No `check_precedents` call
- ❌ No detection of 39-day age

### After Fix (Expected Logs)

```
XX:XX:XX - Agent called 'look_up_order' with input {'order_id': 'ORD-888'}
XX:XX:XX - [INTERNAL] Detected days_since_purchase: 39 (> 30 days = late return)
XX:XX:XX - Agent called 'get_customer_info' with input {'customer_id': 'CUST-REG-0888'}
[... customer confirms condition ...]
XX:XX:XX - [INTERNAL] Late return detected, triggering exception protocol
XX:XX:XX - Agent called 'check_vip_status' with input {'customer_id': 'CUST-REG-0888'}
XX:XX:XX - API SUCCESS: Customer CUST-REG-0888 is NOT VIP (regular customer)
XX:XX:XX - Agent called 'check_precedents' with input {'query_tags_str': 'holiday gift late december'}
XX:XX:XX - PRECEDENT CHECK: Found matching precedent DEC-2024-002
XX:XX:XX - [INTERNAL] Holiday exception applies, 60-day window approved
XX:XX:XX - CYCLE COMPLETE: Sent final response with transparency
```

---

## Code Comments

### Data Format Notes

**Date Format:** ISO 8601 ("YYYY-MM-DD")
- Easy to parse
- Human-readable
- Sortable

**days_since_purchase Calculation:**
- Relative to "today" (2026-02-13)
- Pre-calculated for consistency
- Should be updated if mock data "ages"

### Future Considerations

1. **Dynamic Date Calculation:**
   - Consider calculating `days_since_purchase` dynamically from `purchase_date`
   - Would prevent mock data from becoming stale
   - Could add utility function: `calculate_days_since_purchase(purchase_date)`

2. **Additional Date Fields:**
   - `return_window_expires_at`: Pre-calculate expiration date
   - `last_modified`: Track when order data was updated
   - `eligible_until`: Explicit return deadline

3. **Holiday Detection Logic:**
   - Could add `is_holiday_gift: true` boolean flag
   - Would make precedent matching more reliable
   - Consider adding `purchase_month` field for easier filtering

---

## Files Modified Summary

| File | Lines Changed | Type of Change |
|------|--------------|----------------|
| `data/mock_orders.json` | All order entries | Added date fields |
| `prompts.py` | 215-251 | Added timing validation |
| `config.py` | 21-39 | Added timing validation |
| `docs/NON_VIP_PRECEDENT_TRANSPARENCY_UPDATE.md` | New file | Previous fix documentation |
| `docs/TIMING_VALIDATION_FIX.md` | New file | This documentation |

---

## Success Criteria

✅ **Fix is successful when:**

1. Agent always checks `days_since_purchase` immediately after order lookup
2. Late returns (> 30 days) trigger automatic VIP check and precedent search
3. ORD-888 flow includes:
   - Detection of 39-day age
   - Check for VIP status
   - Search for holiday precedent
   - Explanation of 60-day policy
   - Transparent approval message
4. Logs show complete exception protocol execution
5. Customer receives educational, transparent response

❌ **Fix has failed if:**

1. Late returns are approved without checking precedents
2. ORD-888 approves silently (no mention of holiday policy)
3. Logs don't show `check_vip_status` and `check_precedents` calls
4. Agent skips timing validation and relies only on `eligible_for_return` flag

---

## Next Steps

1. **Test in development environment** with ORD-888 workflow
2. **Verify logs** show complete exception protocol
3. **Validate response** includes transparency message
4. **Test edge cases:**
   - Day 30 exactly (should pass)
   - Day 31 (should trigger exception check)
   - Day 60 for December purchase (should pass with holiday exception)
   - Day 61 for December purchase (should fail, outside 60-day window)
5. **Monitor for regressions** in standard return flows (ORD-555, ORD-111, etc.)

---

## Related Documentation

- **NON_VIP_PRECEDENT_TRANSPARENCY_UPDATE.md** - Section 6 transparency requirements
- **EXPECTED_VIP_RESPONSE.md** - VIP exception formatting examples
- **BEFORE_AFTER_FLOW.md** - Return workflow comparisons
- **IMPLEMENTATION_SUMMARY.md** - Overall system architecture

---

**Implementation Date:** 2026-02-13
**Implemented By:** Claude Code
**Issue Resolution:** Late return detection + Holiday gift exception transparency
