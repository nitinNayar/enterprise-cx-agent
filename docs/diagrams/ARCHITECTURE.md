# Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Layer"
        UI[Chainlit UI<br/>localhost:8000]
        CustomerProfile[TrueCart Support<br/>Customer Facing]
        AdminProfile[TrueCart Admin<br/>Decision Trace Viewer]
        UI --> CustomerProfile
        UI --> AdminProfile
    end

    subgraph "Application Layer"
        Agent[Agent Core<br/>SupportAgent class]
        ReActLoop[ReAct Loop<br/>Reason + Action]
        History[Conversation History<br/>Session Management]

        CustomerProfile --> Agent
        AdminProfile --> AdminReviewer[Admin Decision Reviewer]
        Agent --> ReActLoop
        Agent --> History

        ToolRouter[Tool Router<br/>7 Tool Definitions]
        ReActLoop --> ToolRouter
    end

    subgraph "Service Layer"
        Services[EnterpriseServices<br/>Stateless Business Logic]
        ToolRouter --> Services

        OrderLookup[look_up_order]
        CustomerInfo[get_customer_info]
        VIPCheck[check_vip_status]
        PolicyInfo[get_policy_info]
        PrecedentCheck[check_precedents]
        ExecuteReturn[execute_order_return]
        Escalate[escalate_to_human]

        Services --> OrderLookup
        Services --> CustomerInfo
        Services --> VIPCheck
        Services --> PolicyInfo
        Services --> PrecedentCheck
        Services --> ExecuteReturn
        Services --> Escalate
    end

    subgraph "Data Layer"
        MockOMS[(Mock OMS<br/>JSON)]
        MockCustomers[(Mock Customers<br/>JSON)]
        Policies[(Policy Docs<br/>.md files)]
        Graph[(Context Graph<br/>Kùzu DB)]

        OrderLookup --> MockOMS
        CustomerInfo --> MockCustomers
        VIPCheck --> MockCustomers
        PolicyInfo --> Policies
        PrecedentCheck --> Graph
    end

    subgraph "Observability Layer"
        Phoenix[Arize Phoenix<br/>localhost:6006]
        OTEL[OpenTelemetry<br/>Traces]
        AuditLog[Audit Logs<br/>JSONL]
        ConsoleLog[Console Logs<br/>Text]

        Agent -.-> OTEL
        Services -.-> OTEL
        OTEL -.-> Phoenix

        Agent -.-> AuditLog
        Services -.-> AuditLog
        Agent -.-> ConsoleLog
        Services -.-> ConsoleLog
    end

    subgraph "External Integrations (Mocked)"
        Stripe[Payment Gateway]
        Zendesk[Ticketing System]
        CRM[CRM System]

        ExecuteReturn -.-> Stripe
        Escalate -.-> Zendesk
        VIPCheck -.-> CRM
    end

    style Agent fill:#2b5e82,stroke:#fff,color:#fff
    style Graph fill:#5a2b82,stroke:#fff,color:#fff
    style Policies fill:#ff9900,stroke:#333,color:#000
    style Phoenix fill:#333,stroke:#f66,stroke-width:2px,color:#fff
```

## ReAct Loop Flow

```mermaid
flowchart TD
    Start([User Input]) --> Init[Initialize/Update<br/>Conversation History]
    Init --> Loop{ReAct Loop}

    Loop --> CallClaude[Call Claude API<br/>with tools + history]
    CallClaude --> CheckStop{stop_reason?}

    CheckStop -->|end_turn| FinalText[Extract Final Text]
    FinalText --> AuditResponse[Log: AGENT_RESPONSE]
    AuditResponse --> Return([Return to User])

    CheckStop -->|tool_use| ExtractTools[Extract Tool Calls]
    ExtractTools --> AuditThinking[Log: AGENT_RESPONSE<br/>thinking]
    AuditThinking --> ExecuteTools[Execute All Tools]

    ExecuteTools --> Tool1{Tool Type?}

    Tool1 -->|look_up_order| OrderService[EnterpriseServices<br/>look_up_order]
    Tool1 -->|get_customer_info| CustomerService[EnterpriseServices<br/>get_customer_info]
    Tool1 -->|check_vip_status| VIPService[EnterpriseServices<br/>check_vip_status]
    Tool1 -->|get_policy_info| PolicyService[EnterpriseServices<br/>get_policy_info]
    Tool1 -->|check_precedents| PrecedentService[EnterpriseServices<br/>check_precedents]
    Tool1 -->|execute_order_return| RefundService[EnterpriseServices<br/>execute_refund]
    Tool1 -->|escalate_to_human| EscalateService[EnterpriseServices<br/>escalate_to_human]

    OrderService --> LogTool[Log: TOOL_CALL<br/>Log: TOOL_RESULT]
    CustomerService --> LogTool
    VIPService --> LogTool
    PolicyService --> LogTool
    PrecedentService --> LogTool
    RefundService --> LogTool
    EscalateService --> LogTool

    LogTool --> AddToHistory[Add Tool Results<br/>to History as 'user']
    AddToHistory --> Loop

    style CallClaude fill:#2b5e82,stroke:#fff,color:#fff
    style Loop fill:#ff9900,stroke:#333,color:#000
    style Return fill:#27ae60,stroke:#fff,color:#fff
```

## Data Flow - Complete Request Lifecycle

```mermaid
sequenceDiagram
    actor User
    participant UI as Chainlit UI
    participant Agent as SupportAgent
    participant Claude as Claude API
    participant Services as EnterpriseServices
    participant Graph as Kùzu Graph DB
    participant Data as Mock Data
    participant Audit as Audit Logger
    participant Phoenix as Phoenix UI

    User->>UI: "I want to return ORD-777"
    UI->>Agent: run(message)
    Agent->>Audit: Log USER_MESSAGE
    Agent->>Claude: messages.create()<br/>(system prompt + history + tools)
    Agent-->>Phoenix: OpenTelemetry Trace Start

    Note over Claude: Reasoning: Need order details
    Claude->>Agent: tool_use: look_up_order
    Agent->>Audit: Log TOOL_CALL
    Agent->>Services: look_up_order("ORD-777")
    Services->>Data: Query mock_orders.json
    Data-->>Services: Order details + customer_id
    Services->>Audit: Log TOOL_RESULT
    Services-->>Agent: {order details}

    Agent->>Claude: Add tool results to history
    Note over Claude: Reasoning: Need customer info for greeting
    Claude->>Agent: tool_use: get_customer_info
    Agent->>Audit: Log TOOL_CALL
    Agent->>Services: get_customer_info(customer_id)
    Services->>Data: Query mock_customers.json
    Data-->>Services: Customer details
    Services->>Audit: Log TOOL_RESULT
    Services-->>Agent: {customer_name, is_vip, tier, years_active}

    Agent->>Claude: Add tool results to history
    Note over Claude: Have enough info, output greeting
    Claude->>Agent: end_turn: "Hello [Name]!<br/>...greeting with items..."
    Agent->>Audit: Log AGENT_RESPONSE
    Agent->>UI: Display greeting
    UI->>User: Show personalized greeting

    User->>UI: "I opened them"
    UI->>Agent: run(message)
    Agent->>Audit: Log USER_MESSAGE
    Agent->>Claude: messages.create()

    Note over Claude: Need to check policy
    Claude->>Agent: tool_use: get_policy_info
    Agent->>Services: get_policy_info("returns")
    Services->>Data: Read policies/return_policy.md
    Data-->>Services: Policy text
    Services-->>Agent: {policy_text}

    Agent->>Claude: Add policy to history
    Note over Claude: Policy says DENY, check VIP automatically
    Claude->>Agent: tool_use: check_vip_status
    Agent->>Services: check_vip_status(customer_id)
    Services->>Data: Query mock_customers.json
    Data-->>Services: {is_vip: true, tier: "Gold"}
    Services->>Audit: Log VIP status
    Services-->>Agent: VIP details

    Agent->>Claude: Add VIP status to history
    Note over Claude: VIP + Policy Denial = Check Precedents
    Claude->>Agent: tool_use: check_precedents("vip socks opened")
    Agent->>Audit: Log PRECEDENT_QUERY
    Agent->>Services: check_precedents("vip socks opened")
    Services->>Graph: MATCH (Person)-[MADE]->(Decision)<br/>-[HAS_CONTEXT]->(Tag)
    Graph-->>Services: Found: DEC-2024-001
    Services->>Audit: Log PRECEDENT_MATCH<br/>(decision_id, person_name, person_role)
    Services-->>Agent: {found: true, decision: "APPROVE", ...}

    Agent->>Claude: Add precedent to history
    Note over Claude: Precedent authorizes exception, execute return
    Claude->>Agent: tool_use: execute_order_return
    Agent->>Services: execute_refund(order_id, reason)
    Services->>Services: record_decision_to_ledger<br/>(APPROVE, decision_id, person_id)
    Services->>Audit: Log AGENT_DECISION
    Services-->>Agent: {status: "success", transaction_id}

    Agent->>Claude: Add refund confirmation to history
    Note over Claude: Have all info, craft final response
    Claude->>Agent: end_turn: "✅ Return approved!<br/>**Special exception**<br/>... conditions ..."
    Agent->>Audit: Log AGENT_RESPONSE
    Agent->>Audit: Log PRECEDENT_CITED
    Agent-->>Phoenix: OpenTelemetry Trace End
    Agent->>UI: Display final response
    UI->>User: Show approval with exception notice

    Note over User,Phoenix: Complete audit trail logged:<br/>USER_MESSAGE → TOOL_CALL → PRECEDENT_MATCH<br/>→ AGENT_DECISION → AGENT_RESPONSE
```

## Precedent Matching Flow

```mermaid
flowchart TD
    Start([Agent detects:<br/>VIP + Policy Denial]) --> CallTool[Tool: check_precedents<br/>query_tags_str]

    CallTool --> ParseTags[Parse Tags<br/>Split by space<br/>Convert to lowercase]
    ParseTags --> Example["Example:<br/>'vip socks return exception'<br/>→ ['vip', 'socks', 'return', 'exception']"]

    Example --> GraphQuery[Graph Query:<br/>MATCH Person-Decision-Tag]

    GraphQuery --> FilterQuery{Apply Filters}
    FilterQuery --> Filter1[Tag IN input_tags]
    FilterQuery --> Filter2[expires_at = 'NEVER'<br/>OR expires_at > now]
    FilterQuery --> Filter3[confidence_score >= 0.7]

    Filter1 --> Aggregate[Aggregate:<br/>SUM relevance_scores<br/>per Decision]
    Filter2 --> Aggregate
    Filter3 --> Aggregate

    Aggregate --> Sort[Sort BY:<br/>1. match_score DESC<br/>2. authority_level DESC]

    Sort --> Limit[LIMIT 1<br/>Best match only]

    Limit --> HasResults{Results?}

    HasResults -->|Yes| Extract[Extract:<br/>• decision_id<br/>• decision_title<br/>• outcome APPROVE/DENY<br/>• reasoning<br/>• conditions<br/>• person_name<br/>• person_role<br/>• authority_level<br/>• match_score<br/>• confidence]

    Extract --> AuditMatch[Log: PRECEDENT_MATCH<br/>session_id, decision_id,<br/>person details]

    AuditMatch --> ReturnFound[Return:<br/>{found: true, ...}]

    HasResults -->|No| AuditNoMatch[Log: NO_PRECEDENT<br/>session_id, query_tags]

    AuditNoMatch --> ReturnNotFound[Return:<br/>{found: false}]

    ReturnFound --> AgentDecision{Agent Decision}
    ReturnNotFound --> AgentDecision

    AgentDecision -->|found=true<br/>outcome=APPROVE| ApplyException[Apply Exception:<br/>execute_order_return]
    AgentDecision -->|found=false| OfferEscalate[Offer Escalation:<br/>Human review needed]

    ApplyException --> RecordDecision[record_decision_to_ledger<br/>Link to precedent]
    OfferEscalate --> MaybeEscalate[escalate_to_human<br/>if customer agrees]

    RecordDecision --> End([End])
    MaybeEscalate --> End

    style GraphQuery fill:#5a2b82,stroke:#fff,color:#fff
    style AuditMatch fill:#27ae60,stroke:#fff,color:#fff
    style AuditNoMatch fill:#e74c3c,stroke:#fff,color:#fff
    style ApplyException fill:#27ae60,stroke:#fff,color:#fff
```

## Graph Database Schema

```mermaid
erDiagram
    Person ||--o{ MADE : "makes"
    MADE }o--|| Decision : "creates"
    Decision ||--o{ HAS_CONTEXT : "has"
    HAS_CONTEXT }o--|| Tag : "tagged_with"
    Decision ||--o{ APPLIES_TO : "applies_to"
    APPLIES_TO }o--|| Product : "affects"
    Decision ||--o{ CITES : "cites"
    CITES }o--|| Decision : "cited"

    Person {
        string id PK
        string name
        string email
        string role
        string department
        int authority_level
        string last_active
        string created_at
    }

    Decision {
        string id PK
        string title
        string context
        string outcome
        string reasoning
        string conditions
        string source_ref
        double confidence_score
        string expires_at
        string created_at
        string case_id
    }

    Tag {
        string name PK
        string category
        double weight
    }

    Product {
        string category_name PK
        string risk_level
        bool returnable_by_default
        bool requires_special_handling
        string description
    }

    MADE {
        string decision_timestamp
        bool is_override
    }

    HAS_CONTEXT {
        double relevance_score
    }

    APPLIES_TO {
        string specificity
    }

    CITES {
        string citation_reason
    }
```

## Conversation State Machine

```mermaid
stateDiagram-v2
    [*] --> Initial: User starts chat

    Initial --> AwaitingOrderID: Agent asks for order

    AwaitingOrderID --> OrderLookup: User provides order ID

    OrderLookup --> CustomerGreeting: look_up_order()<br/>get_customer_info()

    CustomerGreeting --> AwaitingContext: Agent greets + asks<br/>policy-specific question

    AwaitingContext --> PolicyCheck: User provides context<br/>(opened/sealed/reason)

    PolicyCheck --> PolicyCompliant: Policy allows
    PolicyCheck --> PolicyDenial: Policy denies

    PolicyCompliant --> ExecuteReturn: execute_order_return()

    PolicyDenial --> VIPCheck: check_vip_status()<br/>(AUTOMATIC)

    VIPCheck --> NotVIP: is_vip = false
    VIPCheck --> IsVIP: is_vip = true

    NotVIP --> DenyReturn: Polite denial<br/>Explain policy

    IsVIP --> PrecedentCheck: check_precedents()

    PrecedentCheck --> PrecedentFound: found = true<br/>outcome = APPROVE
    PrecedentCheck --> NoPrecedent: found = false

    PrecedentFound --> ExecuteException: execute_order_return()<br/>with exception notice

    NoPrecedent --> OfferEscalation: Acknowledge VIP<br/>Offer human review

    OfferEscalation --> UserChoice: Ask permission

    UserChoice --> Escalate: User agrees
    UserChoice --> DenyReturn: User declines

    Escalate --> CreateTicket: escalate_to_human()

    CreateTicket --> Complete: Provide ticket ID
    ExecuteReturn --> Complete: Provide transaction ID
    ExecuteException --> Complete: Provide transaction ID<br/>+ exception details
    DenyReturn --> Complete: Empathetic denial

    Complete --> [*]

    AwaitingOrderID --> Escalate: Angry sentiment detected
    AwaitingContext --> Escalate: Angry sentiment detected
    PolicyCheck --> Escalate: Angry sentiment detected

    note right of VIPCheck
        VIP check is AUTOMATIC
        when policy denies.
        Agent does NOT wait
        for customer to ask.
    end note

    note right of PrecedentCheck
        Graph query with tags.
        Only for VIP customers.
        Links to human decisions.
    end note

    note right of ExecuteException
        Response MUST include:
        - VIP acknowledgment
        - Exception notice
        - Conditions
        - Transaction details
    end note
```

## Multi-Layered Governance

```mermaid
flowchart TD
    UserRequest[User Requests Return] --> Layer1{Layer 1:<br/>Database Check}

    Layer1 --> DB_Flag[eligible_for_return flag]
    DB_Flag --> DBYes{True?}

    DBYes -->|Yes| Layer2[Layer 2:<br/>Policy Check]
    DBYes -->|No| CheckContext[Check Context<br/>Holiday? VIP?]

    Layer2 --> ReadPolicy[Read return_policy.md]
    ReadPolicy --> PolicyRules{Policy Allows?}

    PolicyRules -->|Yes| StandardApprove[✅ APPROVE<br/>Standard Return]
    PolicyRules -->|No| Conflict[⚠️ CONFLICT<br/>DB=Yes, Policy=No]

    Conflict --> PolicyWins[POLICY WINS<br/>Prime Directive]
    PolicyWins --> Layer3[Layer 3:<br/>Precedent Check]

    CheckContext -->|Holiday Exception| Layer3
    CheckContext -->|VIP Customer| Layer3
    CheckContext -->|Regular Customer<br/>No Special Context| StandardDeny

    Layer3 --> AutoVIPCheck[AUTOMATIC:<br/>check_vip_status]
    AutoVIPCheck --> IsVIP{VIP?}

    IsVIP -->|No| StandardDeny[❌ DENY<br/>Enforce Policy]
    IsVIP -->|Yes| GraphQuery[check_precedents<br/>Query Context Graph]

    GraphQuery --> MatchPrecedent{Precedent<br/>Found?}

    MatchPrecedent -->|Yes<br/>outcome=APPROVE| ExceptionApprove[✅ APPROVE<br/>Exception Override]
    MatchPrecedent -->|No| OfferEscalate[🎫 OFFER ESCALATION<br/>Human Review]

    ExceptionApprove --> Attribution[Include Attribution:<br/>• VIP tier<br/>• Years active<br/>• Exception notice<br/>• Conditions<br/>• Transaction ID]

    StandardApprove --> Execute1[execute_order_return]
    ExceptionApprove --> Execute2[execute_order_return<br/>+ record_decision]
    StandardDeny --> DenyMsg[Polite denial message]
    OfferEscalate --> EscalateOption[escalate_to_human<br/>if customer agrees]

    Execute1 --> RecordStandard[record_decision_to_ledger<br/>APPROVE, no precedent]
    Execute2 --> RecordException[record_decision_to_ledger<br/>APPROVE, link precedent]
    EscalateOption --> RecordEscalate[record_decision_to_ledger<br/>ESCALATE]

    RecordStandard --> AuditTrail[(Audit Log)]
    RecordException --> AuditTrail
    RecordEscalate --> AuditTrail
    DenyMsg --> NoAudit[No decision record<br/>Policy enforcement only]

    style Layer1 fill:#3498db,stroke:#fff,color:#fff
    style Layer2 fill:#ff9900,stroke:#333,color:#000
    style Layer3 fill:#5a2b82,stroke:#fff,color:#fff
    style StandardApprove fill:#27ae60,stroke:#fff,color:#fff
    style ExceptionApprove fill:#27ae60,stroke:#fff,color:#fff
    style StandardDeny fill:#e74c3c,stroke:#fff,color:#fff
    style Conflict fill:#e67e22,stroke:#fff,color:#fff
    style PolicyWins fill:#c0392b,stroke:#fff,color:#fff
```

## Tool Execution Flow

```mermaid
flowchart LR
    subgraph "Mandatory Sequence"
        T1[1. look_up_order<br/>MANDATORY FIRST]
        T2[2. get_customer_info<br/>MANDATORY SECOND]
        T3[3. Output Greeting<br/>STOP & WAIT]
    end

    T1 --> T2 --> T3

    subgraph "After Customer Response"
        T4[4. get_policy_info<br/>Before decisions]
    end

    T3 -.->|User responds| T4

    subgraph "Conditional Tools"
        T5{Policy Denies?}
        T6[check_vip_status<br/>AUTOMATIC]
        T7{is_vip?}
        T8[check_precedents<br/>Only for VIPs]
    end

    T4 --> T5
    T5 -->|Yes| T6
    T5 -->|No| Decision
    T6 --> T7
    T7 -->|Yes| T8
    T7 -->|No| Decision
    T8 --> Decision

    subgraph "Action Tools (Mutually Exclusive)"
        A1[execute_order_return<br/>✅ Approve]
        A2[escalate_to_human<br/>🎫 Escalate]
        A3[Text Only<br/>❌ Deny]
    end

    Decision{Decision} --> A1
    Decision --> A2
    Decision --> A3

    subgraph "Post-Action"
        L1[record_decision_to_ledger<br/>Audit trail]
        L2[Log: AGENT_DECISION]
    end

    A1 --> L1 --> L2
    A2 --> L1 --> L2

    style T1 fill:#e74c3c,stroke:#fff,color:#fff
    style T2 fill:#e74c3c,stroke:#fff,color:#fff
    style T3 fill:#e74c3c,stroke:#fff,color:#fff
    style T6 fill:#f39c12,stroke:#fff,color:#fff
    style A1 fill:#27ae60,stroke:#fff,color:#fff
    style A2 fill:#3498db,stroke:#fff,color:#fff
    style A3 fill:#95a5a6,stroke:#fff,color:#fff
```
