# 🎬 Bookly Demo Guide - Test Scenarios

Quick reference for testing the intelligent return workflow with personalized recommendations and automatic exchanges.

---

## 🚀 Setup

```bash
chainlit run app.py -w
```

Open browser: http://localhost:8000

---

## 📋 Test Scenarios

### 1️⃣ Happy Path - VIP Exchange (ORD-123)

**Tests:** Personalized greeting, VIP acknowledgment, recommendation engine, automatic exchange

**Customer:** John McClane (Gold VIP, 5 years)

**Script:**
```
You: I want to return my order
Agent: What's your order ID?
You: ORD-123
Agent: [Should greet: "Hello John! Thank you for being a valued Gold VIP
       customer for 5 years..." with order details]
You: Yes, unopened
Agent: [Approves return, shows 3 personalized thriller recommendations
       with Lee Child/Michael Connelly references]
You: I'll take The Concrete Blonde
Agent: [Automatically processes exchange, shows complete transaction details]
```

**✅ Validates:**
- Personalized greeting with customer name
- VIP tier and loyalty acknowledgment
- Order item details in greeting
- Approval BEFORE recommendations
- Specific genre/author personalization ("loved thrillers by Lee Child...")
- Automatic exchange processing (return + new order)
- Same delivery address
- Payment difference auto-handled

---

### 2️⃣ Late Return - Policy Enforcement (ORD-456)

**Tests:** Policy denial, no VIP exception, regular customer greeting

**Customer:** Jason Bourne (Regular, 2 years)

**Script:**
```
You: can I return order ORD-456?
Agent: [Should greet: "Hello Jason! Thank you for being a loyal customer
       for 2 years..." with "The Bourne Identity" details]
You: The book is in original, unread condition
Agent: [Denies return - outside 30-day window, offers alternatives]
```

**✅ Validates:**
- Greeting with loyalty acknowledgment (2 years)
- Policy enforcement (45 days > 30-day window)
- No VIP exception (regular customer)
- Polite denial with explanation

---

### 3️⃣ Angry Customer - No Upsell (ORD-999)

**Tests:** Sentiment detection, skipping recommendations, quick processing

**Customer:** Neo Anderson (Regular, frustrated about delayed shipment)

**Script:**
```
You: I want to return order ORD-999
Agent: What's your order ID?
You: ORD-999
Agent: [Should greet: "Hello Neo! I can help you with your return for
       order ORD-999..." acknowledges frustration]
You: "The Matrix and Philosophy" still in original condition
Agent: [Approves return quickly WITHOUT showing recommendations]
```

**✅ Validates:**
- Detects angry customer sentiment
- Skips upsell motion (no recommendations)
- Quick processing to resolve frustration
- Empathetic tone

---

### 4️⃣ Recommendation Declined (ORD-123)

**Tests:** Graceful handling of declined recommendations

**Customer:** John McClane (Gold VIP)

**Script:**
```
You: I want to return my order
You: ORD-123
Agent: [Greets, asks condition]
You: Yes, unopened
Agent: [Approves return, offers recommendations]
You: No thanks, just process the return
Agent: [Gracefully accepts, processes refund immediately]
```

**✅ Validates:**
- Approval message appears first
- Soft, optional recommendation offer
- Accepts "no" gracefully
- No repeated sales pitches
- Immediate refund processing

---

### 5️⃣ VIP Exception Test (ORD-777)

**Tests:** VIP status check, precedent matching, exception approval

**Customer:** Sarah Connor (Platinum VIP)

**Script:**
```
You: can I return order ORD-777?
Agent: [Greets with Platinum VIP acknowledgment]
You: I opened it and read the first chapter
Agent: [Checks VIP status, finds precedent, grants exception]
```

**✅ Validates:**
- Automatic VIP status check on policy violation
- Precedent graph query
- VIP exception approval
- Conditions explained ("one-time exception")
- VIP gratitude messaging

---

### 6️⃣ New Customer (ORD-888)

**Tests:** Greeting for new customers without loyalty years

**Customer:** Jack Ryan (Regular, 6 years)

**Script:**
```
You: can I return order ORD-888?
Agent: [Should greet: "Hello Jack! Thank you for being a loyal customer
       for 6 years..." with order details]
```

**✅ Validates:**
- Greeting adapts to customer tenure
- Rounds years_active properly
- Still professional and friendly

---

## 🎯 Key Things to Watch For

### Every Scenario Should Have:

1. **Personalized Greeting**
   - ✅ Customer name ("Hello John!")
   - ✅ Loyalty acknowledgment (VIP tier or years)
   - ✅ Order ID and item details
   - ✅ Policy-specific question

2. **Approval Before Recommendations**
   - ✅ "Good news! Your return is approved ✓"
   - ✅ Complete refund details
   - ✅ THEN soft offer of recommendations

3. **Personalized Recommendations** (if offered)
   - ✅ Specific genres mentioned ("thrillers")
   - ✅ Specific authors mentioned ("Lee Child and Michael Connelly")
   - ✅ Reference to past purchases ("you gave Killing Floor 5 stars!")
   - ✅ VIP pricing shown prominently

4. **Automatic Exchange** (if accepted)
   - ✅ Return processed
   - ✅ New order created
   - ✅ Same delivery address mentioned
   - ✅ Payment difference shown
   - ✅ Tracking info promised

---

## 🐛 Common Issues to Check

### ❌ Agent skips greeting
**Fix:** Restart app, check prompts.py has greeting protocol at top

### ❌ Generic recommendations ("great taste in books")
**Fix:** Should use specific genres/authors from customer data

### ❌ Recommendations before approval
**Fix:** Should approve return FIRST, then offer recommendations

### ❌ Shows recommendations to angry customer
**Fix:** Should detect sentiment and skip upsell

### ❌ Manual exchange process
**Fix:** Should use `process_exchange` tool for automatic handling

---

## 📊 Quick Test Matrix

| Order | Customer | VIP | Scenario | Expected Outcome |
|-------|----------|-----|----------|------------------|
| ORD-123 | John McClane | Gold | Happy path | Personalized recs → exchange |
| ORD-456 | Jason Bourne | No | Late return | Policy denial |
| ORD-999 | Neo Anderson | No | Angry customer | Quick process, no upsell |
| ORD-777 | Sarah Connor | Platinum | Opened book | VIP exception granted |
| ORD-888 | Jack Ryan | No | Loyal customer | Greeting with years |

---

## 🎓 Demo Tips

1. **Start with ORD-123** (best showcase of all features)
2. **Use exact phrases** from scripts for consistency
3. **Watch the logs** to see tool call sequence
4. **Check for emojis** in responses (📚 ✅ 🎉)
5. **Note the tone** - should feel helpful, not pushy

---

## 🚨 Critical Success Criteria

Each test MUST show:

- [x] Personalized greeting with customer name
- [x] Order details mentioned in greeting
- [x] Loyalty/VIP acknowledgment
- [x] Policy-specific question asked
- [x] Return approval stated explicitly
- [x] Recommendations personalized (not generic)
- [x] Automatic exchange if customer accepts
- [x] No recommendations if customer angry

---

## 💡 Advanced Tests

### Test Personalization Variations:

**Sci-Fi Fan:**
- Use customer with sci-fi history
- Should see "loved sci-fi classics" not "thrillers"

**Mystery Fan:**
- Should see "enjoyed Agatha Christie's mysteries"

**Romance Fan:**
- Should see "loved contemporary romance"

### Test Error Handling:

**Invalid Order ID:**
```
You: can I return order ORD-FAKE?
Agent: [Should handle gracefully]
```

**Unclear Response:**
```
You: maybe?
Agent: [Should ask for clarification]
```

---

## 📞 Support

**Issue?** Check:
1. Logs in `/logs/console.log`
2. Audit trail in `/logs/decision_audit.log`
3. `GREETING_BUG_FIX.md` for greeting issues
4. `BEFORE_AFTER_FLOW.md` for workflow issues

**Still stuck?** Run diagnostic:
```bash
python diagnose_connection.py
```

---

**Last Updated:** 2026-02-09
**Version:** 2.0 (with automatic exchange and personalization)
