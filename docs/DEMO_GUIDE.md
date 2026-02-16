# Bookly Demo Guide

**Complete demo script for showcasing the Bookly customer support agent**

---

## Pre-Demo Setup (5 minutes)

### 1. Initialize Database
```bash
# From project root
python scripts/init_graph.py
```

**Expected output:**
```
✅ Schema created successfully!
  → Converting PREC-VIP-001 (VIP Read Book)...
  → Converting PREC-HOL-002 (Holiday Gift Book)...
  → Converting PREC-AUDIO-003 (Book Club VIP Audiobook)...
  ✅ 3 precedents converted successfully
```

### 2. Start Observability (Terminal 1)
```bash
python -m phoenix.server.main serve
```

**Verify:** Open http://localhost:6006 in browser

### 3. Start Bookly Agent (Terminal 2)
```bash
chainlit run app.py -w
```

**Verify:** Open http://localhost:8000 in browser

### 4. Select Profile
- Click **"TrueCart Support"** (customer-facing mode)
- Leave admin mode for later

---

## Demo Flow (20-30 minutes)

### Part 1: The Basics (5 min)
Show standard functionality and agent personality

### Part 2: Policy Enforcement (5 min)
Show how the agent enforces complex rules

### Part 3: VIP Exceptions (10 min)
**⭐ The "wow" moment** - Show precedent-based decision making

### Part 4: Observability (5 min)
Show the decision trace and audit trail

---

## Part 1: The Basics

### Scenario 1A: Simple Return (Happy Path)

**Purpose:** Show basic flow and personalized greeting

**Customer Message:**
```
I want to return my order ORD-123
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → Gets order details
2. ✅ Calls `get_customer_info` → Gets John McClane (Gold VIP, 5 years)
3. ✅ Outputs greeting:
   - "Hello John McClane! Thank you for being a valued Gold VIP customer for 5 years."
   - Lists the item: "Die Hard: The Official Movie Novelization"
   - Asks: "Is the book in unread condition with no bent pages or markings?"
4. 🛑 **Agent stops and waits** (this is key!)

**Your Response:**
```
Yes, I haven't opened it yet. Just changed my mind.
```

**Agent Flow Continues:**
5. ✅ Calls `get_policy_info` → Reads return policy
6. ✅ Determines: Book is unread, within 30 days → COMPLIANT
7. ✅ Calls `execute_order_return`
8. ✅ Outputs: "✅ Return approved! Transaction ID: txn_xxxxx"

**Key Points to Highlight:**
- 🎯 Agent follows mandatory sequence (order → customer → greeting → STOP)
- 🎯 Personalized greeting with VIP acknowledgment
- 🎯 Policy-specific question (asks about book condition)
- 🎯 Conversational flow (doesn't rush to decision)

---

### Scenario 1B: Shipped Order Tracking

**Purpose:** Show handling of in-transit orders

**Start New Chat** (to reset conversation)

**Customer Message:**
```
Where is my order ORD-2002? I pre-ordered it and it should be here by now!
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → Status: "shipped"
2. ✅ Calls `get_customer_info` → Trinity (Silver VIP)
3. ✅ Outputs greeting + status:
   - "Hello Trinity! Thank you for being a valued Silver VIP customer for 1.5 years."
   - "Your order for 'The Simulation Hypothesis' is currently shipped and in transit."
   - "Estimated delivery: 2-3 days"

**Key Points to Highlight:**
- 🎯 Agent handles "shipped" status appropriately
- 🎯 Provides tracking information from order notes
- 🎯 Manages expectations with delivery estimate
- 🎯 Positive sentiment maintained

---

## Part 2: Policy Enforcement

### Scenario 2A: Late Return (Regular Customer)

**Purpose:** Show policy enforcement without VIP override

**Start New Chat**

**Customer Message:**
```
I need to return order ORD-456. I bought it 45 days ago.
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → eligible_for_return: false, reason: "window_expired"
2. ✅ Calls `get_customer_info` → Jason Bourne (Regular, not VIP)
3. ✅ Outputs greeting with tenure acknowledgment
4. 🛑 Waits for response

**Your Response:**
```
The book is in perfect condition, I just forgot about it.
```

**Agent Flow Continues:**
5. ✅ Calls `get_policy_info` → 30-day return window
6. ✅ Determines: Outside 30-day window → DENY
7. ✅ Calls `check_vip_status` → is_vip: false (AUTOMATIC check!)
8. ❌ Outputs polite denial:
   - "I understand you'd like to return this book."
   - "However, our return policy requires returns within 30 days of delivery."
   - "Since this order was delivered 45 days ago, I'm unable to process the return."

**Key Points to Highlight:**
- 🎯 Agent AUTOMATICALLY checks VIP status even when customer doesn't mention it
- 🎯 Policy is enforced for regular customers
- 🎯 Polite, empathetic denial
- 🎯 Clear explanation of policy

---

### Scenario 2B: Digital Product (E-book)

**Purpose:** Show non-returnable digital goods

**Start New Chat**

**Customer Message:**
```
I want to return order ORD-1001. I accidentally bought the wrong book.
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → "The Art of War" (E-book download)
2. ✅ Calls `get_customer_info` → Maximus Decimus (Regular)
3. ✅ Outputs greeting

**Your Response:**
```
I downloaded it but realized it's not what I needed for my class.
```

**Agent Flow Continues:**
4. ✅ Calls `get_policy_info` → E-books are non-returnable once downloaded
5. ✅ Calls `check_vip_status` → is_vip: false
6. ❌ Outputs denial:
   - "I understand the situation."
   - "However, e-books are non-returnable once downloaded per our policy."
   - "This is because digital content is immediately accessible."

**Key Points to Highlight:**
- 🎯 Different rules for digital vs. physical products
- 🎯 Policy is clear and enforced consistently
- 🎯 Agent explains *why* the policy exists

---

## Part 3: VIP Exceptions ⭐

### Scenario 3A: Read Book Exception (The "Wow" Moment)

**Purpose:** Show precedent-based VIP exception - THIS IS THE HIGHLIGHT!

**Start New Chat**

**Customer Message:**
```
I want to return order ORD-777. I'm a Book Club Platinum member.
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → "The Terminator Files" (Signed Edition)
2. ✅ Calls `get_customer_info` → Sarah Connor (Platinum VIP, 10 years, $50k!)
3. ✅ Outputs VIP greeting:
   - "Hello Sarah Connor! Thank you for being a valued **Platinum VIP customer for 10 years.**"
   - Lists: "The Terminator Files: Technical Manual (Hardcover, Signed Edition)"
   - Asks: "To process this return, I need to confirm: is the item still sealed in its original packaging, or has it been opened?"
4. 🛑 Stops and waits (CRITICAL - doesn't assume!)

**Your Response:**
```
I opened it and read the first chapter, but the content wasn't what I expected. I know signed editions are usually final sale, but I've been with you for 10 years.
```

**Agent Flow Continues:**
5. ✅ Calls `get_policy_info` → Read books non-returnable, signed editions must be pristine
6. ✅ Policy says: **DENY** (read book + signed edition)
7. ✅ Calls `check_vip_status` → ALREADY DONE, knows is_vip: true
8. 🔍 Calls `check_precedents("vip book read signed book_club loyalty")`
9. ✅ **Graph returns:** DEC-2024-001 (Sarah Chen, VP Customer Experience)
   - Decision: APPROVE
   - Reasoning: "Book Club Platinum members with demonstrated loyalty..."
   - Conditions: "One-time exception only. Limited to once per year."
10. ✅ Calls `execute_order_return` (uses precedent!)
11. 🎉 Outputs VIP exception response:

**Expected Response Format:**
```
✅ Return approved and processed!

Transaction ID: txn_xxxxx

**Important: This is a special exception to our standard policy**

"The Terminator Files: Technical Manual" would normally not be eligible for return
since you opened and read the book, and signed editions must be in pristine condition
to maintain their collectible value. However, as a valued Platinum customer, we're
making an exception in this case.

**Please note:** This is a one-time courtesy exception and may not apply to future
requests. This exception is limited to one read book return per customer per year.

We truly appreciate your 10 years of loyalty and your business!

Your refund has been processed to your original payment method and should appear
within 5-7 business days.
```

**🎤 Demo Script - What to Say:**

*"Now here's where it gets interesting. Notice what just happened:"*

1. **"The agent automatically checked if Sarah is VIP"** - No prompting needed
2. **"The policy clearly said DENY - read books are non-returnable"** - Show policy.md
3. **"But the agent queried the precedent graph"** - The "case law" system
4. **"Found a decision from Sarah Chen (VP) that allows this exception"** - Real human decision
5. **"The response includes:"**
   - ✅ VIP acknowledgment (Platinum, 10 years)
   - ✅ Exception notice (this is special)
   - ✅ Conditions (one-time, once per year)
   - ✅ Gratitude for loyalty

*"This is NOT the agent hallucinating an exception. This is based on a real decision stored in the graph database. Let me show you the source..."*

**Open:** `data/decision_emails/esc-2024-001-vip-read-book-exception.txt`

*"Here's the actual email from Sarah Chen, VP of Customer Experience, approving this exact scenario."*

---

### Scenario 3B: Holiday Gift Exception (Non-VIP!)

**Purpose:** Show precedents can apply to non-VIP customers too

**Start New Chat**

**Customer Message:**
```
I need to return order ORD-888. It was a Christmas gift I bought in December.
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → Delivered 39 days ago (outside 30-day window!)
2. ✅ Calls `get_customer_info` → Jack Ryan (Regular customer, NOT VIP)
3. ✅ Outputs greeting with tenure

**Your Response:**
```
The recipient just told me they already own this collection. I know it's past 30 days but it was a holiday gift.
```

**Agent Flow Continues:**
4. ✅ Calls `get_policy_info` → 30-day return window
5. ✅ Policy says: **DENY** (39 days > 30 days)
6. ✅ Calls `check_vip_status` → is_vip: false
7. 🔍 Calls `check_precedents("holiday gift late december")`
8. ✅ **Graph returns:** DEC-2024-002 (Mike Rodriguez, Customer Service Manager)
   - Decision: APPROVE
   - Reasoning: "Holiday gifts need extended consideration..."
   - Conditions: "60-day window for November-December purchases"
9. ✅ Calls `execute_order_return`
10. 🎉 Outputs approval with holiday exception notice

**Key Points to Highlight:**
- 🎯 Regular customer (not VIP) can get exceptions
- 🎯 Seasonal/temporal precedents (holiday rules)
- 🎯 Context matters ("holiday gift" keywords trigger precedent search)
- 🎯 Agent explains the extended window

---

### Scenario 3C: Audiobook Exception (Digital Product!)

**Purpose:** Show even "non-returnable" digital goods can have exceptions

**Start New Chat**

**Customer Message:**
```
I need to return order ORD-222. I'm a Book Club Silver member and I buy tons of audiobooks from you.
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → "Master of Disguise" (Audiobook download)
2. ✅ Calls `get_customer_info` → Ethan Hunt (Silver VIP, $8k, "prefers audiobooks")
3. ✅ Outputs VIP greeting

**Your Response:**
```
I downloaded it and listened to 2 chapters, but the narrator's voice makes it impossible for me to focus. Can you make an exception?
```

**Agent Flow Continues:**
4. ✅ Calls `get_policy_info` → Audiobooks non-returnable once downloaded
5. ✅ Policy says: **DENY** (digital product, downloaded)
6. ✅ Already knows: is_vip: true (Silver)
7. 🔍 Calls `check_precedents("vip audiobook digital downloaded book_club narrator")`
8. ✅ **Graph returns:** DEC-2024-003 (Jennifer Park, Director CX)
   - Decision: APPROVE
   - Conditions: "Book Club members $5k+, <20% consumed, once per year, 7 days"
9. ✅ Calls `execute_order_return`
10. 🎉 Outputs approval with digital exception notice

**Key Points to Highlight:**
- 🎯 Digital products CAN have exceptions (for loyal customers)
- 🎯 Specific conditions (20% rule, 7-day reporting, once per year)
- 🎯 Legitimate use case (narrator compatibility)
- 🎯 Rewards loyalty (47 audiobooks purchased!)

**🎤 Demo Script:**
*"Notice this is a DIGITAL PRODUCT - normally these are absolutely non-returnable. But the agent found a precedent for Book Club members who are frequent audiobook buyers. The narrator issue is a real problem that can't be evaluated before purchase. This exception rewards loyalty while having guardrails (20% consumption limit, must report within 7 days)."*

---

## Part 4: Observability & Audit Trail

### Open Phoenix UI

**Navigate to:** http://localhost:6006

1. Click **"Traces"** tab
2. Find the most recent trace (Sarah Connor / ORD-777)
3. Click to expand

**Show the Waterfall:**
- User message
- Tool call: `look_up_order`
- Tool call: `get_customer_info`
- Agent thinking/reasoning
- Tool call: `get_policy_info`
- Tool call: `check_vip_status`
- Tool call: `check_precedents` ← **Highlight this!**
- Tool result: Shows DEC-2024-001, Sarah Chen, VP
- Tool call: `execute_order_return`
- Final response to user

**🎤 Demo Script:**
*"Here's the complete decision trail. Every API call, every tool execution, every decision is logged and traceable. You can see exactly when the agent queried the precedent graph, what it found, and how it used that information to make the decision."*

---

### Admin Decision Viewer

**Start New Chat**

**Select Profile:** "TrueCart Admin" (decision trace viewer)

**Get Session ID from logs:**
```bash
tail -20 logs/decision_audit.log | grep SESSION
```

**Copy a session ID** (e.g., `SESSION-a1b2c3d4`)

**Enter in Admin UI:**
```
SESSION-a1b2c3d4
```

**Show the Formatted Trace:**
- User messages
- Tool calls with inputs
- Precedent matches with attribution
- Decision maker names (Sarah Chen, Jennifer Park)
- Final agent decisions

**🎤 Demo Script:**
*"This is the admin view. Internal staff can investigate any customer session. See how we track not just WHAT the agent decided, but WHO made the original human decision (Sarah Chen, VP Customer Experience). This is complete auditability and attribution."*

---

## Part 5: Edge Cases (Bonus)

### Scenario 5A: Angry Customer (Immediate Escalation)

**Start New Chat**

**Customer Message:**
```
This is absolutely RIDICULOUS! My order ORD-999 STILL hasn't shipped! This is a SCAM!
```

**Agent Flow:**
1. 🚨 Detects angry sentiment/keywords
2. ✅ Calls `escalate_to_human` **IMMEDIATELY** (no policy checks!)
3. 🎫 Outputs:
   - "I'm very sorry you're experiencing frustration..."
   - "I've immediately escalated your case (Ticket TKT-xxx)..."
   - De-escalation language

**Key Points:**
- 🎯 Safety valve - angry customers go straight to human
- 🎯 No arguing, no policy debates
- 🎯 Immediate acknowledgment and empathy

---

### Scenario 5B: Processing Order Cancellation

**Start New Chat**

**Customer Message:**
```
I want to cancel order ORD-2001 before it ships.
```

**Agent Flow:**
1. ✅ Calls `look_up_order` → Status: "processing" (not shipped yet!)
2. ✅ Calls `get_customer_info` → James Bond
3. ✅ Outputs greeting

**Your Response:**
```
I changed my mind about the subscription box.
```

**Agent Flow:**
- Explains order is still being prepared
- Likely offers to cancel (since not shipped)
- Or escalates to ensure cancellation happens in time

**Key Points:**
- 🎯 Different handling for "processing" vs. "shipped"
- 🎯 Processing orders can potentially be modified/canceled
- 🎯 Shipped orders cannot

---

## Demo Talking Points

### The Problem We're Solving

*"Traditional customer service chatbots are black boxes - you never know what they'll say or do. They might approve returns they shouldn't, or deny returns they should approve. There's no consistency, no audit trail, and no way to teach them from human decisions."*

### The Solution: Three Layers

**Layer 1: Policy as Code**
- Written policies in markdown
- Agent reads and interprets them
- Policy ALWAYS wins over database flags

**Layer 2: Graph-Based Precedents**
- Real human decisions stored as graph relationships
- Agent queries for similar cases
- "Case law" system for edge cases

**Layer 3: Complete Auditability**
- Every decision traced
- Attribution to human decision makers
- Phoenix observability shows the "chain of thought"

### Key Differentiators

1. **Deterministic** - Same input = same output (Temperature = 0.0)
2. **Auditable** - Every decision traceable to policy or precedent
3. **Adaptive** - Learns from human decisions without retraining
4. **Governed** - Three-layer governance (DB → Policy → Precedents)
5. **Observable** - OpenTelemetry + Phoenix for real-time monitoring

### Business Value

- **Reduces escalations** - VIP customers get exceptions automatically
- **Maintains consistency** - Policy enforced for everyone
- **Rewards loyalty** - VIPs acknowledged and treated specially
- **Builds trust** - Transparent decision-making
- **Scales expertise** - VP decisions applied automatically by agent

---

## Quick Reference: Order Scenarios

| Order | Status | Customer | Type | Scenario |
|-------|--------|----------|------|----------|
| ORD-123 | Shipped | John McClane (Gold VIP) | Standard | Simple return, happy path |
| ORD-456 | Delivered | Jason Bourne (Regular) | Late | Return denied (45 days) |
| ORD-777 | Delivered | Sarah Connor (Platinum VIP) | Read Book | VIP exception (signed, read) |
| ORD-888 | Delivered | Jack Ryan (Regular) | Holiday Gift | Holiday exception (39 days) |
| ORD-222 | Delivered | Ethan Hunt (Silver VIP) | Audiobook | VIP digital exception |
| ORD-999 | Processing | Neo Anderson (Regular) | Angry | Immediate escalation |
| ORD-1001 | Delivered | Maximus (Regular) | E-book | Digital denied (non-returnable) |
| ORD-2001 | Processing | James Bond (Regular) | Subscription | Cancel before ship |
| ORD-2002 | Shipped | Trinity (Silver VIP) | Pre-order | Tracking request |
| ORD-2003 | Processing | Lara Croft (Gold VIP) | Rare Book | Status inquiry |

---

## Troubleshooting

### Agent not using precedents?
```bash
# Verify graph is initialized
python scripts/debug_graph.py

# Should show 3 precedents
```

### Phoenix not showing traces?
```bash
# Ensure Phoenix started BEFORE app
# Terminal 1: python -m phoenix.server.main serve
# Terminal 2: chainlit run app.py -w
```

### Agent giving wrong responses?
- Check `logs/console.log` for errors
- Check `config.py` - ensure TEMPERATURE = 0.0
- Verify system prompt hasn't been modified

---

## Post-Demo Q&A Prep

**Q: "What if a precedent doesn't exist?"**
A: Agent either denies (if policy says no) or offers to escalate to human for review. The human decision can then become a new precedent.

**Q: "Can precedents contradict each other?"**
A: Graph query ranks by relevance score and decision maker authority. VP decisions > Director > Manager.

**Q: "How do you add new precedents?"**
A: Create decision email file → Update `init_graph.py` → Re-run initialization. In production, you'd have an admin UI.

**Q: "What prevents the agent from hallucinating exceptions?"**
A: Tool-based architecture. Agent can ONLY approve exceptions if `check_precedents` returns found=true. It can't make up decisions.

**Q: "Is this production-ready?"**
A: This is a proof-of-concept. Production would need: authentication, rate limiting, real integrations (Stripe, Zendesk), security hardening, multi-tenancy, etc.

**Q: "What about other languages?"**
A: System prompt could be translated, or model could be prompted to detect/respond in customer's language.

---

## Advanced Demo: Live Graph Query

**Terminal 3:**
```bash
python scripts/debug_graph.py
```

**Or manual Cypher query:**
```python
python
>>> import kuzu
>>> db = kuzu.Database("data/context_graph_db")
>>> conn = kuzu.Connection(db)
>>> result = conn.execute("""
    MATCH (p:Person)-[m:MADE]->(d:Decision)
    RETURN p.name, p.role, d.title, d.outcome
    """)
>>> while result.has_next():
...     print(result.get_next())
```

**Show the graph structure live!**

---

## Success Metrics

**Demo is successful if audience understands:**
1. ✅ Agent follows strict workflow (not just chat)
2. ✅ Policy enforcement is real (not cosmetic)
3. ✅ VIP exceptions are precedent-based (not hallucinated)
4. ✅ Complete audit trail exists
5. ✅ System is deterministic and governable

**"Wow" moments to hit:**
- 🎯 Automatic VIP check (agent doesn't wait to be told)
- 🎯 Precedent query and application (Sarah Connor scenario)
- 🎯 Exception response format (perfect, not generic)
- 🎯 Phoenix waterfall (see the "thinking")
- 🎯 Admin trace viewer (complete attribution)

---

**Demo Time:** 20-30 minutes
**Audience:** Technical stakeholders, product managers, executives
**Goal:** Show enterprise-ready AI that's governed, auditable, and adaptive

**Good luck! 🎉**
