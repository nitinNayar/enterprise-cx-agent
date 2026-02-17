# Enterprise CX Agent - Design Document
**Nitin Nayar | Decagon AI Solutions Engineer Application**

---

## Key Features

This agent implements two critical capabilities that directly impact business metrics: revenue retention and operational efficiency.

### 1. **AI-Powered Upsell & Exchange Engine**

**Business Impact:**
- **Reduces return costs** by converting returns into exchanges
- **Increases revenue** by keeping customer spend within the business
- **Improves customer satisfaction** through personalized recommendations

**How It Works:**

When a customer initiates a return, instead of immediately processing the refund, the agent:

1. **Analyzes customer reading preferences** from purchase history:
   - Favorite authors (e.g., "Lee Child", "James Patterson")
   - Favorite genres (e.g., "Thriller", "Mystery")
   - Preferred formats (e.g., "Hardcover", "Paperback")
   - Past ratings (5-star purchases indicate strong preferences)

2. **Generates personalized recommendations** using the `get_book_recommendations()` tool:
   - **Priority 1:** Books by favorite authors
   - **Priority 2:** Similar genres to past 5-star purchases
   - **Priority 3:** Popular books in same category

3. **Offers seamless exchange** via `process_exchange()`:
   - Returns original book + places new order in single transaction
   - No payment re-entry required
   - Maintains customer loyalty

**Example Flow:**
```
Customer: "I want to return 'Die Hard' - it wasn't what I expected"
Agent: "I understand. Before processing the return, I noticed you loved
       'Reacher' by Lee Child. Would you like to exchange this for his
       latest release 'The Sentinel'? I can process that immediately."
Customer: "That sounds perfect!"
Agent: [Calls process_exchange()] ✅ Exchange processed, no revenue lost
```

**Metrics Tracked:**
- Exchange conversion rate (target: 30%+)
- Average order value retention
- Customer satisfaction post-exchange

---

### 2. **Precedent-Based Decision System (Automated Exception Handling)**

**Business Impact:**
- **Increases deflection rate** by resolving edge cases without human escalation
- **Reduces operational costs** (fewer tickets to support managers)
- **Maintains compliance** by ensuring exceptions follow past managerial decisions
- **Improves VIP retention** by automating loyalty-based exceptions

**The Problem:**

Standard support systems face a dilemma:
- **Rigid rules** → Alienate VIP customers with edge cases (e.g., "I bought this as a holiday gift 45 days ago")
- **Human escalation** → Every exception requires manager review (slow, expensive)
- **Agent discretion** → Inconsistent decisions, compliance risk

**The Solution:**

A **precedent-based decision graph** that encodes past managerial approvals as queryable precedents. When the agent encounters a policy violation, it:

1. **Checks if customer is VIP** (mandatory via `check_vip_status()`)
2. **Queries the precedent database** (`check_precedents()`) with context tags:
   - `vip` - Customer has VIP status
   - `holiday_gift` - Purchase was Nov-Dec (holiday season)
   - `opened` - Item has been opened/used
   - `book_club` - Customer is Book Club member
   - `late_return` - Beyond 30-day window

3. **Retrieves past decisions** with attribution:
   - Decision ID (e.g., `DEC-002`)
   - Person who made decision (e.g., "Sarah Chen, Senior Manager")
   - Authority level (e.g., "Senior Manager")
   - Outcome (`APPROVE` or `DENY`)
   - Conditions (e.g., "One-time courtesy, 60-day window for holiday gifts")
   - Expiration date (precedents expire after 1 year)

4. **Auto-approves if precedent matches**, citing the previous decision:
   - Agent must acknowledge VIP tier + loyalty
   - Agent must explain exception basis
   - Agent must note any conditions

**Implemented Use Cases:**

**Use Case 1: Holiday Gift Exception**
```
Standard Policy: 30-day return window
Precedent: DEC-002 "Holiday Gift 55 Days Old" → APPROVE

Context:
- Purchase date: December 15, 2025
- Return request date: February 3, 2026 (50 days later)
- Reason: "This was a Christmas gift, I just opened it"

Agent Logic:
1. Detects policy violation (50 > 30 days)
2. Queries precedents with tags: ['late_return', 'holiday_gift']
3. Finds DEC-002: "Extend to 60 days for Nov-Dec purchases"
4. Auto-approves: "While our standard policy is 30 days, holiday
   gifts purchased in November-December have a 60-day window..."

Business Outcome: ✅ Return approved, customer satisfied, no manager time spent
```

**Use Case 2: VIP Exception for Opened Items**
```
Standard Policy: Signed/personalized items must be unopened
Precedent: DEC-003 "Platinum VIP High-Value Collector Opened Signed Edition" → APPROVE

Context:
- Customer: Platinum VIP, 10 years loyalty, $50K lifetime value
- Item: Signed first edition
- Issue: Customer opened the book

Agent Logic:
1. Detects policy violation (signed + opened = non-returnable)
2. MANDATORY: check_vip_status() → Platinum VIP confirmed
3. Queries precedents with tags: ['vip', 'book_club', 'opened', 'signed']
4. Finds DEC-003: "Platinum VIPs, one-time courtesy for opened signed editions"
5. Auto-approves with citation: "Thank you for 10 years as a Platinum
   member. While signed editions are typically final sale once opened,
   we're making an exception as a valued customer. This is a one-time
   courtesy..."

Business Outcome: ✅ VIP retained, no manager escalation, precedent followed
```

**Technical Implementation:**

**Graph Database Schema (Kùzu):**
```
Person (name, role, authority_level)
  → MADE → Decision (id, outcome, reasoning, conditions, expires_at)
    → HAS_CONTEXT → Tag (name, relevance_score)
```

**Query Example:**
```cypher
MATCH (p:Person)-[m:MADE]->(d:Decision)-[ctx:HAS_CONTEXT]->(t:Tag)
WHERE t.name IN ['vip', 'holiday_gift', 'late_return']
  AND d.expires_at > current_date()
  AND d.outcome = 'APPROVE'
ORDER BY ctx.relevance_score DESC
RETURN d.id, d.outcome, d.reasoning, d.conditions, p.name, p.role
LIMIT 3
```

**Governance Controls:**
- Each precedent has an **expiration date** (default: 1 year) to prevent stale policies
- Each precedent tracks **authority level** (Manager vs Senior Manager) for audit trails
- Agent MUST cite precedent ID in response for compliance tracking
- All precedent usages logged to audit trail

**Metrics Tracked:**
- Deflection rate increase (target: +15%)
- Manager escalation reduction (target: -30%)
- Precedent match accuracy (target: 95%+)
- VIP retention rate

**Scalability:**
- Production would use **Human-in-the-Loop** workflow:
  - Novel edge case → Manager reviews → Approves/denies → Creates new precedent
  - Precedents auto-expire after 1 year (requires re-validation)
  - Quarterly policy review based on precedent usage patterns

---

### 3. **Multi-Level Admin View & Session Audit System**

**Business Impact:**
- **Ensures compliance** by providing complete audit trails for regulatory reviews
- **Enables quality assurance** through manager review of agent decisions
- **Improves agent performance** via structured feedback loops
- **Reduces risk** by detecting policy violations or hallucinations early
- **Builds customer trust** through transparent, reviewable decision-making

**The Challenge:**

Traditional AI support systems are "black boxes":
- Managers can't see **why** an exception was approved
- Compliance teams can't audit **what precedents** were cited
- No visibility into **agent reasoning** for policy decisions
- Difficult to identify **performance issues** or training needs
- Hard to investigate **customer complaints** about agent behavior

**The Solution:**

A **dual-layer admin visibility system** that provides both high-level oversight and deep forensic analysis:

---

#### **Layer 1: Chainlit Admin Dashboard (Built-In Session Viewer)**

**Access:** Click "Bookly Admin" profile in chat interface

**Capabilities:**
- **Session ID Lookup:** Enter `SESSION-abc123` to retrieve full conversation
- **Decision Trace View:** See complete timeline of:
  - User messages with timestamps
  - Agent reasoning (internal thought process)
  - Tool calls made (`check_vip_status`, `check_precedents`, etc.)
  - Tool results (VIP status returned, precedents matched)
  - Precedent citations (which DEC-XXX was used)
  - Final decision with justification
- **Quick Audit:** Managers can review edge cases in under 2 minutes
- **Export Capability:** Download session as JSON for compliance records

**Use Cases:**
1. **Customer Complaint Investigation**
   ```
   Customer: "Your agent denied my return even though I'm a VIP!"
   Manager: [Enters session ID] → Sees agent DID check VIP status
             → Found no matching precedent → Correctly denied per policy
             → Can explain to customer or create new precedent if warranted
   ```

2. **Quality Assurance Spot Checks**
   ```
   Weekly Review: Manager selects 10 random sessions with precedent usage
   Goal: Verify precedents were applied correctly
   Action: If misapplied, flag for agent tuning / prompt refinement
   ```

3. **New Employee Training**
   ```
   Use Case: Show new support managers examples of good exception handling
   Method: Pull up 3-5 exemplar sessions showing VIP protocol
   Benefit: Standardizes decision-making across team
   ```

**Technical Implementation:**
- **File:** `admin/decision_reviewer.py`
- **Data Source:** Reads from `logs/decision_audit.log` (JSONL format)
- **Session Grouping:** All events tagged with same `session_id`
- **Access Control:** Admin profile requires authentication (production: RBAC with manager role)

**Example Session View:**
```
SESSION-a7b3c4d1 | Customer: John McClane (CUST-VIP-0001) | 2026-02-17 14:23:15

[14:23:15] User: "I want to return my signed Die Hard book, I opened it"
[14:23:18] Agent Thought: "Need to check order status and customer info..."
[14:23:19] Tool Call: look_up_order("ORD-789")
[14:23:19] Tool Result: {status: "delivered", item: "Die Hard Signed Edition",
                         days_since_purchase: 5, eligible_for_return: true}
[14:23:20] Agent Thought: "Item is signed + opened = policy violation.
                          Must check VIP status before denying..."
[14:23:21] Tool Call: check_vip_status("CUST-VIP-0001")
[14:23:21] Tool Result: {is_vip: true, tier: "Gold", years_active: 5}
[14:23:22] Tool Call: check_precedents(["vip", "book_club", "opened", "signed"])
[14:23:22] Tool Result: {found: true, decision_id: "DEC-003",
                         decision: "APPROVE", person: "Sarah Chen",
                         conditions: "One-time courtesy for Gold+ VIPs"}
[14:23:25] Agent Response: "Thank you for 5 years as a Gold member! While
                           signed editions are typically final sale once opened,
                           we're making an exception. This is a one-time courtesy..."
[14:23:26] Tool Call: execute_order_return("ORD-789", "VIP exception per DEC-003")
[14:23:26] Tool Result: {success: true, transaction_id: "txn_98765"}

DECISION: ✅ APPROVED (Precedent-Based Exception)
PRECEDENT CITED: DEC-003 (Sarah Chen, Senior Manager)
COMPLIANCE: ✅ VIP check performed, precedent correctly applied
```

---

#### **Layer 2: Arize Phoenix Cloud Platform (Deep Observability)**

**Access:**
- **Local Development:** `http://localhost:6006` (Phoenix UI)
- **Production:** Arize Phoenix Cloud SaaS (cloud-hosted)

**Capabilities (Beyond Chainlit Admin):**

1. **Distributed Tracing with Waterfall Views**
   - See exact latency breakdown:
     - LLM inference time (e.g., 2.3s)
     - Tool execution time (e.g., 0.1s per API call)
     - Total turn time (e.g., 3.8s)
   - Identify bottlenecks (slow database queries, API timeouts)

2. **Multi-Session Analytics**
   - **Aggregate Metrics:**
     - Average turns per conversation (target: < 4)
     - Tool usage frequency (`check_precedents` called in 12% of sessions)
     - Escalation rate by category (ORDER_STATUS: 5%, RETURNS: 18%)
     - VIP exception approval rate (target: 80%+ when precedent exists)
   - **Trend Analysis:**
     - Week-over-week deflection rate improvement
     - Cost per conversation (LLM token usage)
     - Category distribution shifts (more returns in December)

3. **Error Detection & Alerting**
   - **Hallucination Detection:**
     - Alert if agent cites non-existent precedent (DEC-999 doesn't exist in DB)
     - Alert if agent approves without calling `check_vip_status()` first
   - **Policy Violations:**
     - Alert if agent approves digital goods return
     - Alert if agent bypasses 30-day window without precedent
   - **Performance Degradation:**
     - Alert if p95 latency > 10 seconds
     - Alert if error rate > 1%

4. **LLM Prompt Analysis**
   - View exact prompts sent to Claude (system + user messages)
   - Compare prompt versions (A/B test new system prompts)
   - Token usage breakdown (input vs output tokens)

5. **Session Replay with Timeline**
   - Visual timeline showing:
     - User input (speech bubble)
     - LLM thinking (brain icon)
     - Tool calls (wrench icon)
     - Tool results (checkmark/X icon)
     - Final response (speech bubble)
   - Click any step to see full JSON payload

6. **Custom Dashboards**
   - **Executive Dashboard:**
     - Total conversations handled today
     - Deflection rate (target: 85%+)
     - Average CSAT score
     - Revenue saved (returns → exchanges)
   - **Agent Performance Dashboard:**
     - Resolution rate by category
     - Average handle time
     - Precedent match accuracy
     - Policy compliance score (99%+)
   - **Cost Optimization Dashboard:**
     - Daily LLM spend
     - Cost per conversation (target: < $0.15)
     - Haiku vs Sonnet usage ratio (95:5 ideal)

**Technical Implementation:**
- **File:** `observability/tracing.py`
- **Framework:** OpenTelemetry SDK with Anthropic instrumentation
- **Session Tagging:** All spans tagged with:
  - `session.id` (groups entire conversation)
  - `user.id` (customer ID for privacy-compliant analytics)
  - `category` (ORDER_STATUS, RETURNS_REFUNDS, GENERAL)
  - `model` (haiku vs sonnet)
  - `precedent_used` (boolean)
- **Data Retention:** 90 days in Phoenix Cloud (configurable)

**Example Phoenix Cloud View:**

```
Session: SESSION-a7b3c4d1
Duration: 8.2s | Turns: 3 | Tools: 5 | Cost: $0.08

Waterfall Trace:
├─ [Router] Classify Question (Haiku)          0.8s  $0.001
├─ [Agent] Turn 1 (Sonnet)                     2.3s  $0.025
│  ├─ look_up_order()                          0.1s
│  └─ get_customer_info()                      0.1s
├─ [Agent] Turn 2 (Sonnet)                     2.1s  $0.023
│  ├─ check_vip_status()                       0.1s
│  └─ check_precedents()                       0.3s  [Graph Query]
└─ [Agent] Turn 3 (Sonnet)                     2.9s  $0.031
   └─ execute_order_return()                   0.2s

Metadata:
- Customer: CUST-VIP-0001 (Gold VIP)
- Category: RETURNS_REFUNDS
- Precedent Used: ✅ DEC-003
- Outcome: APPROVED
- Escalation: ❌ No
```

---

#### **Dual-Layer Architecture Benefits**

| Capability | Chainlit Admin | Phoenix Cloud |
|------------|----------------|---------------|
| **Quick Session Lookup** | ✅ Instant | ✅ Search by ID |
| **Decision Justification** | ✅ Full reasoning | ✅ Plus latency |
| **Precedent Citations** | ✅ Shows DEC-IDs | ✅ Plus relevance scores |
| **Compliance Audit** | ✅ Export JSON | ✅ Bulk export |
| **Performance Metrics** | ❌ Single session only | ✅ Cross-session analytics |
| **Error Alerting** | ❌ Manual review | ✅ Automated alerts |
| **Cost Tracking** | ❌ No visibility | ✅ Token-level breakdown |
| **Trend Analysis** | ❌ No aggregation | ✅ Time-series dashboards |

**Access Control:**
- **Chainlit Admin:** Support managers, compliance team
- **Phoenix Cloud:** Engineering team, operations, executives

---

#### **Real-World Use Cases**

**Use Case 1: Regulatory Audit (GDPR Article 22)**
```
Scenario: Customer requests explanation of automated decision
Regulator: "Show me why you denied this return request"

Process:
1. Manager opens Chainlit Admin → Enters session ID
2. Exports full decision trace as JSON
3. Shows regulator:
   - Agent checked policy (return_policy.md)
   - Item was digital goods (audiobook after download)
   - Policy explicitly states: "ACTION: REJECT digital goods"
   - Agent correctly denied per written policy

Result: ✅ Compliance demonstrated, audit passed
```

**Use Case 2: Agent Performance Improvement**
```
Scenario: Escalation rate increased from 15% → 22% last week

Process:
1. Manager opens Phoenix Cloud → Filters to RETURNS_REFUNDS category
2. Analyzes escalated sessions (22 out of 100)
3. Discovers pattern: Agent is NOT checking precedents before escalating
4. Root cause: New system prompt removed "MANDATORY check_precedents" step
5. Action: Rollback prompt, escalation rate returns to 15%

Result: ✅ Performance restored via data-driven debugging
```

**Use Case 3: New Precedent Creation**
```
Scenario: Novel edge case - VIP wants to return damaged book outside 30-day window

Process:
1. Agent escalates (no matching precedent)
2. Manager opens Chainlit Admin → Reviews session
3. Sees: VIP Gold, 5 years loyalty, book damaged in shipping (not customer fault)
4. Decision: Approve as exception
5. Manager creates DEC-010 in graph:
   - Title: "Shipping Damage Outside Return Window"
   - Tags: ['vip', 'damaged', 'late_return']
   - Outcome: APPROVE
   - Conditions: "Damage must be verified via photo, VIP only"
6. Next time similar case occurs → Agent auto-approves via DEC-010

Result: ✅ Deflection rate improves, manager time freed up
```

**Use Case 4: Cost Optimization**
```
Scenario: LLM spend increased 40% month-over-month

Process:
1. Engineering team opens Phoenix Cloud → Cost dashboard
2. Discovers: Sonnet usage increased from 5% → 25% of conversations
3. Root cause: Router is misclassifying GENERAL questions as RETURNS_REFUNDS
4. RETURNS uses Sonnet (expensive), GENERAL uses Haiku (cheap)
5. Action: Improve router prompt with more examples
6. Sonnet usage drops back to 8%, cost normalized

Result: ✅ 30% cost reduction via targeted prompt tuning
```

---

#### **Security & Governance Features**

**Access Controls:**
- **Role-Based Permissions:**
  - `support_agent` - No admin access (can only chat with customers)
  - `manager` - Chainlit Admin access (can view sessions)
  - `compliance_officer` - Read-only audit log access
  - `engineer` - Phoenix Cloud access (can see prompts/tokens)
  - `executive` - Dashboard-only access (metrics, no PII)

**Data Privacy:**
- **PII Redaction:** Admin views can mask customer names/emails (configurable)
- **Retention Policies:** Sessions auto-deleted after 90 days (GDPR compliance)
- **Audit Trail:** All admin views logged ("Manager Jane viewed SESSION-xyz at 2:30pm")

**Compliance Features:**
- **Immutable Logs:** Audit logs written to append-only storage (tamper-proof)
- **Export Formats:** JSON, CSV, PDF (for regulatory submissions)
- **Search Capabilities:** Filter by date range, customer ID, decision type, precedent used

---

#### **Metrics Tracked via Admin Views**

**Operational Metrics:**
- Sessions reviewed per week (target: 5% random sample)
- Average audit time per session (target: < 2 minutes)
- Compliance violations detected (target: 0)
- Precedent creation rate (new DEC-IDs per month)

**Agent Performance Metrics:**
- Policy compliance score (% decisions that follow policy) - Target: 99%+
- Precedent accuracy (% precedents correctly applied) - Target: 95%+
- Escalation appropriateness (% escalations that were justified) - Target: 90%+
- Customer satisfaction on reviewed sessions (CSAT) - Target: 4.5/5

---

**Summary:**

This dual-layer admin system solves the AI "black box" problem by providing:
1. **Transparency** - Every decision is auditable with full reasoning
2. **Accountability** - Precedent citations trace to specific managers
3. **Performance** - Aggregate analytics identify improvement opportunities
4. **Compliance** - Regulatory-ready audit trails with export capabilities
5. **Continuous Improvement** - Data-driven feedback loop for agent tuning

The combination of **quick session lookup (Chainlit)** + **deep analytics (Phoenix)** enables both tactical operations (investigate customer complaint in 2 minutes) and strategic optimization (identify systemic issues via trend analysis).

---

## Architecture Overview

### System Design
The Enterprise CX Agent implements a **deterministic AI workflow engine** that enforces business logic, governance rules, and escalation protocols while maintaining adaptability through precedent-based decision-making. Unlike traditional chatbots, this system prioritizes auditability, compliance, and controlled autonomy.

**Tech Stack:**
- **LLM Layer:** Anthropic Claude (dual-model: Haiku 4.5 for routing, Sonnet 4.5 for reasoning)
- **UI Framework:** Chainlit (web-based chat interface)
- **Context Store:** Kùzu Graph Database (embedded, for precedent relationships)
- **Observability:** Arize Phoenix + OpenTelemetry (full tracing)
- **Data Layer:** JSON mock services (production-ready schemas)

### High-Level Flow
```
User Input
  → Question Router (Haiku) → Categorize into 3 types
    → SupportAgent (Sonnet) → ReAct Loop
      → Tool Invocation → Service Layer → Policy Enforcement
        → Response Generation
          → Arize Tracing (full audit trail)
```

### Core Components

#### 1. **Question Router** (`router/router.py`)
- **Purpose:** Cost optimization + specialized handling
- **Model:** Claude Haiku 4.5 (temp=0.0 for determinism)
- **Categories:**
  - `ORDER_STATUS` - Order tracking, delivery status
  - `RETURNS_REFUNDS` - Returns, refunds, exchanges
  - `GENERAL` - Policies, account help, FAQs
- **Cost Savings:** 95% reduction in routing overhead ($0.15/1M vs $3/1M tokens)

#### 2. **Support Agent** (`agent/agent.py`)
- **Pattern:** ReAct loop (Reason → Act → Observe)
- **State Management:** Stateless service layer - all state in conversation history
- **Session Tracking:** Unique `SESSION-{uuid}` for audit traceability
- **Tool Orchestration:** 10 specialized tools with category-specific availability

#### 3. **Tool Layer** (`tools/tools.py` + `services/services.py`)
**Available Tools:**
- `look_up_order()` - Order data retrieval
- `get_customer_info()` - Customer profile + VIP status
- `get_policy_info()` - Policy document lookup
- `execute_order_return()` - Process refund
- `check_vip_status()` - VIP tier lookup (mandatory for denials)
- `check_precedents()` - Graph query for exception precedents
- `escalate_order_issue()` - Route to Order Support team
- `escalate_general_question()` - Route to General Support
- `get_book_recommendations()` - AI-powered suggestions
- `process_exchange()` - Return + new order in one transaction

#### 4. **Precedent System** (`data/context_graph_db`)
- **Schema:** Person → MADE → Decision → HAS_CONTEXT → Tag
- **Purpose:** Human-in-the-loop override system
- **Query Pattern:** Match customer context (VIP, book club, opened item) to past managerial decisions
- **Attribution:** Each precedent tracks `person_name`, `person_role`, `authority_level`, `expires_at`
- **Governance:** Agent MUST cite precedent when approving policy exceptions

#### 5. **Observability Layer** (`observability/tracing.py`)
- **Framework:** OpenTelemetry + Arize Phoenix
- **Session Grouping:** All LLM calls tagged with same `session_id`
- **Metadata Tracking:** Model name, category, tool count, turn number, user ID
- **Audit Log:** JSONL format at `logs/decision_audit.log` with structured logging

---

## Conversation Design Decisions

### 1. **Tri-Layered Governance**
**Problem:** AI agents can hallucinate policy exceptions or bypass business rules.

**Solution:** Three enforcement layers:
1. **System Prompt:** Explicit override protocols in natural language
2. **Policy Documents:** Markdown files with `ACTION: REJECT/APPROVE` directives
3. **Tool Constraints:** Mandatory arguments like `policy_check_confirmation`

**Example:** Even if database says `eligible_for_return: true`, agent enforces policy if item is:
- Digital goods (e-books after download)
- Personalized/signed items (unless VIP exception)
- Read/used books
- Outside 30-day window

### 2. **Sentiment-Driven Escalation**
**Design:** Immediate escalation on anger detection, prioritizing customer satisfaction over policy enforcement.

**Triggers:**
- Exclamation marks, ALL CAPS
- Keywords: "ridiculous", "unacceptable", "frustrated"
- Demanding tone: "I demand", "I want to speak to"

**Action:** Call `escalate_order_issue()` BEFORE attempting policy checks, creating ticket with 2-4 hour SLA.

### 3. **VIP Exception Protocol**
**Challenge:** Rigid policies alienate high-value customers.

**Solution:** Precedent-based override system:
1. Detect policy violation (e.g., VIP wants to return opened signed book)
2. MANDATORY `check_vip_status()` call before denial
3. Query `check_precedents()` with context tags (vip, book_club, opened)
4. If precedent found with `decision: APPROVE`, execute override
5. Response MUST include:
   - Acknowledgment of VIP tier + years of loyalty
   - Explanation of exception basis (cite precedent ID)
   - Note any conditions from precedent

**Example Precedents:**
- `DEC-001`: VIP Book Club member opened book → APPROVE (one-time courtesy)
- `DEC-002`: Holiday gift 55 days old → APPROVE (60-day extension for Nov-Dec purchases)
- `DEC-003`: Platinum VIP high-value collector opened signed edition → APPROVE (with conditions)

### 4. **Category-Specific System Prompts**
**Rationale:** Single monolithic prompt creates confusion and context dilution.

**Implementation:** Three specialized prompts in `prompts.py`:
- `ORDER_STATUS_PROMPT` - Focus on speed + personalization
- `RETURNS_REFUNDS_PROMPT` - Detailed workflow with VIP logic
- `GENERAL_PROMPT` - Policy information retrieval

Each prompt includes:
- Role definition
- Mandatory steps (e.g., ALWAYS greet VIP customers by name)
- Tool usage guidelines
- Escalation criteria
- Response format requirements

### 5. **Personalization Layer**
**Features:**
- VIP tier acknowledgment ("Thank you for 5 years of loyalty as a Gold member!")
- Reading preference analysis from purchase history
- Intelligent book recommendations during returns (upsell opportunity)
- Recommendation logic: Favorite authors → Similar genres → Popular alternatives

**Data Model:** Each customer has:
```json
{
  "reading_preferences": {
    "favorite_genres": ["Action", "Thriller"],
    "favorite_authors": ["Lee Child"],
    "preferred_formats": ["Hardcover"]
  },
  "purchase_history": [...] // 5-star ratings, genres, authors
}
```

### 6. **Order ID Normalization**
**Problem:** Users enter order IDs in various formats.

**Solution:** Robust parsing handles:
- `ord-123`, `ORD_123`, `ORD:123`, `ORD 123`, `ORD123`
- Normalizes to canonical: `ORD-123`

### 7. **Complete Audit Trail**
**Design:** Every decision logged with structured metadata for compliance audits.

**Logged Events:**
- Session ID
- User messages
- Agent reasoning
- Tool calls + results
- Precedent usage
- Escalations
- Final decision with justification

**Format:** JSONL at `logs/decision_audit.log` for easy ingestion into analytics systems.

---

## Example System Prompt

**Category: RETURNS_REFUNDS** (Most Complex)

```
You are an expert customer support agent for Bookly, an online book retailer specializing
in rare editions, signed books, and collector items.

MANDATORY WORKFLOW:

STEP 1: PERSONALIZED GREETING
- ALWAYS call get_customer_info() first
- If VIP customer, acknowledge tier and years of loyalty:
  "Hello [Name]! Thank you for [X] years as a [Tier] member..."

STEP 2: ANGER DETECTION
- Monitor for: ALL CAPS, exclamation marks, harsh language ("ridiculous", "unacceptable")
- If detected: IMMEDIATELY escalate_order_issue() with reason "Customer frustrated/angry"
- Do NOT attempt policy enforcement if customer is upset

STEP 3: GATHER ORDER INFORMATION
- Call look_up_order(order_id)
- Verify item details, purchase date, customer sentiment

STEP 4: POLICY ENFORCEMENT HIERARCHY
Check in this order:
1. Timing: Within 30-day window? (ACTION: REJECT if outside)
2. Item Category: Digital goods? Gift cards? (ACTION: REJECT - final sale)
3. Item Condition: Read/used book? (ACTION: REJECT)
4. Signed/Personalized: Opened signed edition? (PROCEED TO STEP 5 - VIP CHECK)

STEP 5: VIP EXCEPTION PROTOCOL
If policy violation detected BUT customer is VIP:
1. Call check_vip_status(customer_id) - MANDATORY before denial
2. Call check_precedents(context_tags=["vip", "book_club", "opened"])
3. If precedent found with decision=APPROVE:
   - Execute override: execute_order_return() with precedent citation
   - Response format:
     "This is typically not eligible under our standard policy for [reason].
     However, as a valued [Tier] customer with [X] years of loyalty, we're
     making an exception. This is a one-time courtesy..."
4. If NO precedent found:
   - Politely deny: "I apologize, but as a signed edition that has been opened..."
   - Offer alternatives: "May I recommend similar titles by [favorite author]?"

STEP 6: BOOK RECOMMENDATIONS (Optional)
If customer is disappointed:
- Call get_book_recommendations(customer_id, exclude_order_id)
- Suggest 2-3 titles based on:
  1. Favorite authors (highest priority)
  2. Favorite genres (medium priority)
  3. Popular books in same category (fallback)

STEP 7: PROCESS RETURN OR EXCHANGE
If approved:
- Return: execute_order_return(order_id, reason="[compliance reason]")
- Exchange: process_exchange(order_id, new_book_id, reason="[compliance reason]")

TONE:
- Warm, empathetic, professional
- Acknowledge customer frustration when denying requests
- Never blame the customer
- Emphasize policy purpose (quality, fairness to all customers)

GOVERNANCE RULES:
- NEVER approve digital goods returns after download
- NEVER approve gift card returns
- NEVER bypass 30-day window unless precedent exists
- ALWAYS log decision reasoning in tool calls
```

---

## Changes to Make This Production-Ready

### 1. **Service Integration Layer**
**Current State:** Mock JSON data in `data/` folder

**Production Changes:**
- Replace `services/services.py` mock functions with real API clients:
  - Order Management System (OMS) API
  - Customer Relationship Management (CRM) API - Salesforce, HubSpot
  - Payment Gateway - Stripe, Braintree
  - Ticketing System - Zendesk, Intercom
  - Inventory Management System
- Implement retry logic with exponential backoff
- Add circuit breakers for service degradation
- Cache frequently accessed data (customer profiles, policy docs) with TTL

### 2. **Authentication & Authorization**
**Current State:** Chainlit default auth (no production security)

**Production Changes:**
- Implement OAuth 2.0 / SAML for SSO
- Role-Based Access Control (RBAC):
  - `customer` - Chat interface
  - `agent` - Admin dashboard (decision viewer)
  - `manager` - Precedent approval system
  - `auditor` - Read-only audit log access
- JWT tokens for API authentication
- Rate limiting per user/session (prevent abuse)

### 3. **Database Migration**
**Current State:** Embedded Kùzu database (single-process)

**Production Changes:**
- **Option 1:** Migrate to Neo4j Enterprise (scalable graph DB)
  - Multi-node cluster
  - Causal clustering for high availability
  - ACID transactions
- **Option 2:** PostgreSQL with pgvector extension
  - Hybrid: Relational tables + graph queries via recursive CTEs
  - Better ops team familiarity
- Implement database connection pooling
- Add read replicas for precedent queries (99% read workload)

### 4. **Observability & Monitoring**
**Current State:** Local Phoenix UI, basic JSONL logging

**Production Changes:**
- Deploy Arize Phoenix Cloud (production tracing)
- Centralized logging: ELK Stack (Elasticsearch, Logstash, Kibana) or Datadog
- Metrics & Alerting:
  - **SLIs:** Response latency (p50, p95, p99), error rate, escalation rate
  - **Alerts:**
    - Latency > 10s (p95)
    - Error rate > 1%
    - Escalation rate > 15% (indicates policy/precedent gaps)
    - Anthropic API quota exhaustion
- Custom dashboards:
  - **Agent Performance:** Resolution rate, avg turns per conversation, tool usage patterns
  - **Business Metrics:** VIP exceptions granted, revenue at risk (returns), customer sentiment distribution
  - **Cost Tracking:** LLM token usage by category, daily spend vs budget

### 5. **Scalability & Performance**
**Current State:** Single-process Chainlit app

**Production Changes:**
- **Horizontal Scaling:**
  - Containerize with Docker
  - Deploy on Kubernetes with auto-scaling (HPA)
  - Target: 100 concurrent conversations per pod
- **Async Processing:**
  - Convert synchronous API calls to async/await (aiohttp)
  - Implement streaming responses for better UX
- **Caching Layer:**
  - Redis for:
    - Policy documents (TTL: 1 hour, invalidate on update)
    - Customer VIP status (TTL: 5 minutes)
    - Book catalog (TTL: 1 day)
  - Precedent query cache (TTL: 1 hour)
- **Load Balancing:**
  - NGINX or AWS ALB for traffic distribution
  - Session affinity (sticky sessions) for conversation continuity

### 6. **Security Hardening**
**Current State:** Development environment, no security measures

**Production Changes:**
- **Data Protection:**
  - Encrypt sensitive data at rest (AES-256)
  - TLS 1.3 for all API communication
  - PII redaction in logs (mask email, phone, credit card numbers)
- **Compliance:**
  - GDPR compliance: Right to deletion, data export
  - PCI DSS if handling payment data
  - SOC 2 Type II audit trail requirements
- **Input Validation:**
  - Sanitize user inputs (prevent injection attacks)
  - Content filtering (detect and block malicious prompts)
- **API Security:**
  - API key rotation policy (90 days)
  - Secrets management: AWS Secrets Manager, HashiCorp Vault
  - Network segmentation (VPC, security groups)

### 7. **Testing & Quality Assurance**
**Current State:** 9 test files, manual testing

**Production Changes:**
- **Expand Test Coverage:**
  - Unit tests: Target 80%+ coverage
  - Integration tests: Full workflow scenarios with real API mocks
  - E2E tests: Selenium/Playwright for UI testing
- **LLM Evaluation:**
  - Golden dataset: 100+ test cases with expected behaviors
  - Automated evals:
    - Policy compliance rate (target: 99%+)
    - Escalation accuracy (target: 95%+)
    - VIP exception correctness (target: 100%)
    - Sentiment detection recall (target: 90%+)
  - Weekly regression testing on model updates
- **Load Testing:**
  - Use Locust or k6 to simulate 1000+ concurrent users
  - Identify bottlenecks (database queries, LLM latency)
- **Chaos Engineering:**
  - Test circuit breakers (kill OMS API, verify graceful degradation)
  - Database failover testing

### 8. **Human-in-the-Loop Workflows**
**Current State:** Precedents pre-populated in graph DB

**Production Changes:**
- **Precedent Approval System:**
  - When agent encounters novel scenario without precedent:
    1. Auto-escalate to manager queue
    2. Manager reviews context + agent's proposed decision
    3. Manager approves/denies with reasoning
    4. System creates new precedent in graph (auto-expires in 1 year)
- **Decision Review Dashboard:**
  - Managers audit random 5% of agent decisions weekly
  - Flag incorrect decisions → trigger model fine-tuning
  - Quarterly policy review based on escalation patterns
- **Feedback Loop:**
  - Post-conversation surveys (CSAT, NPS)
  - Track: "Did the agent resolve your issue?" (target: 85%+)
  - Feed negative feedback into training dataset

### 9. **Cost Optimization**
**Current State:** Dual-model routing (95% savings on classification)

**Production Changes:**
- **Prompt Optimization:**
  - Compress system prompts (remove redundancy)
  - Use Claude's prompt caching (50% cost reduction on repeated context)
- **Model Selection:**
  - A/B test: Haiku vs Sonnet for simple returns (Haiku may suffice)
  - Use Opus 4.6 only for complex VIP exceptions (< 5% of requests)
- **Tool Calling Optimization:**
  - Batch tool calls where possible (get_customer_info + look_up_order in parallel)
  - Implement tool result caching (same order ID queried twice in session)
- **Traffic Shaping:**
  - Implement request queuing during peak hours
  - Offer async email responses for non-urgent queries (reduces concurrent load)

### 10. **Deployment & CI/CD**
**Current State:** Manual startup with Python scripts

**Production Changes:**
- **CI/CD Pipeline:**
  - GitHub Actions or GitLab CI:
    1. Lint (flake8, black)
    2. Run tests (pytest)
    3. Build Docker image
    4. Push to container registry (ECR, GCR)
    5. Deploy to staging
    6. Run smoke tests
    7. Deploy to production (blue-green deployment)
- **Infrastructure as Code:**
  - Terraform or CloudFormation for AWS resources
  - Helm charts for Kubernetes deployments
- **Feature Flags:**
  - LaunchDarkly or custom system
  - Gradual rollout of new features (5% → 25% → 100%)
  - Kill switch for problematic features
- **Rollback Strategy:**
  - Keep last 3 versions deployable
  - Automated rollback on error rate spike (> 5%)

### 11. **Documentation & Onboarding**
**Current State:** README + inline comments

**Production Changes:**
- **Runbooks:**
  - Incident response: "Agent is hallucinating policies" → Rollback + alert AI team
  - Escalation: "Customer complains on Twitter" → Notify PR team + manager override
- **Agent Tuning Guide:**
  - How to add new tools
  - How to modify system prompts
  - How to create precedents
- **API Documentation:**
  - OpenAPI spec for all service endpoints
  - Example requests/responses
- **Training Materials:**
  - Video walkthrough for support managers
  - Decision review dashboard tutorial

### 12. **Compliance & Governance**
**Current State:** Basic audit logging

**Production Changes:**
- **Regulatory Compliance:**
  - GDPR Article 22: Right to explanation for automated decisions
    - Every denial includes human-readable reasoning
    - Option to request human review
  - CCPA: Data deletion workflow
- **AI Safety:**
  - Content moderation: Block offensive/discriminatory responses
  - Bias testing: Ensure VIP exceptions don't discriminate by protected class
  - Transparency: Disclose AI usage to customers ("You're chatting with an AI assistant...")
- **Audit Trail:**
  - Immutable log storage (WORM - Write Once Read Many)
  - 7-year retention for financial transactions (legal requirement)
  - Regular compliance audits (quarterly)

---

## Summary

This Enterprise CX Agent demonstrates production-grade AI system design with:

**Core Strengths:**
- ✅ **Deterministic Governance:** Tri-layered policy enforcement prevents hallucinations
- ✅ **Intelligent Escalation:** Sentiment-driven routing prioritizes customer satisfaction
- ✅ **Adaptability:** Precedent-based exceptions with human oversight
- ✅ **Cost Efficiency:** Dual-model architecture (95% savings on routing)
- ✅ **Full Auditability:** OpenTelemetry tracing + structured logging
- ✅ **Personalization:** VIP recognition, reading preferences, loyalty acknowledgment

**Production Readiness:** The architecture is designed for scale with clear migration paths from mock data to real integrations, embedded databases to distributed systems, and local tracing to enterprise observability.

**Key Insight:** This system solves the "Black Box" problem in Generative AI by making every decision traceable, policy-compliant, and auditable—critical for regulated industries like finance, healthcare, and e-commerce.

---

**Technical Contact:** Nitin Nayar | [Your Email] | [Your GitHub/Portfolio]
**Project Repository:** https://github.com/nitinNayar/enterprise-cx-agent
