# Enterprise CX Agent - Design Brief

---

## Key Features

### 1. AI-Powered Upsell & Exchange Engine for revenue protection
When a customer requests a return, the agent gently nudges them towards an exchange through personalized book recommendations based on customer reading preferences (favorite authors, genres, past ratings). Uses `get_book_recommendations()` and `process_exchange()` tools to offer alternatives before processing the refund.

**Business Impact:** Reduces return costs, increases revenue retention, improves CSAT
**Metrics:** 30%+ exchange conversion rate, measurable AOV retention

### 2. Precedent-Based Decision System to improve deflection rates
Addresses the lack of full context in automated returns: when managers manually approve exceptions in ticketing systems (Jira, Zendesk) or via Slack, this decision data is never captured into policy documents, causing the same exceptions to be escalated repeatedly. Our system consolidates this managerial decision history into a queryable graph database (mock). When policy violations occur (e.g., VIP requesting return beyond 30 days during holiday period), the agent checks for matching precedents before escalating, significantly improving deflection rates by preventing repeated human approvals for identical scenarios.

**Business Impact:** improved deflection rate, reductions in manager escalations, maintains compliance through precedent attribution
**Examples Use Cases:** 60-day holiday gift window, VIP exceptions for opened items

### 3. Session level Admin View & Audit System to see full decision flow 
Typical AI chatbots are black boxes; in complex systems with multiple tool calls (order lookup, VIP checks, policy validation), reasoning steps, and guardrails, administrators need transparency into how decisions are made. Our dual-layer system provides: (1) an admin UI where non-technical admins can enter a session ID to view the complete decision trace, and (2) OpenTelemetry (OTEL) export to any observability platform (Datadog, Arize Phoenix (for demo)) for aggregate analytics. This enables end-to-end auditability, helps identify performance trends, allows admins to understand decision logic, and provides insights for tweaking agents and policies.

**Business Impact:** Ensures regulatory compliance (GDPR Article 22), enables QA reviews, identifies performance issues via trend analysis
**Metrics:** 99%+ policy compliance score, < 2 min average audit time

---

## Architecture Overview

**Tech Stack:** Anthropic Claude (Haiku 4.5 for routing, Sonnet 4.5 for reasoning) | Chainlit UI | Kùzu Graph Database | Arize Phoenix + OpenTelemetry | JSON mock services

**System Flow:**
```
User Input → Question Router (Haiku) → Categorize (ORDER_STATUS | RETURNS_REFUNDS | GENERAL)
  → SupportAgent (Sonnet) → ReAct Loop → Tool Invocation → Service Layer
    → Response Generation → Arize Tracing (full audit trail)
```

**Core Components:**
- **Question Router:** Cost-optimized classifier — 95% cheaper for the routing classification step ($0.15/1M vs $3/1M tokens); every conversation still uses Sonnet for reasoning
- **Support Agent:** ReAct loop with stateless service layer, session tracking via unique `SESSION-{uuid.hex[:8]}`. Note: `config.py` retains a legacy `SYSTEM_PROMPT` for backward compatibility; `prompts.py` is the active source for all three category-specific prompts.
- **Tool Layer:** 10 active tools calling mock services (order lookup, VIP checks, precedent queries, escalation, recommendations); `escalate_to_human()` is deprecated — use `escalate_order_issue()` or `escalate_general_question()` instead
- **Precedent System:** Graph database (Person → Decision → Tags) for human-approved exception patterns
- **Observability:** OpenTelemetry tracing with session grouping, JSONL audit logs

---

## Conversation Design: Intent Recognition & Decision Logic

### How the Agent Recognizes Intent

**Step 1: Question Router (Claude Haiku 4.5)**
Every user message is first classified by a lightweight router into one of three categories:
- **ORDER_STATUS** - Order tracking, delivery questions
- **RETURNS_REFUNDS** - Return requests, refund inquiries, exchanges
- **GENERAL** - Policy questions, account help, FAQs

The router uses a specialized prompt with examples for each category, running at temp=0.0 for deterministic classification. This costs ~$0.15/1M tokens vs $3/1M for Sonnet — 95% cheaper for the classification step specifically; agent reasoning still uses Sonnet for every conversation.

**Step 2: Category-Specific System Prompts**
Based on the router's classification, the Support Agent loads one of three specialized prompts. Each prompt contains:
- Mandatory workflow steps (e.g., "ALWAYS call get_customer_info() first")
- Required information to gather (order ID, item condition, customer sentiment)
- Decision trees (if VIP + policy violation → check precedents)
- Escalation triggers (anger detection keywords)

This prevents context dilution from a single monolithic prompt trying to handle all scenarios.

---

### How the Agent Decides: Answer, Ask, or Act

The agent uses Claude's native tool-calling capability with a **ReAct loop** (Reason → Act → Observe). On each turn, Claude returns either:
- **`tool_use`** blocks → Execute tool, add results to history, loop again
- **`end_turn`** → Return final response to user

**Example: RETURNS_REFUNDS Workflow**

When a user says *"I want to return order ORD-123"*, the agent follows this decision logic:

**Turn 1 - Order Lookup (Action):**
- Agent reasoning: "I need the order details first — `customer_id` comes from the order record"
- Returns: `tool_use` block for `look_up_order("ORD-123")`
- System executes tool, returns `{customer_id: "CUST-VIP-0001", item: "Die Hard Signed Edition", days_since_purchase: 5, eligible_for_return: true}`

**Turn 2 - Customer Info & Personalized Greeting (Action + Ask):**
- Agent reasoning: "I now have `customer_id`. Fetch customer profile then greet with item details and ask the policy-relevant question"
- Returns: `tool_use` block for `get_customer_info("CUST-VIP-0001")`
- Agent receives: `{name: "John McClane", is_vip: true, tier: "Gold", years_active: 5, reading_preferences: {favorite_authors: ["Lee Child"], favorite_genres: ["Action", "Thriller"]}}`
- Returns: `end_turn` with *"Hello John! Thank you for 5 years as a Gold member. I can help with your return for the Die Hard Signed Edition. Is the book still in its original sealed condition?"*

**Turn 3 - Policy Check & Upsell Opportunity (Action):**
- User: *"Yes, it's unopened"*
- Agent reasoning: "Unopened signed edition within 30 days = eligible per policy. Before processing refund, offer exchange based on reading preferences"
- Returns: `tool_use` for `get_book_recommendations(customer_id="CUST-VIP-0001", exclude_order_id="ORD-123")`

**Turn 4 - Offer Exchange (Answer with Recommendation):**
- Agent receives: Recommendations = ["The Sentinel by Lee Child", "Killing Floor by Lee Child", "Past Tense by Lee Child"]
- Returns: `end_turn` with *"I can process that return for you. Before I do, I noticed you love Lee Child's work! Would you like to exchange this for his latest release 'The Sentinel'? I can process the exchange immediately with no additional payment needed."*

**Turn 5 - Process Exchange (Action):**
- User: *"That sounds perfect, let's do the exchange!"*
- Agent reasoning: "Customer accepts exchange recommendation"
- Returns: `tool_use` for `process_exchange("ORD-123", new_book_id="BOOK-456", reason="Customer exchange for preferred author")`

**Turn 6 - Final Response (Answer):**
- Agent receives: `{success: true, transaction_id: "txn_12345", new_order_id: "ORD-789"}`
- Returns: `end_turn` with *"Perfect! I've processed the exchange. Your new order for 'The Sentinel' is ORD-789 and will ship within 2 business days. Transaction ID: txn_12345. You'll love this one - it's getting great reviews from Action/Thriller fans!"*

---

### Key Decision Rules in RETURNS_REFUNDS Prompt

**Mandatory Actions (Agent MUST take action):**
1. Always call `get_customer_info()` first (for personalized greeting)
2. Always call `look_up_order()` (to verify eligibility)
3. If policy violation + VIP customer → MUST call `check_vip_status()` and `check_precedents()` before denying
4. If anger detected → MUST call `escalate_order_issue()` immediately (skip policy checks)

**When to Ask Follow-Ups:**
- Order ID missing → Ask: *"What's your order number?"*
- Item condition unclear → Ask: *"Is the book unread and in resellable condition?"*
- Customer wants exchange → Ask: *"Would you like a recommendation based on your reading preferences?"*

**When to Answer Directly:**
- All required information gathered + decision made + action completed → Return final response
- Policy information requests (GENERAL category) → Retrieve from `get_policy_info()` and explain

**Tri-Layered Governance to Prevent Hallucinations:**
Even if database returns `eligible_for_return: true`, the agent enforces policy through:
1. System prompt explicit rules (*"NEVER approve digital goods after download"*)
2. Policy documents with ACTION directives (*"ACTION: REJECT - Digital goods are final sale"*)
3. Tool constraints: `execute_order_return()` requires a mandatory `reason` argument (agent must state the compliance justification before executing the refund); `escalate_order_issue()` requires `policy_check_confirmation: "verified_compliant"` before routing to human support

This prevents the agent from bypassing business rules based solely on database flags.

---

## Hallucination & Safety Controls

### How the Agent Avoids Inventing Information

**1. Tool-Only Information Retrieval**
The agent cannot invent data - all customer information, order details, and policies must come from tool calls. The system prompt explicitly forbids stating facts without tool confirmation. For example, the agent cannot say "Your order shipped yesterday" without first calling `look_up_order()` and receiving `{status: "shipped", ship_date: "2026-02-16"}`.

**2. Structured Tool Responses (No Free-Form Text)**
All tools return structured JSON with predefined schemas. This prevents the agent from misinterpreting vague responses:
- `look_up_order()` returns: `{status: "shipped" | "delivered" | "processing", eligible_for_return: boolean, days_since_purchase: integer}`
- No tool returns free-form text like "probably eligible" - only explicit boolean values
- Transaction IDs are system-generated (e.g., `txn_12345`), not invented by the agent

**3. Mandatory Tool Call Sequences**
The system prompt enforces required tool chains to prevent skipping validation steps:
- **VIP denials:** Agent MUST call `check_vip_status()` → `check_precedents()` before denying any VIP customer
- **Returns:** Agent MUST call `look_up_order()` → `get_customer_info()` → `get_policy_info()` before making eligibility decisions
- If agent tries to skip steps, the response will lack required context and fail validation

**4. Policy-as-Code with Explicit ACTION Directives**
Policy documents (markdown files) contain unambiguous rules:
```
Digital Goods (E-books, Audiobooks):
- Non-returnable after download
- ACTION: REJECT with message "Digital goods are final sale per our terms"
```
The agent cannot "interpret" policies creatively - ACTION directives are explicit commands.

### Key Guardrails & Constraints

**1. Tri-Layered Governance (Prevents Policy Bypass)**
Even if the database returns `eligible_for_return: true`, the agent enforces three layers:
- **Layer 1 (System Prompt):** "NEVER approve digital goods returns after download"
- **Layer 2 (Policy Documents):** "ACTION: REJECT - Digital goods are final sale"
- **Layer 3 (Tool Constraints):** `execute_order_return()` requires a mandatory `reason` argument (agent must state the compliance justification); `escalate_order_issue()` requires `policy_check_confirmation: "verified_compliant"` before routing to human support

This prevents the agent from trusting database flags alone (databases can have stale/incorrect data).

**2. Deterministic Router (No Creative Categorization)**
The Question Router runs at `temperature=0.0` with explicit examples for each category. This prevents misclassification that could lead to wrong workflows (e.g., routing a return request to GENERAL category, which lacks return tools).

**3. Escalation Triggers (Safety Valves)**
The agent auto-escalates in high-risk scenarios:
- **Anger detection:** Immediate `escalate_order_issue()` before making decisions (prevents rushed approvals under pressure)
- **No precedent match:** VIP exception with no matching precedent → Escalate to manager (no guessing)
- **Ambiguous situations:** If policy is unclear or customer intent is vague → Ask clarifying questions or escalate

**4. Audit Trail with Reasoning Capture**
Every decision is logged with:
- Tool calls made (with arguments)
- Tool results received (exact JSON)
- Agent reasoning ("Unopened signed edition within 30 days = eligible per policy")
- Precedent citations (if used)
- Final decision with justification

Managers can review logs to identify hallucinations (e.g., agent claiming a tool was called when it wasn't, or citing a non-existent precedent).

**5. Tool Result Validation**
Before using tool results, the service layer validates:
- Required fields are present (no `undefined` or `null` for critical data)
- Data types are correct (`days_since_purchase` is integer, not string)
- Enum values are valid (`status` is one of ["shipped", "delivered", "processing"], not "maybe shipped")

**6. Order ID Validation & Normalization**
The service layer validates all inputs:
- Order IDs must match pattern `ORD-\d{3}` after normalization
- Non-existent order IDs return error (agent cannot proceed with fake orders)
- Customer IDs must exist in database (prevents inventing customers)

**7. Precedent Attribution Requirements**
When approving exceptions, the agent MUST cite:
- **Precedent ID** (e.g., "DEC-002")
- **Manager name** (e.g., "Sarah Chen")
- **Manager role** (e.g., "Senior Manager")
- **Authority level** (determines precedent weight)

If no matching precedent exists in the graph database, the agent CANNOT invent one - it must escalate to a human. Precedents have expiration dates (1 year TTL) to prevent using outdated decisions.

---

## Example System Prompt Structure

**Category:** RETURNS_REFUNDS (Most Complex)

**Mandatory Workflow:**
1. **Personalized Greeting** - Call `get_customer_info()`, acknowledge VIP tier and years of loyalty
2. **Anger Detection** - Monitor for frustration signals → Immediate `escalate_order_issue()` if detected
3. **Gather Order Info** - Call `look_up_order()` for item details, purchase date, eligibility
4. **Policy Enforcement Hierarchy** - Check timing (30-day window), item category (digital goods), condition (read/unread)
5. **VIP Exception Protocol** - If policy violation + VIP customer: `check_vip_status()` → `check_precedents()` → Auto-approve if match found
6. **Book Recommendations** - Call `get_book_recommendations()` if customer disappointed
7. **Process Return/Exchange** - `execute_order_return()` or `process_exchange()` with compliance reason

**Governance Rules:** Never approve digital goods after download, never bypass 30-day window without precedent, always log decision reasoning

*(Full prompt text available in DESIGN_DOCUMENT.md)*

---

## Production-Ready Changes

The current system uses mock data and embedded databases. Production deployment requires:

### 1. Service Integration
Replace mock JSON with real API clients: OMS, CRM (Salesforce/HubSpot), payment gateway (Stripe), ticketing system (Zendesk/Intercom). Implement retry logic, circuit breakers, and caching layers.

### 2. Authentication & Security
OAuth 2.0/SAML for SSO, RBAC (customer/agent/manager/auditor roles), JWT tokens, rate limiting, PII redaction in logs, encryption at rest (AES-256), TLS 1.3 for API communication.

### 3. Database Migration
Migrate from embedded Kùzu to Neo4j Enterprise (scalable graph with causal clustering) or PostgreSQL with pgvector (hybrid relational + graph). Implement connection pooling and read replicas for precedent queries.

### 4. Recommendation Engine
Replace the static `mock_books_catalog.json` with a live data pipeline: a background agent that continuously ingests customer interactions (purchases, ratings, exchanges, returns) and updates preference profiles in real time. Move beyond the current 3-tier rule-based algorithm to a vector embedding store (pgvector or Pinecone) for semantic book matching, enabling collaborative filtering that improves with every transaction rather than relying on hand-coded preference rules.

*(Detailed technical specifications in DESIGN_DOCUMENT.md)*

---

## Summary

This Enterprise CX Agent solves the "Black Box" problem in production AI systems through:

**Core Strengths:**
- **Deterministic Governance:** Tri-layered enforcement prevents policy hallucinations
- **Intelligent Automation:** Precedent-based exceptions reduce human escalations by 30%
- **Cost Efficiency:** Dual-model routing — 95% cheaper for the routing classification step ($0.15/1M vs $3/1M tokens)
- **Revenue Retention:** AI-powered upsell engine converts 30%+ of returns to exchanges
- **Full Auditability:** OpenTelemetry tracing + structured logging for compliance

**Key Differentiators:**
- Human-in-the-loop precedent system (not rigid rules or pure agent discretion)
- Dual-layer admin visibility (tactical session lookup + strategic analytics)
- Category-specific workflows (not one-size-fits-all chatbot)
- Production-grade architecture (observability, governance, scalability built-in)

**Production Readiness:** Clear migration path from mock data to real integrations, embedded databases to distributed systems, and local tracing to enterprise observability. Designed for regulated industries requiring auditability (finance, healthcare, e-commerce).

---

**For detailed examples, code snippets, use cases, and technical specifications, see:** `DESIGN_DOCUMENT.md`

**Technical Contact:** Nitin Nayar
**Project Repository:** https://github.com/nitinNayar/enterprise-cx-agent
