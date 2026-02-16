# Submission Guide: Bookly AI Agent

**A Production-Grade AI Customer Support Agent Proof-of-Concept**

---

## Overview

This repository demonstrates a **deterministic, governed, and auditable AI agent** for enterprise customer support. It showcases advanced architectural patterns including:

1. **Dual-Model Cost Optimization** - Router (Haiku) + Agent (Sonnet)
2. **Graph-Based Precedent System** - Human decisions as "case law"
3. **Tri-Layered Governance** - Database → Policy → Precedents
4. **Category-Based Specialization** - Filtered tools per question type
5. **Complete Observability** - OpenTelemetry + Phoenix tracing

---

## Deliverables

### 1. Agent Design Document
**Location:** `AGENT_DESIGN_DOCUMENT.md`

**Contents:**
- ✅ Architecture Overview (system components, data flow)
- ✅ Conversation & Decision Design (intent recognition, when to answer/ask/act)
- ✅ Hallucination & Safety Controls (tool constraints, precedent retrieval, audit trail)
- ✅ Example System Prompt (excerpt from 1100+ line production prompt)
- ✅ Production Readiness (gaps, tradeoffs, roadmap)

**Key Sections:**
- **Section 1:** High-level architecture diagram with component breakdown
- **Section 2:** 13-step SOP workflow with decision logic examples
- **Section 3:** 7 hallucination prevention mechanisms with code examples
- **Section 4:** Real system prompt excerpt (RETURNS_REFUNDS category)
- **Section 5:** Production gaps analysis (12 categories, 50+ items)

---

### 2. GitHub Repository with Run Instructions

**Repository:** https://github.com/nitinnayar/enterprise-cx-agent

#### Quick Start (5 minutes)

**Prerequisites:**
- Python 3.10+
- Anthropic API Key

**Installation:**
```bash
# Clone repository
git clone https://github.com/nitinnayar/enterprise-cx-agent.git
cd enterprise-cx-agent

# Install dependencies
pip install -r requirements.txt

# Initialize Context Graph (precedent database)
python scripts/init_graph.py

# Configure API key
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." > .env
```

**Run the System:**

**Terminal 1: Start Observability (Arize Phoenix)**
```bash
python -m phoenix.server.main serve
```
→ Open http://localhost:6006 to view traces

**Terminal 2: Start Agent (Chainlit UI)**
```bash
chainlit run app.py -w
```
→ Open http://localhost:8000 to chat with agent

**Select Chat Profile:**
- **"Bookly Support"** - Customer-facing agent
- **"Bookly Admin"** - Decision trace viewer (for investigating sessions)

---

#### Demo Scenarios (15 minutes)

**Scenario 1: Simple Return (Happy Path)**
```
User: I want to return my order ORD-123
Agent: [Looks up order, greets customer]
       "Hello John McClane! Thank you for being a valued Gold VIP customer
       for 5 years. I can help you with your return for order ORD-123 -
       'Die Hard: The Official Movie Novelization' (Hardcover).

       Could you please tell me why you'd like to return this item?"
User: Changed my mind, book is unopened
Agent: [Checks policy, approves return]
       "Good news! Your return is approved ✓"
```

**Scenario 2: Late Return (Policy Denial)**
```
User: I need to return order ORD-456 (purchased 45 days ago)
Agent: [Checks 30-day policy, automatically checks VIP status]
       Policy says DENY (outside window)
       Customer is NOT VIP
       No precedent found
       → Politely denies with explanation
```

**Scenario 3: VIP Exception (The "Wow" Moment) ⭐**
```
User: I want to return ORD-777 (I'm a Book Club Platinum member)
Agent: [Looks up order: "The Terminator Files" - Signed Edition]
       [Gets customer: Sarah Connor - Platinum VIP, 10 years, $50k]
       "Hello Sarah Connor! Thank you for being a valued Platinum VIP
       customer for 10 years..."
       [Asks about condition]
User: I opened it and read the first chapter
Agent: [Policy says DENY - read book, signed edition]
       [Automatically checks VIP status - already knows]
       [Queries precedent graph: "vip book read signed book_club"]
       [Graph returns: DEC-2024-001 by Sarah Chen, VP Customer Experience]
       [Precedent says: APPROVE with conditions]

       "✅ Return approved and processed!

       **Important: This is a special exception to our standard policy**

       'The Terminator Files' would normally not be eligible since you
       opened and read the book, and signed editions must be in pristine
       condition. However, as a valued Platinum customer, we're making an
       exception in this case.

       **Please note:** This is a one-time courtesy exception and may not
       apply to future requests. This exception is limited to one read
       book return per customer per year.

       We truly appreciate your 10 years of loyalty!"
```

**Scenario 4: Observability (View Decision Trace)**
1. Open Phoenix UI: http://localhost:6006
2. Click **"Traces"** tab
3. Find Sarah Connor trace (ORD-777)
4. View waterfall:
   - Tool call: `look_up_order`
   - Tool call: `get_customer_info`
   - Tool call: `get_policy_info`
   - Tool call: `check_vip_status`
   - Tool call: `check_precedents` ← **Precedent query!**
   - Tool result: DEC-2024-001, Sarah Chen, VP
   - Tool call: `execute_order_return`
   - Final response with VIP exception notice

---

### 3. Screen Recording (Alternative to Live Demo)

**Video:** See `docs/DEMO_GUIDE.md` for full demo script

**2-Minute Demo Structure:**
1. **00:00-00:30** - Show architecture diagram, explain dual-model routing
2. **00:30-01:00** - Demo simple return (happy path)
3. **01:00-01:30** - Demo VIP exception (precedent-based approval)
4. **01:30-02:00** - Show Phoenix trace, explain audit trail & attribution

**Key Points to Hit:**
- ✅ Deterministic decision-making (Temperature 0.0)
- ✅ Tool-constrained execution (cannot hallucinate)
- ✅ Policy-grounded reasoning (reads markdown files)
- ✅ Automatic VIP checks (proactive exception handling)
- ✅ Precedent-based approvals (graph query with attribution)
- ✅ Complete audit trail (OpenTelemetry tracing)

---

## Key Technical Features

### 1. Intelligent Question Routing

**Problem:** Using Sonnet for all queries is expensive
**Solution:** Haiku classifies questions, Sonnet handles complex reasoning

```
User Question → Router (Haiku) → Category
                                     ↓
                    ┌────────────────┼────────────────┐
                    │                │                │
              ORDER_STATUS    RETURNS_REFUNDS      GENERAL
              (3 tools)       (9 tools - full)    (2 tools)
                    │                │                │
                    └────────────────┼────────────────┘
                                     ↓
                            Agent (Sonnet)
```

**Cost Savings:**
- Routing: $0.15/1M tokens (Haiku)
- Reasoning: $3/1M tokens (Sonnet)
- Overhead: +$4.50/month for 300K queries
- Benefit: Better organization, specialized handling, scalable architecture

### 2. Tri-Layered Governance

**Layer 1: Database (Basic Eligibility)**
```json
{"order_id": "ORD-123", "eligible_for_return": true}
```

**Layer 2: Policy Documents (Rules as Code)**
```markdown
# Return Policy
Physical books must be:
- Returned within 30 days of delivery
- In unread, resellable condition
```

**Layer 3: Context Graph (Human Precedents)**
```cypher
(Person:Sarah_Chen)-[:MADE]->(Decision:DEC-2024-001)-[:HAS_CONTEXT]->(Tag:vip)
```

**Decision Flow:**
```
IF Database says "eligible" BUT Policy says "deny" → Policy WINS
IF Policy says "deny" BUT customer is VIP → Check precedent graph
IF precedent found → APPROVE with conditions
ELSE → Enforce policy OR escalate to human
```

### 3. Precedent-Based Exception Handling

**Problem:** Rigid policies frustrate VIP customers
**Solution:** Store human decisions in graph database, query for similar cases

**Precedent Structure:**
```json
{
  "decision_id": "DEC-2024-001",
  "decision_title": "Book Club Platinum VIP - Read Book Exception",
  "outcome": "APPROVE",
  "reasoning": "Book Club Platinum members with demonstrated loyalty (10+ years, $25k+) may return read books as one-time courtesy",
  "conditions": "One-time exception only. Limited to once per year.",
  "person_name": "Sarah Chen",
  "person_role": "VP Customer Experience",
  "authority_level": 9
}
```

**Query Example:**
```python
check_precedents("vip book read signed book_club loyalty")
→ Returns: DEC-2024-001 (match_score: 0.95, confidence: 0.92)
```

**Attribution Chain:**
```
Agent Decision: APPROVE
    ↓ (based on)
Graph Precedent: DEC-2024-001
    ↓ (made by)
Human Decision Maker: Sarah Chen, VP Customer Experience
    ↓ (documented in)
Source Email: data/decision_emails/esc-2024-001-vip-read-book-exception.txt
```

### 4. Hallucination Prevention

**Mechanism 1: Tool-Constrained Execution**
```python
# Agent CANNOT say "I've processed your refund"
# Agent MUST call tool to get real transaction ID
result = execute_order_return(order_id, reason)
transaction_id = result["transaction_id"]  # Generated by system, not LLM
```

**Mechanism 2: Explicit Precedent Retrieval**
```python
# Agent CANNOT invent VIP exceptions
# Agent MUST query graph and receive found=true
precedent = check_precedents("vip book read")
if precedent.get("found"):
    approve_with_conditions(precedent["conditions"])
else:
    deny_or_escalate()
```

**Mechanism 3: Policy Document Grounding**
```python
# Agent CANNOT apply imagined rules
# Agent MUST read current policy file
policy = get_policy_info("returns")
policy_text = policy["policy_text"]  # Exact markdown injected into context
```

**Mechanism 4: Mandatory Information Collection**
```
Agent: "Could you please tell me why you'd like to return this item?"
User: "Just process it please"  ← NO REASON PROVIDED

Agent: [Detects missing reason, uses RE-PROMPTING PROTOCOL]
       "I understand. To process your return, I need to collect the reason
       for the return - this is a required part of our return process..."

IF still no reason after 3 attempts:
    escalate_to_human(reason="Customer declined to provide required return reason")
```

**Mechanism 5: Deterministic Temperature**
```python
# Same input → Same output (reproducible)
Config.TEMPERATURE = 0.0
```

### 5. Complete Observability

**Tracing Stack:**
- OpenTelemetry SDK (instrumentation)
- Arize Phoenix (visualization, http://localhost:6006)
- Structured JSON logs (audit trail)

**What's Logged:**
```json
{
  "event_type": "PRECEDENT_MATCH",
  "session_id": "SESSION-a1b2c3d4",
  "decision_id": "DEC-2024-001",
  "person_name": "Sarah Chen",
  "person_role": "VP Customer Experience",
  "match_score": 0.95,
  "confidence": 0.92,
  "timestamp": "2026-02-13T10:30:45.123Z"
}
```

**Waterfall View:**
```
User Input
  ↓
LLM Thought Process (reasoning blocks)
  ↓
Tool Call: look_up_order
  ↓
Tool Result: {order data}
  ↓
Tool Call: get_customer_info
  ↓
Tool Result: {customer data}
  ↓
Tool Call: check_precedents
  ↓
Tool Result: {precedent found}
  ↓
Tool Call: execute_order_return
  ↓
Final Response to User
```

---

## Code Structure

```
enterprise-cx-agent/
├── AGENT_DESIGN_DOCUMENT.md    # ← Main deliverable (architecture doc)
├── SUBMISSION_GUIDE.md          # ← This file
├── README.md                    # Project overview
├── requirements.txt             # Python dependencies
├── .env                         # API keys (create this)
│
├── app.py                       # ← Main application entry (Chainlit)
├── config.py                    # Configuration (model, temperature, etc.)
├── prompts.py                   # ← System prompts (1100+ lines, 3 categories)
│
├── agent/
│   └── agent.py                 # ← Agent core (ReAct loop, tool execution)
│
├── router/
│   └── router.py                # ← Question classifier (Haiku routing)
│
├── services/
│   └── services.py              # ← Backend integrations (mocked for demo)
│                                #    - look_up_order, execute_refund, check_precedents, etc.
│
├── tools/
│   └── tools.py                 # Tool schemas (9 tools with descriptions)
│
├── data/
│   ├── mock_orders.json         # Mock order data
│   ├── mock_customers.json      # Mock customer data
│   ├── mock_books.json          # Mock book recommendations
│   ├── context_graph_db/        # Kùzu graph database (precedents)
│   └── decision_emails/         # Source emails for precedents
│
├── policies/
│   ├── return_policy.md         # ← Policy documents (markdown)
│   ├── shipping_policy.md
│   └── privacy_policy.md
│
├── scripts/
│   ├── init_graph.py            # Initialize precedent graph database
│   └── debug_graph.py           # Query graph for debugging
│
├── tests/
│   ├── test_specialized_routing.py
│   ├── test_order_id_normalization.py
│   ├── test_return_reason_mandatory.py
│   └── test_timing_validation.py
│
├── docs/
│   ├── DEMO_GUIDE.md            # Full demo script with scenarios
│   ├── TECHNICAL_OVERVIEW.md    # Detailed technical documentation
│   └── [other documentation]
│
└── logs/                        # Generated logs (audit trail)
    ├── console.log              # Application logs
    └── decision_audit.log       # Audit logs (JSON structured)
```

**Key Files to Review:**

1. **`AGENT_DESIGN_DOCUMENT.md`** - Main submission document
2. **`prompts.py`** - System prompts showing decision logic
3. **`agent/agent.py`** - ReAct loop implementation
4. **`services/services.py`** - Tool implementations & precedent query
5. **`router/router.py`** - Cost optimization via Haiku routing
6. **`data/decision_emails/`** - Source documents for precedents

---

## Evaluation Criteria

### 1. Architecture & Design ✅

**What We Demonstrate:**
- ✅ Clear separation of concerns (Router → Agent → Tools → Services)
- ✅ Dual-model architecture for cost optimization
- ✅ Graph-based precedent system for adaptive governance
- ✅ Category-based specialization with filtered tools
- ✅ Complete observability with OpenTelemetry

**Document Reference:** Section 1 of `AGENT_DESIGN_DOCUMENT.md`

### 2. Conversation & Decision Design ✅

**What We Demonstrate:**
- ✅ Intent recognition via two-stage classification (Router + Agent)
- ✅ 13-step SOP workflow with mandatory stops
- ✅ Decision logic: when to answer, ask follow-up, or take action
- ✅ Precedent-based exception handling (automatic VIP checks)
- ✅ Conversational flow with greeting protocol

**Document Reference:** Section 2 of `AGENT_DESIGN_DOCUMENT.md`
**Code Reference:** `prompts.py` lines 1-1100

### 3. Hallucination & Safety Controls ✅

**What We Demonstrate:**
- ✅ Tool-constrained execution (cannot invent actions)
- ✅ Explicit precedent retrieval (cannot invent exceptions)
- ✅ Policy document grounding (reads markdown files)
- ✅ Mandatory information collection (re-prompting protocol)
- ✅ Deterministic temperature (0.0 for consistency)
- ✅ Escalation safety valve (angry customers)
- ✅ Complete audit trail (attribution chain)

**Document Reference:** Section 3 of `AGENT_DESIGN_DOCUMENT.md`
**Code Reference:** `agent/agent.py` lines 134-385 (tool execution with logging)

### 4. Production Readiness ✅

**What We Demonstrate:**
- ✅ Clear understanding of demo scope vs. production requirements
- ✅ Identified 12 production gap categories (50+ specific items)
- ✅ Architectural tradeoffs table with production alternatives
- ✅ Cost analysis & ROI calculation
- ✅ Testing strategy (unit, integration, E2E)

**Document Reference:** Section 5 of `AGENT_DESIGN_DOCUMENT.md`

---

## Assumptions & Tradeoffs

### Assumptions

1. **Single-Tenant Design**
   - Assumption: Demo for one bookshop
   - Production: Multi-tenant with row-level security

2. **Mock Backend Services**
   - Assumption: Focus on agent logic, not integration complexity
   - Production: Real APIs (Shopify, Stripe, Zendesk, etc.)

3. **Local Graph Database**
   - Assumption: Embedded Kùzu for simplicity
   - Production: Neo4j with clustering, backups

4. **English Language Only**
   - Assumption: Single-language demo
   - Production: Multi-language support via i18n

5. **No Authentication**
   - Assumption: Demo environment, trusted users
   - Production: OAuth 2.0, SSO, RBAC

### Tradeoffs

| Decision | Benefit | Cost | Production Alternative |
|----------|---------|------|------------------------|
| **Kùzu embedded DB** | Zero setup, fast iteration | Not distributed | Neo4j (scalable graph) |
| **Mock services** | Focus on agent logic | No real integrations | Real API connections |
| **Chainlit UI** | Rapid prototyping | Limited customization | React + WebSocket UI |
| **Synchronous tools** | Simple debugging | Sequential execution | Async/parallel calls |
| **Temperature 0.0** | Deterministic output | No creativity | Higher temp for recommendations |
| **Local file storage** | Simple for demo | Not scalable | S3/GCS for policies |

---

## What Makes This Different?

### Traditional AI Chatbot:
- ❌ Black box (no visibility)
- ❌ Hallucinations (invents information)
- ❌ Inconsistent (different response each time)
- ❌ Not governed (can't enforce policies)
- ❌ Can't learn (requires retraining)

### Our Solution:
- ✅ **Transparent** - Complete audit trail
- ✅ **Tool-Constrained** - Cannot hallucinate actions
- ✅ **Deterministic** - Same input = same output
- ✅ **Governed** - Tri-layered enforcement
- ✅ **Adaptive** - Learns from human decisions

### Innovation Highlights:
1. **Dual-Model Architecture** - Cost optimization through routing
2. **Context Graph** - Precedent-based "case law" system
3. **Attribution Chain** - Every decision → human decision-maker
4. **Category-Based Specialization** - Right tools + prompt per question
5. **Mandatory Information Collection** - Prevents hallucination

---

## Questions & Answers

**Q: How do you prevent the agent from hallucinating VIP exceptions?**
A: Tool-based architecture. Agent can ONLY approve exceptions if `check_precedents()` returns `found=true`. It cannot make up decisions. Every precedent includes attribution (person_name, person_role, decision_id).

**Q: What if a precedent doesn't exist?**
A: Agent either denies (if policy says no) or offers to escalate to human for review. The human decision can then become a new precedent (added via admin UI in production).

**Q: Can precedents contradict each other?**
A: Graph query ranks by relevance score and decision maker authority. VP decisions > Director > Manager. Most relevant + highest authority wins.

**Q: How do you ensure the agent follows the workflow?**
A: Explicit instructions in system prompt with "MUST", "MANDATORY", "STOP and wait" keywords. Temperature 0.0 ensures consistent execution. Extensive testing validates SOP adherence.

**Q: Is this production-ready?**
A: This is a proof-of-concept demonstrating core architectural patterns. Production needs authentication, real APIs, security hardening, multi-tenancy, monitoring, etc. See Section 5 of design document for full gap analysis.

---

## Contact & Support

**GitHub:** https://github.com/nitinnayar/enterprise-cx-agent
**Issues:** https://github.com/nitinnayar/enterprise-cx-agent/issues
**Documentation:** See `docs/` directory for detailed guides

**Created by:** Nitin Nayar
**Date:** 2026-02-13
**License:** MIT (see LICENSE file)

---

## Thank You!

Thank you for reviewing this submission. This project demonstrates:

✅ **Technical Depth** - Advanced AI architecture with novel patterns
✅ **Practical Value** - Solves real enterprise CX problems
✅ **Production Awareness** - Clear understanding of demo vs. production
✅ **Thorough Documentation** - Design decisions explained with reasoning
✅ **Working Prototype** - Fully functional, runnable system

We look forward to discussing the architecture, design decisions, and production pathway in detail.
