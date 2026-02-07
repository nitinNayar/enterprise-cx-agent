# Documentation Index

**Complete documentation for the Enterprise CX Agent system.**

---

## 📚 Documentation Structure

```
docs/
├── README.md                    ← You are here
├── TECHNICAL_OVERVIEW.md        ← Start here for deep technical understanding
├── QUICK_REFERENCE.md           ← Quick lookup for common tasks
├── BRANDING_GUIDE.md            ← UI/UX and branding guidelines
├── requirements-decision-ledger.md  ← Feature requirements
└── diagrams/
    ├── README.md                ← Diagram viewing guide
    └── ARCHITECTURE.md          ← Mermaid architecture diagrams
```

---

## 🎯 Start Here

### For Different Roles

**👨‍💻 Software Engineers**
1. Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Get started quickly
2. Then: [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Understand the system
3. View: [ReAct Loop Diagram](diagrams/ARCHITECTURE.md#react-loop-flow) - See agent logic
4. Study: `agent/agent.py` - Main implementation

**👨‍🔬 Data Engineers**
1. Read: [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Section: "Context Graph"
2. View: [Graph Database Schema](diagrams/ARCHITECTURE.md#graph-database-schema)
3. Explore: `scripts/init_graph.py` - Database initialization
4. Query: `python scripts/debug_graph.py` - Inspect data

**👨‍💼 Product Managers**
1. Read: [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Section: "Conversation Types"
2. View: [Conversation State Machine](diagrams/ARCHITECTURE.md#conversation-state-machine)
3. Test: Use scenarios from [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-test-scenarios)
4. Review: [EXPECTED_VIP_RESPONSE.md](../EXPECTED_VIP_RESPONSE.md) - Response quality

**🏗️ Architects**
1. Read: [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Full document
2. View: [System Architecture](diagrams/ARCHITECTURE.md#system-architecture-overview)
3. Study: [Multi-Layered Governance](diagrams/ARCHITECTURE.md#multi-layered-governance)
4. Review: Design decisions section

**👨‍⚖️ Compliance/Audit**
1. Read: [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Section: "Audit Trail"
2. View: [Data Flow Lifecycle](diagrams/ARCHITECTURE.md#data-flow---complete-request-lifecycle)
3. Inspect: `logs/decision_audit.log` - Complete audit trail
4. Use: Admin UI (TrueCart Admin profile) - Trace viewer

**🎨 Designers**
1. Read: [BRANDING_GUIDE.md](BRANDING_GUIDE.md) - Complete UI guidelines
2. View: `public/` directory - Brand assets
3. Test: Customer UI - Live interface
4. Review: `.chainlit/config.toml` - UI configuration

---

## 📖 Document Summaries

### [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md)
**350+ lines | Complete System Documentation**

**Contents:**
- Executive Summary
- System Architecture (all layers)
- Core Components (8 major components)
- Data Flow (request-response lifecycle)
- Conversation Types (7 scenarios with flows)
- Technical Deep Dives (ReAct loop, precedent matching, governance)
- Deployment & Dependencies
- Design Decisions & Rationale

**When to use:** Deep technical understanding, architecture decisions, implementation details

---

### [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**One-page | Quick Lookup Guide**

**Contents:**
- Quick start commands
- Debugging guide
- Component overview
- Tool execution order
- Test scenarios
- Common mistakes
- Monitoring commands

**When to use:** Daily development, debugging, quick lookup, testing

---

### [diagrams/ARCHITECTURE.md](diagrams/ARCHITECTURE.md)
**8 Mermaid Diagrams | Visual Documentation**

**Diagrams:**
1. System Architecture Overview
2. ReAct Loop Flow
3. Data Flow - Complete Request Lifecycle (sequence)
4. Precedent Matching Flow
5. Graph Database Schema (ERD)
6. Conversation State Machine
7. Multi-Layered Governance
8. Tool Execution Flow

**When to use:** Visual learning, presentations, understanding flows, onboarding

---

### [BRANDING_GUIDE.md](BRANDING_GUIDE.md)
**UI/UX Guidelines**

**Contents:**
- Brand colors, typography, logo usage
- Component styling
- Customer-facing language
- Response templates

**When to use:** UI development, brand consistency, customer communications

---

### [requirements-decision-ledger.md](requirements-decision-ledger.md)
**Feature Requirements**

**Contents:**
- Decision ledger feature requirements
- Attribution system specs
- Audit log format

**When to use:** Feature development, requirements review

---

## 🔍 Finding Information

### By Topic

**Agent Behavior**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#agent-core-agentagentpy)
- [ReAct Loop Diagram](diagrams/ARCHITECTURE.md#react-loop-flow)
- [Conversation State Machine](diagrams/ARCHITECTURE.md#conversation-state-machine)

**Tools & Services**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#2-tool-system-toolstoolspy)
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#3-service-layer-servicesservicespy)
- [Tool Execution Flow](diagrams/ARCHITECTURE.md#tool-execution-flow)

**Data & Database**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#4-context-graph-datacontext_graph_db)
- [Graph Database Schema](diagrams/ARCHITECTURE.md#graph-database-schema)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-data-sources)

**Precedents & Exceptions**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#precedent-matching-algorithm)
- [Precedent Matching Flow](diagrams/ARCHITECTURE.md#precedent-matching-flow)
- [Multi-Layered Governance](diagrams/ARCHITECTURE.md#multi-layered-governance)

**Policies & Governance**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#multi-layered-governance-system)
- [Multi-Layered Governance](diagrams/ARCHITECTURE.md#multi-layered-governance)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-governance-layers)

**Audit & Compliance**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#session-tracking--audit-trail)
- [Data Flow Lifecycle](diagrams/ARCHITECTURE.md#data-flow---complete-request-lifecycle)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-audit-log-events)

**Observability & Debugging**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#7-observability-observabilitytracingy)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-debugging)

**Deployment & Setup**
- [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#deployment--dependencies)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-quick-start)
- [../README.md](../README.md#-quick-start)

---

## 🎓 Learning Path

### 1. Quick Start (30 minutes)
1. Read [../README.md](../README.md) - Project overview
2. Follow [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-quick-start) - Get system running
3. Test one scenario from [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-test-scenarios)
4. View trace in Phoenix UI

### 2. Understanding the System (2 hours)
1. Read [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Sections: Executive Summary, Architecture
2. View [System Architecture Diagram](diagrams/ARCHITECTURE.md#system-architecture-overview)
3. Read [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Section: Core Components
4. View [ReAct Loop Diagram](diagrams/ARCHITECTURE.md#react-loop-flow)
5. Test 2-3 scenarios, watch in Phoenix

### 3. Deep Dive (4 hours)
1. Read [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Complete document
2. View all diagrams in [diagrams/ARCHITECTURE.md](diagrams/ARCHITECTURE.md)
3. Read source code:
   - `agent/agent.py` - Main logic
   - `services/services.py` - Tool implementations
   - `config.py` - System prompt
4. Explore graph database: `python scripts/debug_graph.py`
5. Test all scenarios, inspect audit logs

### 4. Contributing (Ongoing)
1. Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-common-mistakes)
2. Check [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md#known-limitations)
3. Read [BRANDING_GUIDE.md](BRANDING_GUIDE.md) if touching UI
4. Test changes with Phoenix observability
5. Verify audit logs for new features

---

## 🔧 Development Workflow

### Making Changes

**1. Changing Agent Behavior**
- Edit: `config.py` (system prompt)
- Test: Run scenario in Chainlit
- Verify: Check Phoenix trace
- Validate: Check audit log

**2. Adding New Tool**
- Define: `tools/tools.py` (add schema)
- Implement: `services/services.py` (add method)
- Wire: `agent/agent.py` (add elif branch)
- Document: Update [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md)
- Test: Create test scenario

**3. Adding Precedent**
- Create: Email file in `data/decision_emails/`
- Add: To `scripts/init_graph.py`
- Run: `python scripts/init_graph.py`
- Test: VIP scenario that uses it
- Verify: Check graph with `debug_graph.py`

**4. Modifying Policies**
- Edit: `policies/*.md`
- Test: Scenario that exercises policy
- Verify: Agent follows new rules
- Document: Note changes in git commit

**5. Changing UI**
- Edit: `app.py`, `.chainlit/config.toml`
- Follow: [BRANDING_GUIDE.md](BRANDING_GUIDE.md)
- Test: Both customer and admin profiles
- Verify: Responsive on different screen sizes

---

## 📊 Metrics & KPIs

### System Health
- ✅ All tests passing (`pytest`)
- ✅ Phoenix traces showing
- ✅ Audit logs populating
- ✅ Graph queries < 100ms

### Agent Quality
- 📈 Policy compliance rate > 95%
- 📈 VIP detection rate = 100%
- 📈 Precedent match accuracy > 90%
- 📈 Inappropriate escalations < 5%

### User Experience
- 📈 First response time < 2s
- 📈 Complete resolution time < 30s
- 📈 Customer satisfaction (simulated) > 4.5/5

---

## 🆘 Getting Help

### Debugging Steps
1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-debugging)
2. View Phoenix UI trace
3. Read `logs/console.log`
4. Check `logs/decision_audit.log`
5. Run `python scripts/debug_graph.py`

### Common Issues
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md#common-issues)
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-common-mistakes)

### Still Stuck?
- Review [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) relevant section
- Check GitHub issues
- Review demo video in [../README.md](../README.md)

---

## 📝 Contributing to Docs

### Documentation Standards

**When adding new features:**
1. Update [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) - Add to relevant section
2. Update [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Add quick reference
3. Create diagram if needed in [diagrams/ARCHITECTURE.md](diagrams/ARCHITECTURE.md)
4. Add test scenario to [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-test-scenarios)

**Documentation style:**
- Clear, concise, technical but readable
- Include code examples
- Add diagrams for complex flows
- Link between related documents
- Keep QUICK_REFERENCE.md to one page

**Diagram style:**
- Use Mermaid syntax
- Follow color conventions (see [diagrams/README.md](diagrams/README.md))
- Add annotations for critical decisions
- Test rendering in GitHub preview

---

## 🔗 External Links

**Technologies Used:**
- [Claude API](https://docs.anthropic.com/claude/reference) - LLM provider
- [Chainlit](https://docs.chainlit.io) - Chat UI framework
- [Kùzu Database](https://kuzudb.com) - Graph database
- [OpenTelemetry](https://opentelemetry.io) - Observability standard
- [Arize Phoenix](https://docs.arize.com/phoenix) - LLM observability

**Related Concepts:**
- [ReAct Pattern](https://arxiv.org/abs/2210.03629) - Reasoning + Acting
- [Tool Use in LLMs](https://www.anthropic.com/research/tool-use) - Function calling
- [Graph RAG](https://arxiv.org/abs/2404.16130) - Graph-based retrieval

---

## 📅 Version History

- **v1.0** (Feb 2026) - Initial documentation release
  - Complete technical overview
  - 8 architecture diagrams
  - Quick reference guide
  - Branding guidelines

---

## 📧 Feedback

This is a demo/interview project. For questions or feedback:
- Review the code and documentation
- Check demo videos in main README
- Understand this is a proof-of-concept, not production-ready

---

*Documentation maintained by: Nitin Nayar*
*Last Updated: February 2026*
*Generated with: Claude Sonnet 4.5*
