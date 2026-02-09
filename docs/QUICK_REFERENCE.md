# Quick Reference - Copy & Paste Test Scripts

## Setup
```bash
chainlit run app.py -w
```

---

## Test 1: Happy Path (ORD-123)
**Shows:** Full feature showcase - greeting, recommendations, automatic exchange

```
I want to return my order
ORD-123
Yes, unopened
I'll take The Concrete Blonde
```

**Look for:**
- "Hello John! Thank you for being a valued Gold VIP customer for 5 years..."
- "loved thrillers by Lee Child and Michael Connelly"
- "Your exchange has been processed!"

---

## Test 2: Policy Denial (ORD-456)
**Shows:** Late return enforcement, regular customer handling

```
can I return order ORD-456?
The book is in original, unread condition
```

**Look for:**
- "Hello Jason! Thank you for being a loyal customer for 2 years..."
- "outside our 30-day return window"

---

## Test 3: Angry Customer (ORD-999)
**Shows:** No upsell when customer is frustrated

```
I want to return order ORD-999
"The Matrix and Philosophy" still in original condition
```

**Look for:**
- Quick processing WITHOUT recommendations
- Empathetic tone

---

## Test 4: Decline Recommendations (ORD-123)
**Shows:** Graceful handling of "no"

```
I want to return my order
ORD-123
Yes, unopened
No thanks, just process the return
```

**Look for:**
- "No problem at all!"
- Immediate refund processing

---

## Validation Checklist

Every response should have:
- [ ] Customer name in greeting
- [ ] Order ID and item details
- [ ] VIP/loyalty acknowledgment
- [ ] "Your return is approved ✓" (if approved)
- [ ] Specific genres/authors (not "great taste in books")
- [ ] "Totally optional!" for recommendations
