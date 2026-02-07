# Technical Overview: Enterprise CX Agent

**Last Updated:** February 2026
**Version:** 1.0
**Status:** Proof of Concept / Demo

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Conversation Types & Handling](#conversation-types--handling)
6. [Technical Deep Dives](#technical-deep-dives)
7. [Deployment & Dependencies](#deployment--dependencies)

---

## Executive Summary

The **Enterprise CX Agent** is a deterministic AI workflow system designed to handle customer support interactions with enterprise-grade governance, traceability, and adaptability. Unlike traditional "black box" chatbots, this system operates as a **State-Based Workflow Engine** that follows a strict Standard Operating Procedure (SOP) while maintaining the ability to apply nuanced, human-approved exceptions through a precedent-based decision system.

### Key Capabilities

- **Deterministic Decision-Making:** Follows explicit business logic with policy-as-code enforcement
- **Multi-Layered Governance:** Policy documents override database flags; precedents override policies
- **Precedent-Based Adaptability:** Uses a graph database to apply "case law" from historical human decisions
- **Complete Auditability:** Every decision is traced, logged, and attributable to either policy or human precedent
- **Risk Detection & Escalation:** Automatically identifies angry customers and escalates appropriately
- **VIP Exception Handling:** Proactively checks for VIP status and applies appropriate precedents

---

## System Architecture

> **📊 Interactive Diagrams:** For detailed Mermaid diagrams (system architecture, data flow, state machines, etc.), see [docs/diagrams/ARCHITECTURE.md](diagrams/ARCHITECTURE.md)

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Chainlit UI (localhost:8000)                            │   │
│  │  • TrueCart Support Profile (Customer Facing)            │   │
│  │  • TrueCart Admin Profile (Decision Trace Viewer)        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Agent Core (agent/agent.py)                             │   │
│  │  • SupportAgent class                                    │   │
│  │  • ReAct Loop (Reason + Action)                          │   │
│  │  • Conversation History Management                       │   │
│  │  • Session Tracking                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tool Router (tools/tools.py)                            │   │
│  │  • 7 Tool Definitions (look_up_order, get_policy_info,   │   │
│  │    execute_order_return, escalate_to_human,              │   │
│  │    check_vip_status, check_precedents, get_customer_info)│   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Service Layer (services/services.py)                    │   │
│  │  • EnterpriseServices (Stateless)                        │   │
│  │  • Tool Implementation Logic                             │   │
│  │  • Graph Database Queries                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA & INTEGRATION LAYER                      │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ Mock OMS     │ Policy Docs  │ Context Graph│ Audit Logs   │  │
│  │ (JSON)       │ (.md files)  │ (Kùzu DB)    │ (JSONL)      │  │
│  │              │              │              │              │  │
│  │ Orders &     │ Return       │ Person →     │ Structured   │  │
│  │ Customers    │ Shipping     │ Decision →   │ Decision     │  │
│  │              │ Privacy      │ Tags         │ Traces       │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Arize Phoenix (localhost:6006)                          │   │
│  │  • OpenTelemetry Traces                                  │   │
│  │  • Agent Decision Waterfall Visualization                │   │
│  │  • Tool Call Inspection                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Headless Agent Pattern:** UI is decoupled from agent logic
2. **Stateless Service Layer:** All state lives in agent conversation history
3. **Tool-Based Extensibility:** New capabilities added via tool schema
4. **Graph-First Decision Model:** Precedents stored as graph relationships, not flat rules
5. **Observability by Design:** Every API call and decision is traced

---

## Core Components

### 1. Agent Core (`agent/agent.py`)

**Purpose:** Orchestrates the conversation loop and decision-making process.

**Key Features:**
- **ReAct Loop:** Continuous Reason → Action → Observation cycle
- **Session Management:** Tracks conversation state and generates unique session IDs
- **Tool Orchestration:** Interprets Claude's tool calls and routes to service layer
- **Audit Logging:** Records every decision, tool call, and precedent usage

**Implementation Details:**
```python
class SupportAgent:
    - self.client: Anthropic API client
    - self.messages: List of conversation history
    - self.session_id: Unique session identifier
    - self.precedent_used: Tracks if a precedent was applied

    def run(user_input):
        # Main ReAct loop:
        while True:
            response = call_claude_with_tools()
            if stop_reason == "end_turn":
                return final_text
            elif stop_reason == "tool_use":
                results = execute_tools()
                add_to_history(results)
                # Loop continues...
```

**Exit Conditions:**
- `end_turn`: Claude has final answer → return to user
- `tool_use`: Claude needs more information → execute tools and continue

### 2. Tool System (`tools/tools.py`)

**Purpose:** Defines the agent's available actions as structured tool schemas.

**Available Tools:**

| Tool Name | Purpose | When Used |
|-----------|---------|-----------|
| `look_up_order` | Fetch order details from OMS | **MANDATORY** first step for any order inquiry |
| `get_customer_info` | Retrieve customer details | **MANDATORY** immediately after order lookup for personalized greeting |
| `get_policy_info` | Read policy documents | Before any refund decision |
| `check_vip_status` | Verify VIP/high-value status | **AUTOMATIC** when policy denies a return |
| `check_precedents` | Query graph for similar cases | When VIP customer faces policy denial |
| `execute_order_return` | Process refund | Only after policy verification |
| `escalate_to_human` | Create support ticket | Angry customers or edge cases |

**Tool Constraints:**
- Tools have required parameters (enforced by schema)
- `execute_order_return` requires explicit policy confirmation
- Tools return structured JSON responses

### 3. Service Layer (`services/services.py`)

**Purpose:** Stateless business logic that executes tool functionality.

**Key Services:**

```python
class EnterpriseServices:
    # Data Access
    @staticmethod
    def look_up_order(order_id) -> dict
    @staticmethod
    def get_customer_info(customer_id) -> dict
    @staticmethod
    def check_vip_status(customer_id) -> dict

    # Policy & Precedents
    @staticmethod
    def get_policy_info(policy_type) -> dict
    @staticmethod
    def check_precedents(query_tags_str) -> dict

    # Actions
    @staticmethod
    def execute_refund(order_id, reason) -> dict
    @staticmethod
    def escalate_to_human(order_id, reason) -> dict

    # Audit
    @staticmethod
    def record_decision_to_ledger(...) -> dict
```

**Implementation Notes:**
- All methods are static (no instance state)
- Each method logs to audit system
- Graph queries use Cypher-like syntax for Kùzu
- Mock data loaded from JSON files (`data/mock_orders.json`, `data/mock_customers.json`)

### 4. Context Graph (`data/context_graph_db`)

**Purpose:** Embedded graph database storing precedent decisions as relationships.

**Technology:** Kùzu (embedded graph database, similar to DuckDB but for graphs)

**Schema:**

```
┌─────────┐      MADE       ┌──────────┐    HAS_CONTEXT    ┌──────┐
│ Person  │ ──────────────> │ Decision │ ───────────────> │ Tag  │
└─────────┘                 └──────────┘                   └──────┘
    │                            │
    │                            │ APPLIES_TO
    │                            ↓
    │                       ┌─────────┐
    └───────────────────────│ Product │
                            └─────────┘
```

**Node Types:**
- **Person:** Decision makers (e.g., "Sarah Chen, VP Customer Experience")
- **Decision:** Historical rulings with reasoning and conditions
- **Tag:** Context keywords (e.g., "vip", "socks", "opened", "electronics")
- **Product:** Product categories affected by decisions

**Relationship Types:**
- **MADE:** Person → Decision (who made the decision)
- **HAS_CONTEXT:** Decision → Tag (what context applies)
- **APPLIES_TO:** Decision → Product (which products affected)
- **CITES:** Decision → Decision (precedent citations)

**Query Pattern:**
```cypher
MATCH (p:Person)-[m:MADE]->(d:Decision)-[ctx:HAS_CONTEXT]->(t:Tag)
WHERE t.name IN ['vip', 'socks', 'return']
  AND d.expires_at = 'NEVER'
  AND d.confidence_score >= 0.7
WITH p, d, SUM(ctx.relevance_score) AS score
ORDER BY score DESC, p.authority_level DESC
LIMIT 1
RETURN d.id, d.title, d.outcome, d.reasoning, p.name, p.role
```

**Seeded Data:**
- ESC-2024-001: VIP Socks Exception (Sarah Chen, VP CX)
- ESC-2024-002: Holiday Gift Late Return (Michelle Rodriguez, Director of Operations)
- ESC-2024-003: Opened Tech High Value (Jennifer Park, Director CX)

### 5. System Prompt (`config.py`)

**Purpose:** The "Standard Operating Procedure" that governs agent behavior.

**Key Sections:**

1. **Prime Directive:** Policy overrides database flags
2. **Exception Protocol:** VIP customers get automatic precedent checks
3. **Customer Greeting Protocol:** Personalized greetings based on tenure
4. **Decision Attribution:** How to cite precedents to customers
5. **Standard Operating Procedure:** Step-by-step workflow

**Prompt Engineering Techniques:**
- Explicit MANDATORY instructions (capitalized)
- Examples of correct/incorrect behavior
- Policy-specific questions for different product categories
- Required response templates for exceptions
- Warning about not assuming item state

**Critical Rules:**
- NEVER skip customer greeting after order lookup
- ALWAYS check VIP status on policy denials
- DO NOT mention decision maker names to customers (internal only)
- STOP after greeting and wait for customer response
- DO NOT assume item condition without customer confirmation

### 6. Logging System (`logging_config.py`)

**Purpose:** Dual logging system for development and audit trails.

**Two Log Streams:**

**Console Logs** (`logs/console.log`):
- Human-readable text format
- For development and debugging
- Standard Python logging format

**Audit Logs** (`logs/decision_audit.log`):
- JSONL format (one JSON object per line)
- For monitoring tools and compliance
- Structured with decision attribution

**Audit Event Types:**
```python
'USER_MESSAGE'          # Customer input
'AGENT_RESPONSE'        # Agent output (thinking or final)
'TOOL_CALL'            # Tool invocation
'TOOL_RESULT'          # Tool output
'PRECEDENT_QUERY'      # Graph search initiated
'PRECEDENT_MATCH'      # Precedent found
'NO_PRECEDENT'         # No precedent found
'AGENT_USING_PRECEDENT' # Precedent will be applied
'PRECEDENT_CITED'      # Precedent mentioned to customer
'AGENT_DECISION'       # Final decision (APPROVE/DENY/ESCALATE)
```

**Sample Audit Entry:**
```json
{
  "timestamp": "2026-02-07T10:30:45.123Z",
  "level": "INFO",
  "logger": "DecisionAudit",
  "message": "Agent approved return",
  "session_id": "SESSION-a1b2c3d4",
  "decision_id": "DEC-2024-001",
  "person_id": "PER-001",
  "person_name": "Sarah Chen",
  "person_role": "VP, Customer Experience",
  "order_id": "ORD-777",
  "agent_decision": "APPROVE",
  "event_type": "AGENT_DECISION"
}
```

### 7. Observability (`observability/tracing.py`)

**Purpose:** Real-time visualization of agent decision-making process.

**Technology Stack:**
- **OpenTelemetry:** Industry-standard tracing protocol
- **Arize Phoenix:** Observability UI specifically designed for LLM applications
- **AnthropicInstrumentor:** Auto-instrumentation for Anthropic API calls

**What Gets Traced:**
- Every API call to Claude
- Token usage per request
- Tool call decisions
- Tool execution duration
- Multi-turn conversation flows

**Access:** `http://localhost:6006` (Phoenix UI)

**Use Cases:**
- Debugging agent behavior
- Measuring latency
- Identifying bottlenecks
- Understanding decision paths
- Demonstrating system internals

### 8. UI Layer (`app.py`)

**Purpose:** User interface for both customers and administrators.

**Framework:** Chainlit (async chat framework for AI agents)

**Two Chat Profiles:**

**TrueCart Support** (Customer-Facing):
- Standard customer support interface
- Initializes SupportAgent instance
- Handles order inquiries and returns
- Displays agent responses in real-time

**TrueCart Admin** (Internal Tool):
- Decision trace viewer
- Input: Session ID (e.g., `SESSION-a1b2c3d4`)
- Output: Complete audit trail for that session
- Shows which precedents were used
- Reveals decision attribution

**Key Functions:**
```python
@cl.on_chat_start
async def start():
    # Route based on selected profile
    if profile == "TrueCart Admin":
        # Admin mode
    else:
        # Initialize customer agent
        cl.user_session.set("agent", SupportAgent())

@cl.on_message
async def main(message):
    # Route message handling
    if mode == "admin":
        await handle_admin_query(message.content)
    else:
        response = agent.run(message.content)
```

---

## Data Flow

> **📊 Detailed Diagrams:** See [Data Flow Sequence Diagram](diagrams/ARCHITECTURE.md#data-flow---complete-request-lifecycle) for a visual representation of the complete request lifecycle with all API calls and database queries.

### Complete Request-Response Flow

```
1. USER INPUT
   │
   ├─→ Chainlit UI captures message
   │
   └─→ app.py routes to SupportAgent.run()
        │
        ├─→ Append to conversation history
        │   │
        │   └─→ AUDIT LOG: USER_MESSAGE
        │
2. REACT LOOP BEGINS
   │
   ├─→ Call Anthropic API with:
   │   • System prompt (SOP)
   │   • Conversation history
   │   • Tool schema
   │   │
   │   └─→ OBSERVABILITY: OpenTelemetry trace starts
   │
3. CLAUDE RESPONSE
   │
   ├─→ If stop_reason == "tool_use":
   │   │
   │   ├─→ AUDIT LOG: AGENT_RESPONSE (thinking)
   │   │
   │   ├─→ Extract tool calls
   │   │
   │   ├─→ For each tool:
   │   │   │
   │   │   ├─→ AUDIT LOG: TOOL_CALL
   │   │   │
   │   │   ├─→ Route to EnterpriseServices
   │   │   │   │
   │   │   │   ├─→ look_up_order?
   │   │   │   │   └─→ Load from MOCK_ORDERS
   │   │   │   │
   │   │   │   ├─→ get_customer_info?
   │   │   │   │   └─→ Load from MOCK_CUSTOMERS
   │   │   │   │
   │   │   │   ├─→ get_policy_info?
   │   │   │   │   └─→ Read policies/*.md file
   │   │   │   │
   │   │   │   ├─→ check_vip_status?
   │   │   │   │   └─→ Query MOCK_CUSTOMERS
   │   │   │   │
   │   │   │   ├─→ check_precedents?
   │   │   │   │   │
   │   │   │   │   ├─→ AUDIT LOG: PRECEDENT_QUERY
   │   │   │   │   │
   │   │   │   │   ├─→ Query Kùzu Graph DB
   │   │   │   │   │   │
   │   │   │   │   │   └─→ MATCH (Person)-[MADE]->(Decision)-[HAS_CONTEXT]->(Tag)
   │   │   │   │   │
   │   │   │   │   ├─→ If found:
   │   │   │   │   │   └─→ AUDIT LOG: PRECEDENT_MATCH
   │   │   │   │   │
   │   │   │   │   └─→ If not found:
   │   │   │   │       └─→ AUDIT LOG: NO_PRECEDENT
   │   │   │   │
   │   │   │   ├─→ execute_order_return?
   │   │   │   │   │
   │   │   │   │   ├─→ Generate transaction ID
   │   │   │   │   │
   │   │   │   │   └─→ record_decision_to_ledger()
   │   │   │   │       └─→ AUDIT LOG: AGENT_DECISION
   │   │   │   │
   │   │   │   └─→ escalate_to_human?
   │   │   │       │
   │   │   │       ├─→ Generate ticket ID
   │   │   │       │
   │   │   │       └─→ record_decision_to_ledger()
   │   │   │           └─→ AUDIT LOG: AGENT_DECISION
   │   │   │
   │   │   └─→ AUDIT LOG: TOOL_RESULT
   │   │
   │   ├─→ Add tool results to conversation history
   │   │
   │   └─→ LOOP BACK TO STEP 2 (Claude sees new context)
   │
   └─→ If stop_reason == "end_turn":
       │
       ├─→ AUDIT LOG: AGENT_RESPONSE (final)
       │
       ├─→ If precedent was cited:
       │   └─→ AUDIT LOG: PRECEDENT_CITED
       │
       └─→ Return final text to Chainlit UI
            │
            └─→ Display to user
```

### Data Dependencies

```
Orders ─────┐
            ├─→ customer_id ─→ Customers ─→ VIP Status
            │
            └─→ items[] ─→ Policy Documents ─→ Compliance Check
                                │
                                └─→ If denied + VIP ─→ Context Graph
                                                        │
                                                        └─→ Precedent Match?
                                                            │
                                                            ├─→ Yes: Apply Exception
                                                            └─→ No: Deny or Escalate
```

---

## Conversation Types & Handling

> **📊 State Machine Diagram:** See [Conversation State Machine](diagrams/ARCHITECTURE.md#conversation-state-machine) for a visual representation of all possible conversation paths and transitions.

### 1. Simple Return (Policy-Compliant)

**Scenario:** Customer wants to return an eligible item within policy.

**Flow:**
```
User: "I want to return order ORD-123"
  ↓
Agent calls: look_up_order("ORD-123")
  → Returns: {status: "delivered", eligible_for_return: true, items: ["Headphones"]}
  ↓
Agent calls: get_customer_info(customer_id)
  → Returns: {customer_name: "John Doe", is_vip: false, years_active: 2}
  ↓
Agent outputs: "Hello John Doe! Thank you for being a loyal customer for 2 years.
I can help you with your return for order ORD-123 - Wireless Headphones.
Is the product still in its unopened, original packaging?"
  ↓
User: "Yes, never opened it"
  ↓
Agent calls: get_policy_info("returns")
  → Returns: Policy text (electronics must be unopened ✓)
  ↓
Agent calls: execute_order_return("ORD-123", "Customer changed mind")
  → Returns: {status: "success", transaction_id: "txn_12345"}
  ↓
Agent outputs: "✅ Return approved! Transaction ID: txn_12345..."
```

**Key Characteristics:**
- Straightforward flow
- No exceptions needed
- 2-3 tool calls total
- ~5 seconds end-to-end

### 2. Policy-Denied Return (Regular Customer)

**Scenario:** Customer wants to return a final sale item, not VIP.

**Flow:**
```
User: "I want to return ORD-777 (Socks)"
  ↓
Agent calls: look_up_order("ORD-777")
  ↓
Agent calls: get_customer_info(customer_id)
  → Returns: {is_vip: false, years_active: 1}
  ↓
Agent outputs: "Hello Jane Smith! I can help you with your return for order ORD-777 - Premium Wool Socks.
What's the reason for the return, and is the item in its original condition with tags attached?"
  ↓
User: "They don't fit"
  ↓
Agent calls: get_policy_info("returns")
  → Returns: "Socks are Final Sale (Non-returnable)"
  ↓
Agent calls: check_vip_status(customer_id)  # AUTOMATIC check
  → Returns: {is_vip: false}
  ↓
Agent outputs: "I understand you'd like to return these socks, however, according to our return policy,
socks are classified as Final Sale items and are non-returnable. This policy is in place due to
hygiene and safety standards. I apologize for any inconvenience."
```

**Key Characteristics:**
- VIP check is AUTOMATIC (not customer-requested)
- Policy clearly enforced
- No escalation (policy is clear)
- Empathetic denial

### 3. VIP Exception (Precedent Applied)

**Scenario:** VIP customer wants to return final sale item, precedent exists.

**Flow:**
```
User: "I want to return ORD-777 (Socks). I know they're final sale but I'm a VIP customer."
  ↓
Agent calls: look_up_order("ORD-777")
  ↓
Agent calls: get_customer_info(customer_id)
  → Returns: {customer_name: "Jessica Williams", is_vip: true, tier: "Gold",
             years_active: 10, lifetime_value: 50000}
  ↓
Agent outputs: "Hello Jessica Williams! Thank you for being a valued Gold VIP customer
for 10 years. I can help you with your return for order ORD-777 - Premium Wool Socks.
What's the reason for the return, and is the item in its original condition with tags attached?"
  ↓
User: "They just don't fit well"
  ↓
Agent calls: get_policy_info("returns")
  → Returns: "Socks are Final Sale"
  ↓
Agent calls: check_vip_status(customer_id)  # AUTOMATIC
  → Returns: {is_vip: true, tier: "Gold", years_active: 10}
  ↓
Agent calls: check_precedents("vip socks return exception")
  → Returns: {
      found: true,
      decision_id: "DEC-2024-001",
      decision: "APPROVE",
      person_name: "Sarah Chen",
      person_role: "VP, Customer Experience",
      conditions: "One-time exception only. Not to be used as precedent for all VIP customers.",
      rationale: "VIP customers with demonstrated loyalty and high lifetime value..."
    }
  ↓
Agent calls: execute_order_return("ORD-777", "VIP exception per precedent DEC-2024-001")
  → Returns: {status: "success", transaction_id: "txn_99887"}
  ↓
Agent outputs: "✅ Return approved and processed!

Transaction ID: txn_99887

**Important: This is a special exception to our standard policy**

Premium Wool Socks would normally not be eligible for return since socks are classified
as Final Sale items for hygiene reasons, however, as a valued Gold customer, we're making
an exception in this case.

**Please note:** This is a one-time courtesy exception and may not apply to future requests.

We truly appreciate your 10 years of loyalty and your business!

Your refund has been processed to your original payment method and should appear within
5-7 business days."
```

**Key Characteristics:**
- VIP check happens automatically
- Precedent graph query uses context tags
- Decision is attributed internally (Sarah Chen)
- Customer response includes conditions
- Customer does NOT see decision maker name
- Clear explanation of exception

### 4. VIP No Precedent (Escalation)

**Scenario:** VIP customer requests exception, but no precedent exists.

**Flow:**
```
User: "I want to return ORD-888 (Opened Gaming Monitor)"
  ↓
[... same flow as above until precedent check ...]
  ↓
Agent calls: check_precedents("vip electronics opened gaming monitor")
  → Returns: {found: false, message: "No matching precedents found"}
  ↓
Agent outputs: "I can see you're a valued Gold VIP customer for 5 years, and I truly
appreciate your loyalty. While you are a valued customer, this particular situation
(opened electronics return) requires human review since it falls outside our standard
policy and I don't have a precedent to guide this decision.

I'd like to escalate your case to a senior customer experience manager who can personally
review your request and account history. Would you like me to create a priority escalation
ticket for you?"
  ↓
User: "Yes please"
  ↓
Agent calls: escalate_to_human("ORD-888", "VIP customer requesting exception for opened electronics")
  → Returns: {status: "escalated", ticket_id: "TKT-789"}
  ↓
Agent outputs: "I've created priority ticket TKT-789 for you. A senior manager will
review your case within 24 hours and reach out directly. Thank you for your patience!"
```

**Key Characteristics:**
- Acknowledges VIP status
- Explains why escalation is needed
- Asks permission before escalating
- Provides ticket number for tracking

### 5. Database vs. Policy Conflict

**Scenario:** Database says "eligible" but policy says "no" (opened electronics).

**Flow:**
```
User: "I want to return ORD-222 (Headphones)"
  ↓
Agent calls: look_up_order("ORD-222")
  → Returns: {eligible_for_return: true, items: ["Wireless Headphones"]}
  ↓
[... greeting flow ...]
  ↓
Agent: "Is the product still in its unopened, original packaging?"
  ↓
User: "I opened the box to try them"
  ↓
Agent calls: get_policy_info("returns")
  → Returns: "Electronics must be in unopened, original packaging.
             If the box is opened, the return is DENIED."
  ↓
[Agent recognizes CONFLICT: DB says yes, Policy says no]
  ↓
Agent calls: check_vip_status(customer_id)  # AUTOMATIC
  → Returns: {is_vip: false}
  ↓
Agent outputs: "I understand you'd like to return the headphones. However, according
to our return policy, electronics must be in unopened, original packaging to be eligible
for return. Since the box has been opened, I'm unable to process a standard return.

For defective items, we do offer warranty support. Is there an issue with the product
performance that I can help troubleshoot?"
```

**Key Characteristics:**
- **CRITICAL:** Policy ALWAYS wins over database
- This is explicitly stated in system prompt ("Prime Directive")
- Agent must verify actual item state with customer
- VIP check still happens automatically
- Alternative solution offered (warranty)

### 6. Angry Customer (Immediate Escalation)

**Scenario:** Customer is angry or uses profanity.

**Flow:**
```
User: "This is absolutely ridiculous! I want my money back NOW for ORD-999!
This is a SCAM!"
  ↓
Agent detects: angry sentiment / keywords
  ↓
Agent calls: escalate_to_human("ORD-999", "Customer expressing frustration,
                                immediate human attention needed")
  → Returns: {status: "escalated", ticket_id: "TKT-456"}
  ↓
Agent outputs: "I'm very sorry you're experiencing frustration with this order.
I've immediately escalated your case to our support team (Ticket TKT-456) and
they will reach out to you shortly to resolve this. Is there anything else I
can help clarify while you wait?"
```

**Key Characteristics:**
- **IMMEDIATE** escalation (no policy checks)
- No argument with customer
- Empathetic response
- Ticket provided immediately
- De-escalation language

### 7. Holiday Exception

**Scenario:** Return is late (45 days) but was a holiday gift.

**Flow:**
```
User: "I want to return ORD-888. It was a holiday gift I bought in December,
so I'm returning it a bit late."
  ↓
Agent calls: look_up_order("ORD-888")
  → Returns: {eligible_for_return: false, notes: "Outside 30-day window (45 days)"}
  ↓
[... greeting flow ...]
  ↓
Agent calls: get_policy_info("returns")
  → Returns: "Items are eligible for return within 30 days of delivery."
  ↓
[Agent detects: "holiday gift" + "late" context]
  ↓
Agent calls: check_precedents("holiday gift late return")
  → Returns: {
      found: true,
      decision_id: "DEC-2024-002",
      decision: "APPROVE",
      person_name: "Michelle Rodriguez",
      person_role: "Director of Operations",
      conditions: "Extended return window to 60 days for holiday purchases
                   (Nov 1 - Dec 31). One-time courtesy extension.",
      rationale: "Holiday gift recipients need additional time..."
    }
  ↓
Agent calls: execute_order_return("ORD-888", "Holiday gift exception per DEC-2024-002")
  ↓
Agent outputs: "✅ Return approved!

**Important: This is a special holiday gift exception**

Normally, returns must be completed within 30 days of delivery. However, we understand
that holiday gifts require additional time for recipients, so we're extending the return
window to 60 days for your December purchase.

Your refund has been processed to your original payment method..."
```

**Key Characteristics:**
- Precedent applies to non-VIP customers too
- Context keywords trigger precedent lookup
- Seasonal/temporal exceptions supported
- Clear explanation of special circumstance

---

## Technical Deep Dives

> **📊 Visual Guides:**
> - [ReAct Loop Flowchart](diagrams/ARCHITECTURE.md#react-loop-flow)
> - [Precedent Matching Algorithm](diagrams/ARCHITECTURE.md#precedent-matching-flow)
> - [Multi-Layered Governance Flow](diagrams/ARCHITECTURE.md#multi-layered-governance)
> - [Graph Database Schema](diagrams/ARCHITECTURE.md#graph-database-schema)

### ReAct Loop Implementation

The **ReAct Pattern** (Reason + Act) is the core of the agent's decision-making process.

**Standard Agent Flow (Non-ReAct):**
```
User Input → Claude → Tool Call → Tool Result → Claude → Final Answer
```

**Problem:** Agent can only make ONE decision per turn. If it needs to:
1. Look up order
2. Check policy
3. Check precedents
4. Execute refund

It would require 4 separate user messages.

**ReAct Loop Solution:**
```python
while True:
    response = call_claude()

    if response.stop_reason == "end_turn":
        return response.text  # Claude has final answer

    elif response.stop_reason == "tool_use":
        # Execute ALL tool calls
        tool_results = execute_tools(response.content)

        # Add results back to conversation as "user" message
        self.messages.append({"role": "user", "content": tool_results})

        # Loop continues automatically - Claude sees results and decides next step
```

**Benefits:**
- Agent can chain multiple reasoning steps
- No user intervention needed between tool calls
- Agent can course-correct based on tool results
- Enables complex workflows (check order → greet → check policy → check VIP → check precedents → execute)

**Example Trace:**
```
Turn 1: Claude → [Tool: look_up_order] → Results added to history
Turn 2: Claude → [Tool: get_customer_info] → Results added to history
Turn 3: Claude → [Text: Greeting message] → END_TURN (stop, send to user)
Turn 4: User responds → Claude → [Tool: get_policy_info] → Results added
Turn 5: Claude → [Tool: check_vip_status] → Results added
Turn 6: Claude → [Tool: check_precedents] → Results added
Turn 7: Claude → [Tool: execute_order_return] → Results added
Turn 8: Claude → [Text: Final response with transaction ID] → END_TURN
```

### Precedent Matching Algorithm

**Challenge:** How to find relevant historical decisions from a graph of precedents?

**Approach: Graph Traversal with Weighted Scoring**

**Step 1: Tag Extraction**
```python
# Agent calls: check_precedents("vip socks return exception")
input_tags = ["vip", "socks", "return", "exception"]
```

**Step 2: Graph Query**
```cypher
MATCH (p:Person)-[m:MADE]->(d:Decision)-[ctx:HAS_CONTEXT]->(t:Tag)
WHERE t.name IN ['vip', 'socks', 'return', 'exception']
  AND d.expires_at = 'NEVER'  # Decision hasn't expired
  AND d.confidence_score >= 0.7  # High confidence only
WITH p, d, SUM(ctx.relevance_score) AS score
ORDER BY score DESC, p.authority_level DESC
LIMIT 1
RETURN d.id, d.title, d.outcome, d.reasoning, d.conditions,
       p.name, p.role, p.authority_level, score
```

**Step 3: Scoring Logic**
- Each Tag → Decision relationship has a `relevance_score` (0.0 - 1.0)
- Scores are summed for all matching tags
- Example:
  - Tag "vip" → relevance: 1.0
  - Tag "socks" → relevance: 1.0
  - Tag "return" → relevance: 0.8
  - Tag "exception" → relevance: 0.5
  - **Total Score: 3.3**

**Step 4: Tie-Breaking**
- If multiple decisions have same score, use `person.authority_level`
- VP decisions > Director decisions > Manager decisions

**Step 5: Confidence Filtering**
- Only return decisions with `confidence_score >= 0.7`
- Low-confidence precedents are ignored (require human review)

**Result:**
```json
{
  "found": true,
  "decision_id": "DEC-2024-001",
  "decision_title": "VIP Socks Exception - Loyalty Override",
  "decision": "APPROVE",
  "rationale": "VIP customers with demonstrated loyalty...",
  "conditions": "One-time exception only...",
  "person_name": "Sarah Chen",
  "person_role": "VP, Customer Experience",
  "authority_level": 3,
  "match_score": 3.3,
  "confidence": 0.95
}
```

**Why This Works:**
- Semantic matching via tags (not keyword search)
- Weighted by relevance (not just boolean match)
- Authority levels encode organizational hierarchy
- Expiration dates allow temporal policies
- Confidence scores enable human-in-the-loop for edge cases

### Multi-Layered Governance System

**Challenge:** How to enforce complex compliance rules that can't be captured in a simple boolean flag?

**Solution: Three-Layer Governance Hierarchy**

**Layer 1: Database Flags (Lowest Priority)**
```json
{
  "order_id": "ORD-123",
  "eligible_for_return": true  // ← Can be overridden
}
```

**Layer 2: Policy Documents (Medium Priority)**
```markdown
# Return Policy

## Non-Returnable Categories (FINAL SALE)
- Socks → ACTION: REJECT
- Opened Electronics → ACTION: REJECT
```

**Layer 3: Context Graph (Highest Priority)**
```
Person → Decision → "APPROVE despite policy" → Tags ["vip", "socks"]
```

**Enforcement Mechanism:**

**Prompt-Based Enforcement:**
```
# YOUR PRIME DIRECTIVE: "Policy Overrides Database"
1. Even if `eligible_for_return` is TRUE, you MUST check the Policy.
2. If Policy says "Non-Returnable", the Policy WINS.
```

**Data-Based Enforcement:**
```markdown
**ACTION: REJECT**  // ← Explicit imperative language
```

**Tool-Based Enforcement:**
```python
{
  "name": "execute_order_return",
  "input_schema": {
    "required": ["order_id", "reason", "policy_check_confirmation"]
    #                                   ↑ Forces agent to self-certify compliance
  }
}
```

**Conflict Resolution Matrix:**

| Database | Policy | Precedent | Result |
|----------|--------|-----------|--------|
| ✓ Yes    | ✓ Yes  | N/A       | **APPROVE** (standard return) |
| ✓ Yes    | ✗ No   | N/A       | **DENY** (policy wins) |
| ✗ No     | ✗ No   | ✓ Yes     | **APPROVE** (precedent overrides) |
| ✗ No     | ✗ No   | ✗ No      | **DENY** or **ESCALATE** |

**Example Conflict:**

```
Situation: Customer opened electronics
  ├─ Database: eligible_for_return = true
  ├─ Policy: "Opened electronics are non-returnable"
  ├─ Customer: CUST-VIP-0001 (Gold VIP)
  └─ Precedent: DEC-2024-003 (Opened tech exception for high-value customers)

Resolution:
  1. Check Database → "yes" ✓
  2. Check Policy → "no" ✗ (CONFLICT!)
  3. Check VIP Status → true ✓
  4. Check Precedents → Found DEC-2024-003 ✓
  5. Final Decision: APPROVE (Precedent overrides Policy)
```

**Why Three Layers?**
- **Layer 1 (DB):** Fast initial filtering (99% of cases)
- **Layer 2 (Policy):** Catches edge cases DB doesn't understand
- **Layer 3 (Graph):** Enables human judgment to override rigid rules
- **Result:** Deterministic for standard cases, adaptive for edge cases

### Session Tracking & Audit Trail

**Challenge:** How to trace every decision back to its source for compliance?

**Solution: Session-Scoped Audit Logging**

**Session Lifecycle:**
```python
# 1. Session Creation (First message in conversation)
if not self.session_id:
    self.session_id = f"SESSION-{uuid.uuid4().hex[:8]}"
    set_session_id(self.session_id)  # Store in thread-local storage

# 2. Every event tagged with session_id
audit_logger.info(
    "Tool call",
    extra={'session_id': self.session_id, 'tool_name': 'check_precedents'}
)

# 3. Session persists across entire conversation
# 4. Admin can query: "Show me SESSION-a1b2c3d4"
```

**Audit Log Structure:**
```jsonl
{"timestamp": "...", "session_id": "SESSION-a1b2", "event_type": "USER_MESSAGE", "user_message": "..."}
{"timestamp": "...", "session_id": "SESSION-a1b2", "event_type": "TOOL_CALL", "tool_name": "look_up_order"}
{"timestamp": "...", "session_id": "SESSION-a1b2", "event_type": "TOOL_RESULT", "order_id": "ORD-123"}
{"timestamp": "...", "session_id": "SESSION-a1b2", "event_type": "PRECEDENT_QUERY", "query_tags": ["vip", "socks"]}
{"timestamp": "...", "session_id": "SESSION-a1b2", "event_type": "PRECEDENT_MATCH", "decision_id": "DEC-2024-001", "person_name": "Sarah Chen"}
{"timestamp": "...", "session_id": "SESSION-a1b2", "event_type": "AGENT_DECISION", "agent_decision": "APPROVE", "decision_id": "DEC-2024-001"}
{"timestamp": "...", "session_id": "SESSION-a1b2", "event_type": "AGENT_RESPONSE", "agent_response": "✅ Return approved..."}
```

**Admin Trace Viewer:**
```python
# Input: SESSION-a1b2
# Output: Chronological event timeline with attribution

def get_session_events(session_id):
    # Parse decision_audit.log
    # Filter by session_id
    # Return chronological list of events

async def handle_admin_query(session_id):
    events = get_session_events(session_id)
    formatted_trace = format_decision_trace(session_id, events)
    # Display in admin UI
```

**Decision Attribution Chain:**
```
Agent Decision: APPROVE return for ORD-777
    ↓ (cited)
Precedent: DEC-2024-001 "VIP Socks Exception"
    ↓ (made by)
Person: Sarah Chen, VP Customer Experience
    ↓ (authority)
Authority Level: 3 (VP)
    ↓ (source)
Source Email: esc-2024-001-vip-socks-exception.txt
```

**Compliance Benefits:**
- Every exception is attributable to a specific human decision
- Audit trail shows agent followed proper protocol
- Can reconstruct decision path months later
- Proves agent didn't "hallucinate" exceptions

---

## Deployment & Dependencies

### System Requirements

**Software:**
- Python 3.10+
- Anthropic API Key

**Hardware (for local demo):**
- 2 GB RAM (for Kùzu database)
- ~500 MB disk space (database + logs)

### Dependencies

**Core:**
- `anthropic` - Claude API client
- `chainlit` - Chat UI framework
- `kuzu` - Embedded graph database
- `python-dotenv` - Environment variable management

**Observability:**
- `opentelemetry-api` - Tracing API
- `opentelemetry-sdk` - Tracing SDK
- `opentelemetry-exporter-otlp` - OTLP exporter
- `openinference-instrumentation-anthropic` - Anthropic auto-instrumentation
- `arize-phoenix` - Observability UI

**Utilities:**
- `logging` (stdlib) - Audit logging
- `json` (stdlib) - Data serialization
- `uuid` (stdlib) - Session ID generation
- `datetime` (stdlib) - Timestamps
- `pathlib` (stdlib) - File path handling

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/enterprise-cx-agent.git
cd enterprise-cx-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-api03-...
EOF

# 4. Initialize graph database
python scripts/init_graph.py

# Expected output:
# 📦 Backed up old database...
# 🗑️  Cleared existing database...
# ⚙️  Initializing Kùzu Graph Database...
# ✅ Schema created successfully!
# 📊 Seeded 3 precedent decisions
```

### Running the System

**Terminal 1: Start Observability UI**
```bash
python -m phoenix.server.main serve

# Expected output:
# 🌍 Server started on http://localhost:6006
# 📊 Trace collector listening on http://localhost:4317
```

**Terminal 2: Start Agent Application**
```bash
chainlit run app.py -w

# Expected output:
# ✅ Connected to Kùzu Graph at: /path/to/context_graph_db
# 🔭 Observability: Tracing enabled. Sending to Phoenix (localhost:6006)
# 🚀 Chainlit running at http://localhost:8000
```

**Access Points:**
- Customer UI: http://localhost:8000 (select "TrueCart Support")
- Admin UI: http://localhost:8000 (select "TrueCart Admin")
- Observability: http://localhost:6006

### Configuration Files

**.env** (not committed to git)
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**config.py**
```python
MODEL_NAME = "claude-sonnet-4-5-20250929"  # Latest Sonnet
MAX_TOKENS = 1024
TEMPERATURE = 0.0  # Deterministic
SYSTEM_PROMPT = """..."""  # 239-line SOP
```

**.gitignore**
```
.env
logs/
data/context_graph_db/
__pycache__/
```

### Mock Data Files

**data/mock_orders.json**
```json
{
  "orders": {
    "ORD-123": {
      "status": "delivered",
      "items": ["Wireless Headphones"],
      "eligible_for_return": true,
      "customer_id": "CUST-REG-0001",
      "customer_name": "John Doe"
    }
  }
}
```

**data/mock_customers.json**
```json
{
  "customers": {
    "CUST-VIP-0001": {
      "customer_name": "Jessica Williams",
      "is_vip": true,
      "tier": "Gold",
      "lifetime_value": 50000,
      "years_active": 10,
      "member_since": "2015-03-15"
    }
  }
}
```

### Database Initialization

**scripts/init_graph.py** creates:
1. **Node Tables:** Person, Decision, Product, Tag
2. **Relationship Tables:** MADE, APPLIES_TO, HAS_CONTEXT, CITES
3. **Seed Data:** 3 precedent decisions from email files

**Seeded Precedents:**
- DEC-2024-001: VIP Socks Exception (Sarah Chen, VP CX)
- DEC-2024-002: Holiday Gift Late Return (Michelle Rodriguez, Director Ops)
- DEC-2024-003: Opened Tech High Value (Jennifer Park, Director CX)

### Logging Configuration

**logs/console.log** (human-readable)
```
2026-02-07 10:30:45 INFO [Claude Agent] User Input: I want to return ORD-123
2026-02-07 10:30:46 INFO [BackendServices] API CALL: Querying OMS for Order ID: ORD-123
2026-02-07 10:30:46 INFO [Claude Agent] DECISION: Agent called 'look_up_order' with input {'order_id': 'ORD-123'}
```

**logs/decision_audit.log** (machine-readable, JSONL)
```jsonl
{"timestamp":"2026-02-07T10:30:45.123Z","level":"INFO","session_id":"SESSION-a1b2","event_type":"USER_MESSAGE","message":"..."}
{"timestamp":"2026-02-07T10:30:46.456Z","level":"INFO","session_id":"SESSION-a1b2","event_type":"TOOL_CALL","tool_name":"look_up_order"}
```

---

## Key Design Decisions

### Why Kùzu Instead of SQL?

**Problem:** Precedent matching requires traversing relationships (Person → Decision → Tags)

**SQL Approach:**
```sql
SELECT d.*, p.*
FROM decisions d
JOIN person p ON d.person_id = p.id
JOIN decision_tags dt ON d.id = dt.decision_id
JOIN tags t ON dt.tag_id = t.id
WHERE t.name IN (?, ?, ?)
```

**Graph Approach:**
```cypher
MATCH (p:Person)-[MADE]->(d:Decision)-[HAS_CONTEXT]->(t:Tag)
WHERE t.name IN ['vip', 'socks', 'return']
```

**Benefits of Graph:**
- Natural representation of relationships
- Easier to add new relationship types (CITES, SUPERSEDES, etc.)
- Better performance for traversal queries
- Embedded database (no separate server)
- SQL-like syntax (Cypher)

### Why Temperature = 0.0?

**Goal:** Deterministic agent behavior (same input → same output)

**Temperature = 0.0:**
- Claude always picks most likely token
- No randomness in decision-making
- Same conversation will produce same result
- Critical for customer support (consistency)

**Trade-off:**
- Less creative responses
- More formal language
- Worth it for reliability

### Why Chainlit Instead of Gradio/Streamlit?

**Chainlit Advantages:**
- Built specifically for chat agents
- Async-first (non-blocking I/O)
- Built-in streaming support
- Multi-user sessions out of the box
- Chat profiles (customer vs admin)
- Message history management

**Comparison:**
- Gradio: Better for model demos, not chat
- Streamlit: State management is painful for chat
- Custom Flask/FastAPI: Would need to rebuild chat UI

### Why Mock Services?

**Purpose:** Proof-of-concept demonstration

**Real Production Would Integrate:**
- Actual OMS (Order Management System)
- Real payment gateway (Stripe, PayPal)
- CRM system (Salesforce, HubSpot)
- Ticketing system (Zendesk, Intercom)
- Authentication & authorization
- Rate limiting & security

**Mock Benefits:**
- Easy to set up and demo
- No external dependencies
- Predictable data for testing
- Focus on agent logic, not integration

---

## Future Enhancements

### Potential Additions

1. **Multi-Language Support:** Detect customer language and respond accordingly
2. **Sentiment Analysis:** More sophisticated emotion detection beyond keywords
3. **Batch Processing:** Handle multiple orders in one conversation
4. **Proactive Outreach:** Agent initiates conversations for order delays
5. **Learning from Escalations:** Feed human decisions back into graph
6. **A/B Testing:** Test different prompts with traffic splitting
7. **Cost Optimization:** Use Haiku for simple queries, Opus for complex
8. **Voice Interface:** Integrate with speech-to-text
9. **Multi-Modal:** Support image uploads (damaged product photos)
10. **Analytics Dashboard:** Metrics on return rates, exception usage, etc.

### Known Limitations

1. **No Authentication:** Anyone can access admin trace viewer
2. **No Rate Limiting:** Could be abused in production
3. **Single-User Database:** Kùzu is not multi-tenant
4. **No Caching:** Policy documents re-read on every call
5. **Limited Error Handling:** Mock services don't fail realistically
6. **No Retry Logic:** Network failures not handled
7. **Session Expiration:** Sessions never expire (memory leak in long runs)
8. **No Data Validation:** Mock data not validated for consistency

---

## Conclusion

The **Enterprise CX Agent** demonstrates how to build a **reliable, auditable, and adaptive** AI system for customer support. By combining:

- **Deterministic workflow** (ReAct loop with explicit SOP)
- **Multi-layered governance** (Database → Policy → Precedents)
- **Graph-based decision memory** (Kùzu precedent matching)
- **Complete observability** (OpenTelemetry + structured logging)

...the system achieves the "holy grail" of enterprise AI: **predictable enough for compliance, flexible enough for real-world edge cases.**

The architecture patterns demonstrated here (tool-based agent, policy-as-code, precedent graphs, decision attribution) are applicable to any enterprise workflow that requires both strict governance and human-in-the-loop adaptability.

---

## Appendix

### Glossary

- **ReAct:** Reason + Act pattern (multi-turn tool use loop)
- **Context Graph:** Graph database storing precedents as relationships
- **Decision Ledger:** Audit log of agent decisions with attribution
- **SOP:** Standard Operating Procedure (system prompt)
- **Tool Schema:** JSON definition of agent capabilities
- **Session ID:** Unique identifier for conversation trace
- **Precedent:** Historical human decision that can be applied to similar cases
- **Attribution:** Linking agent decision to human decision maker
- **Observability:** Real-time monitoring and visualization of agent behavior
- **Kùzu:** Embedded graph database (like DuckDB for graphs)

### File Structure

```
enterprise-cx-agent/
├── app.py                    # Main application entry point
├── agent/
│   └── agent.py              # SupportAgent class (ReAct loop)
├── tools/
│   └── tools.py              # Tool schema definitions
├── services/
│   └── services.py           # EnterpriseServices (tool implementations)
├── config.py                 # Configuration & system prompt
├── logging_config.py         # Audit logging setup
├── observability/
│   └── tracing.py            # OpenTelemetry configuration
├── admin/
│   └── decision_reviewer.py  # Admin trace viewer
├── data/
│   ├── mock_orders.json      # Order database
│   ├── mock_customers.json   # Customer database
│   ├── data_loader.py        # JSON data loader
│   ├── context_graph_db/     # Kùzu database files
│   └── decision_emails/      # Source precedent emails
│       ├── esc-2024-001-vip-socks-exception.txt
│       ├── esc-2024-002-holiday-gift-late-return.txt
│       └── esc-2024-003-opened-tech-high-value.txt
├── policies/
│   ├── return_policy.md      # Return policy document
│   ├── shipping_policy.md    # Shipping policy
│   └── privacy_policy.md     # Privacy policy
├── scripts/
│   ├── init_graph.py         # Database initialization
│   └── debug_graph.py        # Database inspection tool
├── logs/
│   ├── console.log           # Human-readable logs
│   └── decision_audit.log    # Machine-readable audit log (JSONL)
├── tests/
│   ├── test_complete_workflow.py
│   ├── test_decision_ledger.py
│   └── test_new_schema.py
├── docs/
│   ├── BRANDING_GUIDE.md
│   ├── requirements-decision-ledger.md
│   └── TECHNICAL_OVERVIEW.md  # This document
├── .env                       # API keys (not committed)
├── .gitignore
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
└── EXPECTED_VIP_RESPONSE.md  # Example response format

```

### Contact & Contribution

**Author:** Nitin Nayar
**Purpose:** Interview / Demo Project
**Status:** Proof of Concept (Not Production-Ready)

**Note:** This project is designed to showcase architectural patterns and is not intended for production deployment without significant security, scalability, and reliability enhancements.

---

*Document Version: 1.0*
*Last Updated: February 2026*
*Generated with: Claude Sonnet 4.5*
