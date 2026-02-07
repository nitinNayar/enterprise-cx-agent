# Architecture Diagrams

This directory contains detailed Mermaid diagrams for visualizing the Enterprise CX Agent system architecture and workflows.

## Available Diagrams

### 1. System Architecture Overview
**File:** `ARCHITECTURE.md` - Section 1

A comprehensive view of all system layers:
- User Layer (Chainlit UI with profiles)
- Application Layer (Agent Core, ReAct Loop, Tool Router)
- Service Layer (EnterpriseServices with 7 tool implementations)
- Data Layer (Mock data, policies, Context Graph)
- Observability Layer (Phoenix, OpenTelemetry, Audit Logs)
- External Integrations (Mocked services)

### 2. ReAct Loop Flow
**File:** `ARCHITECTURE.md` - Section 2

Detailed flowchart showing:
- How the ReAct (Reason + Action) loop operates
- Decision points (end_turn vs tool_use)
- Tool routing and execution
- Conversation history management
- Audit logging at each step

### 3. Data Flow - Complete Request Lifecycle
**File:** `ARCHITECTURE.md` - Section 3

Sequence diagram showing a complete VIP exception scenario:
- User input to final response
- Every API call to Claude
- All tool executions
- Database queries
- Precedent matching
- Decision recording
- Complete audit trail

**Use this to understand:** How a complex exception case flows through the entire system.

### 4. Precedent Matching Flow
**File:** `ARCHITECTURE.md` - Section 4

Flowchart of the graph-based precedent matching algorithm:
- Tag parsing and normalization
- Graph query construction
- Filtering (expiration, confidence)
- Weighted scoring and aggregation
- Authority level tie-breaking
- Decision application logic

**Use this to understand:** How the Context Graph finds relevant historical decisions.

### 5. Graph Database Schema
**File:** `ARCHITECTURE.md` - Section 5

Entity-Relationship diagram showing:
- Node types (Person, Decision, Tag, Product)
- Relationship types (MADE, HAS_CONTEXT, APPLIES_TO, CITES)
- Attributes for each entity
- Cardinality of relationships

**Use this to understand:** The data model for storing precedents.

### 6. Conversation State Machine
**File:** `ARCHITECTURE.md` - Section 6

State diagram showing:
- All possible conversation states
- Transitions between states
- Decision points (VIP check, precedent check)
- Exit conditions (approve, deny, escalate)
- Angry customer fast-path

**Use this to understand:** How conversations progress from start to finish.

### 7. Multi-Layered Governance
**File:** `ARCHITECTURE.md` - Section 7

Flowchart showing the 3-tier governance system:
- Layer 1: Database flags (lowest priority)
- Layer 2: Policy documents (medium priority)
- Layer 3: Context Graph precedents (highest priority)
- Conflict resolution logic
- Exception approval flow

**Use this to understand:** How the system enforces policies while allowing human-approved exceptions.

### 8. Tool Execution Flow
**File:** `ARCHITECTURE.md` - Section 8

Flowchart showing:
- Mandatory tool sequence (look_up_order → get_customer_info → greeting)
- Conditional tools (VIP check, precedent check)
- Action tools (execute, escalate, deny)
- Post-action audit logging

**Use this to understand:** The order and conditions for tool execution.

---

## How to View These Diagrams

### Option 1: GitHub (Recommended)
GitHub automatically renders Mermaid diagrams in markdown files. Just view `ARCHITECTURE.md` on GitHub.

### Option 2: VS Code
Install the "Markdown Preview Mermaid Support" extension:
```bash
code --install-extension bierner.markdown-mermaid
```
Then open `ARCHITECTURE.md` and use "Markdown: Open Preview" (Cmd+K V).

### Option 3: Mermaid Live Editor
1. Go to https://mermaid.live/
2. Copy/paste any diagram code
3. View and export as PNG/SVG

### Option 4: Export to Images

Using Mermaid CLI:
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Export all diagrams
mmdc -i ARCHITECTURE.md -o architecture-diagrams.pdf
```

---

## Diagram Conventions

### Colors
- **Blue (#2b5e82):** Agent/Claude components
- **Purple (#5a2b82):** Graph database components
- **Orange (#ff9900):** Policy/configuration components
- **Green (#27ae60):** Successful outcomes (APPROVE)
- **Red (#e74c3c):** Denial outcomes (DENY)
- **Gray (#95a5a6):** Neutral actions
- **Dark (#333):** Observability components

### Node Shapes
- **Rectangles:** Processes, services, components
- **Rounded Rectangles:** Start/end states
- **Diamonds:** Decision points
- **Cylinders:** Databases, data storage
- **Dotted Lines:** Observability/logging (non-blocking)
- **Solid Lines:** Data flow, control flow

### Annotations
- **MANDATORY:** Required steps that cannot be skipped
- **AUTOMATIC:** Steps that happen without user request
- **CONDITIONAL:** Steps that depend on data/decisions

---

## Use Cases by Role

### For Software Engineers
- **Start with:** ReAct Loop Flow, Tool Execution Flow
- **Understand:** How the agent makes decisions step-by-step

### For Data Engineers
- **Start with:** Graph Database Schema, Data Flow Lifecycle
- **Understand:** How data is stored and queried

### For Product Managers
- **Start with:** Conversation State Machine, Multi-Layered Governance
- **Understand:** Customer journey and policy enforcement

### For Architects
- **Start with:** System Architecture Overview
- **Understand:** Component interaction and system boundaries

### For Compliance/Audit
- **Start with:** Data Flow Lifecycle, Multi-Layered Governance
- **Understand:** Decision traceability and audit trail

---

## Related Documentation

- **[TECHNICAL_OVERVIEW.md](../TECHNICAL_OVERVIEW.md):** Complete technical documentation
- **[README.md](../../README.md):** Project overview and quick start
- **[EXPECTED_VIP_RESPONSE.md](../../EXPECTED_VIP_RESPONSE.md):** Example response formats
- **[BRANDING_GUIDE.md](../BRANDING_GUIDE.md):** UI/UX guidelines

---

*Last Updated: February 2026*
*Generated with: Claude Sonnet 4.5*
