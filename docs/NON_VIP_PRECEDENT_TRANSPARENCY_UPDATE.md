# Non-VIP Precedent Transparency Update

**Date:** 2026-02-13
**Issue:** Agent was silently approving non-VIP precedent exceptions without explaining context to customers

---

## Problem Statement

When a non-VIP precedent (e.g., Holiday Gift Extension DEC-2024-002) approved a return that violated standard policy, the agent would approve it without explaining:
- What policy was being extended
- Why the customer qualified
- What made this approval different from standard policy

**Example:** ORD-888 (Jack Ryan, regular customer)
- Order was 39 days old (exceeds 30-day standard policy)
- Holiday gift exception applied (60-day window for Nov-Dec purchases)
- Agent approved silently without mentioning the extended holiday window

### Impact
- Customer unaware they received extended consideration
- Missed opportunity to build trust and goodwill
- No education about holiday gift policy
- Company's customer-first values not communicated

---

## Solution Implemented

Added new section **6** to the Exception Protocol in both `prompts.py` and `config.py`:

### New Section: Non-VIP Precedent Approvals

**When:** Customer is NOT VIP BUT a non-VIP precedent approves the return

**Requirements:**
1. **Context Acknowledgment** - Mention relevant context from order
2. **Extended Policy Explanation** - State the policy clearly and confidently
3. **Customer-First Reasoning** - Brief empathetic explanation of WHY
4. **Confirmation** - Reassure they meet the criteria
5. **Keep It Concise** - 2-3 sentences, placed BEFORE approval statement

---

## Key Principle

**Different messaging for different exception types:**

| Exception Type | Tone | Message Focus |
|---------------|------|---------------|
| **VIP Exception** | "You're special" | "We're making an exception FOR YOU" |
| **Non-VIP Precedent** | "We understand" | "We have sensible policies THAT MAKE SENSE" |

---

## Example: Before vs After

### BEFORE (No Transparency)
```
Customer: "yes [item is in good condition]"

Agent: "Good news! Your return is approved ✓

Refund Details:
- Refund amount: Will be credited for the original purchase price
- Processing time: 5-7 business days
..."
```

**Problem:** Customer has no idea this was 39 days old and holiday policy applied.

---

### AFTER (With Transparency)
```
Customer: "yes [item is in good condition]"

Agent: "Thank you for confirming. I see this was purchased in December as
a holiday gift - we extend our return window to 60 days for holiday purchases
made in November-December since recipients often need extra time to evaluate
gifts. Your return is well within that timeframe!

Good news! Your return is approved ✓

Refund Details:
- Refund amount: Will be credited for the original purchase price
- Processing time: 5-7 business days
..."
```

**Benefits:**
✅ Customer understands WHY it was approved
✅ Learns about 60-day holiday policy
✅ Feels understood (not confused by silent approval)
✅ Trust in Bookly's customer-first values
✅ Clear expectations (60 days for holidays, not unlimited)

---

## Files Modified

1. **`prompts.py`** - Lines 267-270
   - Updated section 5 to clarify it applies when no precedent found
   - Added new section 6 with full guidance and example

2. **`config.py`** - Lines 101-111
   - Updated section 5 to clarify it applies when no precedent found
   - Added new section 6 with condensed guidance

---

## Applicable Precedents

This guidance applies to any non-VIP precedents, including:

- **DEC-2024-002:** Holiday Gift Extension (60-day window for Nov-Dec purchases)
- Any future non-VIP precedents added to the knowledge graph
- Context-based exceptions that apply to ALL customers (not just VIPs)

---

## Testing Recommendations

Test with ORD-888 (Jack Ryan, holiday gift):
1. User: "I want to return order ORD-888"
2. Agent should greet Jack Ryan (regular customer, 3 years)
3. User: "dont need it anymore"
4. Agent should ask about condition
5. User: "yes [it's in good condition]"
6. **Expected:** Agent should mention holiday gift context, explain 60-day policy, THEN approve
7. **Verify:** Response includes all 5 required elements (context, policy, reasoning, confirmation, approval)

---

## Design Philosophy

**Transparency builds trust:**
- When you explain WHY you're approving something exceptional, customers appreciate it
- Silent approvals feel arbitrary or like policy enforcement is sloppy
- Educational moments create positive brand perception
- Customer-first values should be VISIBLE, not just internal

**Balance efficiency with clarity:**
- Keep it brief (2-3 sentences)
- Place before approval for logical flow
- Use positive framing ("we extend" not "you're late but...")
- Frame as policy, not favor

---

## Future Considerations

As new non-VIP precedents are added to the knowledge graph, ensure they include:
- Clear `context` field that can be surfaced to customers
- `reasoning` that explains the customer-first rationale
- `conditions` that can be communicated clearly

This allows the agent to consistently provide transparent, educational responses that build trust across all exception types.
