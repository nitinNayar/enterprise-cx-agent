# Demo Scenarios for Bookly CX Agent

## 1. ORDER STATUS TRACKING

### Scenario 1A: Simple Order Tracking (Happy Path)
**Input:** "I want to check on my order ORD-2002"

**Expected Flow:**
- Agent looks up order → Status: shipped (pre-ordered book)
- Gets customer info → Trinity, VIP Silver
- Greeting: "Hello Trinity! Thank you for being a valued Silver VIP customer..."
- Provides tracking details and delivery estimate (2-3 days)

---

### Scenario 1B: Pre-Order Status Check
**Input:** "What's the status of my order ORD-2003?"

**Expected Flow:**
- Agent looks up order → Status: processing (rare book)
- Customer: Lara Croft, VIP Platinum
- Explains: Special order being sourced from third-party, ships in 7-10 days
- Sets expectation for collector-quality item

---

## 2. SIMPLE RETURNS (Policy-Compliant)

### Scenario 2A: Unopened Book Return
**Input:** "I need to return my order ORD-123"

**Expected Flow:**
1. Looks up order → John McClane, VIP Gold, "Die Hard" book
2. **Greeting:** "Hello John! Thank you for being a valued Gold VIP customer for X years..."
3. **Asks:** "Is the book in its original, unread condition with no bent spines or markings?"
4. **You respond:** "Yes, it's unopened"
5. **May ask:** "May I ask why you'd like to return this item?"
6. **You respond:** "Ordered by mistake"
7. **Approval + Soft Offer:** "Good news! Your return is approved ✓ ... Before I finalize, I noticed you love action thrillers - would you like to see a couple recommendations?"
8. **Option A:** Say "Yes" → See 3 book recommendations with 15% VIP discount → Can exchange
9. **Option B:** Say "No thanks" → Processes refund immediately

---

### Scenario 2B: Return with Exchange
**Input:** "I want to return order ORD-555"

**Expected Flow:**
1. Customer: Trinity, VIP Silver, "Neuromancer" book
2. Greeting + condition check → "Yes, unopened"
3. Reason: "Changed my mind about genre"
4. **Approval:** "Good news! Your return is approved ✓"
5. **Soft offer:** Shows 3 sci-fi/tech book recommendations with 10% VIP discount
6. **You respond:** "I'll take the second one"
7. **Automatic exchange:** Processes return + new order in one transaction
8. Shows complete exchange summary (new order ID, delivery, payment adjustment)

---

## 3. POLICY DENIALS (Non-VIP)

### Scenario 3A: Downloaded E-book (Clear Denial)
**Input:** "I need to return order ORD-1001"

**Expected Flow:**
1. Order lookup → "The Art of War" E-book, Maximus (Regular customer)
2. Greeting → "Hello Maximus! I can help with your return..."
3. **Asks:** "Have you downloaded or accessed this e-book yet?"
4. **You respond:** "Yes, I downloaded it"
5. Calls policy → Digital products non-returnable once downloaded
6. Checks VIP status → NOT VIP
7. **Denies politely:** "Unfortunately, our return policy doesn't allow returns for digital products once downloaded..."
8. No offer to escalate (standard policy applies)

---

### Scenario 3B: Gift Card (Non-Returnable)
**Input:** "I want to return my gift card from order ORD-666"

**Expected Flow:**
1. Indiana Jones, regular customer, $50 digital gift card
2. Greeting + asks: "Has the gift card been redeemed or used?"
3. **You respond:** "No, I haven't used it"
4. Checks policy → Gift cards non-returnable per policy
5. **Denies politely:** Explains gift cards are final sale items

---

## 4. VIP EXCEPTIONS (Using Precedent Graph)

### Scenario 4A: VIP Exception - Read Book
**Input:** "I need to return order ORD-777"

**Expected Flow:**
1. Sarah Connor, VIP Platinum, "Terminator Files" signed edition
2. Greeting + condition check
3. **Asks:** "Is the book in original, unread condition?"
4. **You respond:** "Actually, I opened it and read the first chapter"
5. Checks policy → Opened/read books non-returnable
6. **Automatic VIP check** → is_vip: true, Platinum tier
7. **Checks precedents** with tags: "vip book read"
8. **Finds precedent:** Previous manager approved for VIP customers
9. **Grants exception:** "Thank you for being a valued Platinum VIP... As a special exception for our VIP members..."
10. Explains one-time exception, processes return with VIP benefits

---

### Scenario 4B: VIP + Downloaded Audiobook
**Input:** "I want to return order ORD-222"

**Expected Flow:**
1. Ethan Hunt, VIP Gold, audiobook download
2. Greeting + asks: "Have you downloaded or accessed this audiobook?"
3. **You respond:** "Yes, I listened to 2 chapters"
4. Policy → Digital products non-returnable once accessed
5. **Auto VIP check** → Gold VIP, 5+ years
6. **Checks precedents:** "vip audiobook downloaded"
7. **Finds precedent** OR **No precedent found**:
   - If found: Grants exception
   - If not found: "This requires manager review. May I escalate to a specialist?"
8. If escalate → Uses `escalate_order_issue` with VIP context

---

### Scenario 4C: VIP + Late Return (Outside Window)
**Input:** "I need to return order ORD-888"

**Expected Flow:**
1. Jack Ryan, Regular customer, Sherlock Holmes gift set
2. Note: 39 days since purchase (outside 30-day window)
3. Greeting + condition check → "Unopened"
4. Policy → 30-day return window
5. VIP check → NOT VIP
6. **Denies:** "Our return policy allows returns within 30 days... yours was purchased 39 days ago"
7. No exception offered (not VIP)

---

## 5. BOOK RECOMMENDATIONS + EXCHANGE

### Scenario 5A: Accept Recommendations
**Input:** "I want to return order ORD-111"

**Expected Flow:**
1. James Bond, Regular customer, "Casino Royale" hardcover
2. Condition check → "Unopened"
3. Reason → "Not what I expected"
4. **Approval + Soft Offer:** Shows 3 spy/thriller recommendations (no VIP discount, regular customer)
5. **You respond:** "I like the first one"
6. **Process exchange:** One-click exchange transaction
7. Return processed + new order created + payment handled automatically

---

## 6. ANGRY CUSTOMER ESCALATION

### Scenario 6A: Order Status - Angry Customer
**Input:** "Where is my order? This is taking FOREVER! I ordered this weeks ago!"

**Expected Flow:**
1. Agent asks: "I'm sorry for the frustration. What's your order number?"
2. **You respond:** "ORD-2003 and this is ridiculous!"
3. Looks up order + customer info
4. Detects anger/frustration
5. **Immediate escalation:** Uses `escalate_order_issue`
6. "I'm going to connect you with a specialist right away. Reference: TICKET-ORDER-XXXX"
7. No further processing - hands off to human

---

### Scenario 6B: Return Request - Angry Mid-Conversation
**Input:** "I want to return order ORD-333"

**Expected Flow:**
1. Jack Sparrow, regular customer, Pirates book
2. Greeting + condition check
3. **You respond:** "It's damaged! I spilled rum on it, but that's not my fault! This is ridiculous!"
4. Agent detects anger + policy violation (customer damaged it)
5. **Immediate escalation:** `escalate_order_issue` with context
6. Doesn't argue about who damaged it - escalates to human

---

## 7. GENERAL SUPPORT QUESTIONS

### Scenario 7A: Policy Question (Shipping)
**Input:** "Do you ship to India?"

**Expected Flow:**
1. Checks policy → No info about India shipping
2. **Escalates:** Uses `escalate_general_question`
3. Category: "shipping_inquiry"
4. "Let me connect you with our shipping specialist... Reference: TICKET-GEN-XXXX"

---

### Scenario 7B: Account Issue
**Input:** "I can't reset my password - I've tried 3 times and no email is coming"

**Expected Flow:**
1. Provides basic troubleshooting: Check spam, wait 5 minutes
2. If still failing: **Escalates** `escalate_general_question`
3. Category: "account_issue"
4. Ticket created for technical support

---

### Scenario 7C: Policy Question (Returns - General)
**Input:** "What's your return policy for books?"

**Expected Flow:**
1. Calls `get_policy_info(policy_type="returns")`
2. Explains: 30 days, unread condition, no bent spines
3. Notes: Digital products non-returnable once downloaded
4. Asks: "Do you have a specific book you'd like to return?"

---

## 8. EDGE CASES

### Scenario 8A: Damaged Book (Customer Fault)
**Input:** "I want to return order ORD-333"

**Flow:**
1. Jack Sparrow, regular customer
2. **Agent asks:** "Is the book in original, unread condition?"
3. **You respond:** "Well, I spilled rum on it..."
4. Policy → Customer-damaged items non-returnable
5. VIP check → NOT VIP
6. **Polite denial:** Explains policy about customer-caused damage

---

### Scenario 8B: Personalized Item
**Input:** "I need to return order ORD-1234"

**Flow:**
1. Ethan Hunt, VIP Gold, personalized box set with inscription
2. Condition check → "Unopened"
3. Policy → Personalized items typically non-returnable
4. **VIP check** → Gold VIP
5. May check precedents for "vip personalized"
6. Depends on precedent: Exception or escalate for manager review

---

## 9. SUBSCRIPTION BOX

### Scenario 9A: Cancel Before Shipment
**Input:** "I want to cancel order ORD-2001"

**Flow:**
1. James Bond, Book Club subscription box (processing)
2. Status: Not yet shipped (within 2-3 days)
3. **Option:** Can cancel before shipment
4. Processes cancellation/return with no restocking fee

---

## QUICK REFERENCE

**VIP Customers (for exceptions):**
- CUST-VIP-0001: John McClane (Gold)
- CUST-VIP-9921: Sarah Connor (Platinum)
- CUST-VIP-0555: Trinity (Silver)
- CUST-VIP-0222: Ethan Hunt (Gold)
- CUST-VIP-0444: Lara Croft (Platinum)

**Orders with Policy Issues:**
- ORD-222: Downloaded audiobook
- ORD-777: Read book (opened)
- ORD-333: Customer-damaged
- ORD-666: Gift card
- ORD-1001: Downloaded e-book
- ORD-456: Outside return window

**Clean Returns:**
- ORD-123, ORD-555, ORD-111, ORD-444
