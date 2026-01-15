# Expected VIP Exception Response Format

## Scenario: VIP Customer with Opened Electronics (ORD-123)

### Order Details:
- Order ID: ORD-123
- Item: Wireless Headphones
- Customer: CUST-VIP-0001 (Gold VIP, 5 years active, $15k lifetime value)
- Issue: Customer opened the box/packaging (violates electronics policy)

### Precedent Applied:
- Decision ID: (from check_precedents)
- Decision Maker: Jennifer Park, Director of Customer Experience
- Precedent: ESC-2024-003 - Opened electronics exception for high-value customers
- Decision: APPROVED

---

## OLD RESPONSE (Missing Attribution - BAD):

```
✅ Return approved and processed!

Transaction ID: txn_87200

Refund Status: Your refund has been processed to your original payment method. You
should see it within 5-7 business days depending on your bank.

Thank you for being a loyal customer for the past 5 years. We truly appreciate your
business! If you have any other questions or need assistance, please don't hesitate to reach out.
```

**Problems:**
- ❌ No mention this is a special exception
- ❌ No attribution to Jennifer Park
- ❌ No explanation of conditions (one-time exception)
- ❌ No transparency about policy violation
- ❌ Customer doesn't understand WHY they got approved

---

## NEW RESPONSE (Customer-Friendly Exception - GOOD):

```
✅ Return approved and processed!

Transaction ID: txn_87200

**Important: This is a special exception to our standard policy**

Your Wireless Headphones would normally not be eligible for return since opened
electronics are final sale and must be in unopened, original packaging. However,
as a valued Gold VIP customer, we're making an exception in this case.

**Please note:** This is a one-time courtesy exception and may not apply to future
requests. This exception is limited to one opened electronics return per customer
per year.

We truly appreciate your 5 years of loyalty and your business!

Refund Status: Your refund has been processed to your original payment method. You
should see it within 5-7 business days depending on your bank.

If you have any other questions or need assistance, please don't hesitate to reach out.
```

**What's included:**
- ✅ VIP acknowledgment ("valued Gold VIP customer")
- ✅ Exception notice ("special exception to our standard policy")
- ✅ Policy explanation (what would normally happen and why)
- ✅ Conditions (one-time courtesy, limited to once per year)
- ✅ Gratitude with specifics (5 years from years_active field)
- ✅ Transaction details
- ✅ NO internal decision maker names (kept for audit logs only)

---

## Test Cases to Verify:

### Test 1: ORD-777 (VIP Socks - Sarah Chen Precedent)
**Expected:** Return approved with attribution to Sarah Chen, VP Customer Experience

### Test 2: ORD-222 (VIP Smartphone - Opened)
**Expected:** Return approved with attribution to Jennifer Park, Director CX

### Test 3: ORD-444 (VIP Opened Beauty Product)
**Expected:** VIP acknowledged, but likely no precedent → offer escalation

### Test 4: ORD-333 (Regular Customer - Socks)
**Expected:** Politely denied, NO mention of VIP system

---

## Key Fields from Tool Responses to Use:

### From `check_vip_status`:
```json
{
  "is_vip": true,
  "tier": "Gold",              ← USE IN CUSTOMER MESSAGE: "valued Gold VIP customer"
  "lifetime_value": 15000,     ← For internal tracking only
  "years_active": 5            ← USE IN CUSTOMER MESSAGE: "your 5 years of loyalty"
}
```

### From `check_precedents`:
```json
{
  "found": true,
  "person_name": "Jennifer Park",        ← AUDIT LOG ONLY (not in customer message)
  "person_role": "Director of CX",       ← AUDIT LOG ONLY (not in customer message)
  "conditions": "ONE-TIME exception...", ← USE IN CUSTOMER MESSAGE
  "rationale": "...",                    ← Internal only
  "reasoning": "..."                     ← Internal only
}
```

**IMPORTANT:**
- The agent MUST use `tier` and `years_active` in the customer response
- The agent MUST include `conditions` in the customer response
- The agent should NOT mention `person_name` or `person_role` to customers
- Decision maker attribution is for audit logs only (already logged automatically)
