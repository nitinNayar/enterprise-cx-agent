# Quick Reference Guide

**One-page reference for common tasks, debugging, and system understanding.**

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Initialize database
python scripts/init_graph.py

# 4. Start Phoenix (Terminal 1)
python -m phoenix.server.main serve

# 5. Start app (Terminal 2)
chainlit run app.py -w
```

**Access:**
- Customer UI: http://localhost:8000 (select "TrueCart Support")
- Admin UI: http://localhost:8000 (select "TrueCart Admin")
- Phoenix: http://localhost:6006

---

## 🔍 Debugging

### View Agent Decision Trace

**Method 1: Phoenix UI**
1. Go to http://localhost:6006
2. Click "Traces" tab
3. Select most recent trace
4. View waterfall of API calls and tool executions

**Method 2: Admin Interface**
1. Start new chat, select "TrueCart Admin"
2. Enter session ID (e.g., `SESSION-a1b2c3d4`)
3. View formatted decision trace with precedent attribution

**Method 3: Raw Logs**
```bash
# Console logs (human-readable)
tail -f logs/console.log

# Audit logs (JSON, machine-readable)
tail -f logs/decision_audit.log | jq '.'

# Find specific session
cat logs/decision_audit.log | jq 'select(.session_id == "SESSION-a1b2c3d4")'
```

### Common Issues

**Issue: "Graph DB not initialized"**
```bash
python scripts/init_graph.py
```

**Issue: "ANTHROPIC_API_KEY not found"**
```bash
# Check .env file exists
cat .env

# Or set in shell
export ANTHROPIC_API_KEY=sk-ant-...
```

**Issue: Agent not using precedents**
```bash
# Check graph database has data
python scripts/debug_graph.py
```

**Issue: Phoenix not showing traces**
```bash
# Ensure Phoenix is running first
python -m phoenix.server.main serve

# Then restart app
chainlit run app.py -w
```

---

## 🛠️ System Components

| Component | File | Purpose |
|-----------|------|---------|
| **Agent Core** | `agent/agent.py` | Main ReAct loop, decision-making |
| **Tools** | `tools/tools.py` | 7 tool schemas |
| **Services** | `services/services.py` | Tool implementations |
| **Config** | `config.py` | System prompt (SOP) |
| **Logging** | `logging_config.py` | Audit trail setup |
| **Tracing** | `observability/tracing.py` | OpenTelemetry config |
| **UI** | `app.py` | Chainlit interface |
| **Admin** | `admin/decision_reviewer.py` | Trace viewer |

---

## 📋 Tool Execution Order

### Mandatory Sequence
1. `look_up_order` - **ALWAYS FIRST** - Fetch order details
2. `get_customer_info` - **ALWAYS SECOND** - Get customer name, VIP status
3. **OUTPUT GREETING** - Send personalized message, then **STOP AND WAIT**

### After Customer Response
4. `get_policy_info` - Read return policy

### Conditional (Automatic)
5. `check_vip_status` - **AUTOMATIC** if policy denies
6. `check_precedents` - Only if VIP + policy denied

### Action (One of)
7. `execute_order_return` - Approve return
8. `escalate_to_human` - Create ticket
9. **Text only** - Deny (no tool call)

---

## 🎯 Conversation Types

| Scenario | Flow | Outcome |
|----------|------|---------|
| **Standard Return** | Order → Customer → Policy → Execute | ✅ APPROVE |
| **Late Return (Regular)** | Order → Customer → Policy | ❌ DENY |
| **Late Return (VIP)** | Order → Customer → Policy → VIP → Precedents | ✅ APPROVE (exception) |
| **Final Sale (Regular)** | Order → Customer → Policy → VIP (no) | ❌ DENY |
| **Final Sale (VIP)** | Order → Customer → Policy → VIP → Precedents | ✅ APPROVE (exception) |
| **Angry Customer** | Detect keywords | 🎫 ESCALATE |
| **Opened Electronics (Regular)** | Order → Customer → Policy → VIP (no) | ❌ DENY |
| **Opened Electronics (VIP)** | Order → Customer → Policy → VIP → Precedents | ✅ APPROVE or 🎫 ESCALATE |

---

## 🗄️ Data Sources

### Mock Orders (`data/mock_orders.json`)
```json
{
  "ORD-123": {
    "status": "delivered",
    "items": ["Wireless Headphones"],
    "eligible_for_return": true,
    "customer_id": "CUST-REG-0001"
  }
}
```

### Mock Customers (`data/mock_customers.json`)
```json
{
  "CUST-VIP-0001": {
    "customer_name": "Jessica Williams",
    "is_vip": true,
    "tier": "Gold",
    "lifetime_value": 50000,
    "years_active": 10
  }
}
```

### Policies (`policies/*.md`)
- `return_policy.md` - Return rules, non-returnable categories
- `shipping_policy.md` - Shipping information
- `privacy_policy.md` - Privacy rules

### Context Graph (`data/context_graph_db/`)
- **Nodes:** Person, Decision, Tag, Product
- **Edges:** MADE, HAS_CONTEXT, APPLIES_TO, CITES
- **Seeded Decisions:** 3 precedents (VIP socks, holiday gifts, opened tech)

---

## 📊 Graph Database

### Query Precedents
```bash
python scripts/debug_graph.py
```

Or use Python:
```python
import kuzu
db = kuzu.Database("data/context_graph_db")
conn = kuzu.Connection(db)

# Find all decisions
result = conn.execute("""
    MATCH (p:Person)-[m:MADE]->(d:Decision)
    RETURN p.name, p.role, d.title, d.outcome
""")

while result.has_next():
    print(result.get_next())
```

### Add New Precedent

1. Create email file in `data/decision_emails/`
2. Edit `scripts/init_graph.py` to add new decision
3. Re-run: `python scripts/init_graph.py`

---

## 🔐 Governance Layers

### Layer 1: Database (Lowest Priority)
- `eligible_for_return: true/false`
- Fast initial check
- Can be overridden

### Layer 2: Policy (Medium Priority)
- `policies/return_policy.md`
- **ALWAYS wins over database**
- Explicit rules: "Socks → ACTION: REJECT"

### Layer 3: Precedents (Highest Priority)
- Context Graph decisions
- Human-approved exceptions
- Only for VIPs or special circumstances

**Resolution:** Precedents > Policy > Database

---

## 📝 Audit Log Events

| Event Type | Meaning |
|------------|---------|
| `USER_MESSAGE` | Customer sent message |
| `AGENT_RESPONSE` | Agent replied (thinking or final) |
| `TOOL_CALL` | Agent called a tool |
| `TOOL_RESULT` | Tool returned data |
| `PRECEDENT_QUERY` | Searching for precedent |
| `PRECEDENT_MATCH` | Precedent found |
| `NO_PRECEDENT` | No precedent found |
| `AGENT_USING_PRECEDENT` | Precedent will be applied |
| `PRECEDENT_CITED` | Precedent mentioned to customer |
| `AGENT_DECISION` | Final decision (APPROVE/DENY/ESCALATE) |

---

## 🧪 Test Scenarios

### Scenario 1: Simple Return
```
Order: ORD-123 (Headphones)
Customer: Regular
Status: Delivered, within 30 days, unopened
Expected: ✅ APPROVE
```

### Scenario 2: VIP Exception
```
Order: ORD-777 (Socks - Final Sale)
Customer: CUST-VIP-9921 (Gold VIP, 10 years)
Expected: ✅ APPROVE (exception via DEC-2024-001)
```

### Scenario 3: Policy Denial
```
Order: ORD-777 (Socks - Final Sale)
Customer: Regular (not VIP)
Expected: ❌ DENY (policy enforced)
```

### Scenario 4: Escalation
```
Message: "This is a SCAM! I want my money NOW!"
Expected: 🎫 ESCALATE (immediate, no policy check)
```

### Scenario 5: Opened Electronics
```
Order: ORD-222 (Headphones - opened)
Customer: Regular
Expected: ❌ DENY (policy: electronics must be unopened)
```

### Scenario 6: Holiday Exception
```
Order: ORD-888 (45 days old)
Customer: "It was a holiday gift"
Expected: ✅ APPROVE (holiday exception via DEC-2024-002)
```

---

## 🔧 Configuration

### Model Settings (`config.py`)
```python
MODEL_NAME = "claude-sonnet-4-5-20250929"  # Latest Sonnet
MAX_TOKENS = 1024
TEMPERATURE = 0.0  # Deterministic (no randomness)
```

### System Prompt
- 239 lines
- Defines Standard Operating Procedure (SOP)
- Includes customer greeting protocol
- VIP exception handling rules
- Response templates

---

## 📈 Monitoring

### Key Metrics

**Success Rate:**
```bash
cat logs/decision_audit.log | jq 'select(.event_type == "AGENT_DECISION")' | jq '.agent_decision' | sort | uniq -c
```

**Precedent Usage:**
```bash
cat logs/decision_audit.log | jq 'select(.event_type == "PRECEDENT_MATCH")' | wc -l
```

**Average Response Time:**
Check Phoenix UI → Traces → Duration column

**Escalation Rate:**
```bash
cat logs/decision_audit.log | jq 'select(.event_type == "AGENT_DECISION" and .agent_decision == "ESCALATE")' | wc -l
```

---

## 🔗 Documentation Links

- **[TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md)** - Complete system documentation
- **[diagrams/ARCHITECTURE.md](diagrams/ARCHITECTURE.md)** - Mermaid diagrams
- **[BRANDING_GUIDE.md](BRANDING_GUIDE.md)** - UI/UX guidelines
- **[EXPECTED_VIP_RESPONSE.md](../EXPECTED_VIP_RESPONSE.md)** - Response templates
- **[README.md](../README.md)** - Project overview

---

## 💡 Pro Tips

1. **Always read logs first** - Check `logs/console.log` before debugging code
2. **Use Phoenix for visualization** - Easier than reading raw traces
3. **Test with VIP customers** - Most interesting behavior happens there
4. **Check graph database** - Run `scripts/debug_graph.py` to verify data
5. **Temperature = 0.0 matters** - Same input = same output (deterministic)
6. **Session IDs are key** - Use them to trace decisions in admin UI
7. **Policy always wins** - Even if DB says "eligible", policy can deny
8. **VIP checks are automatic** - Agent doesn't wait for customer to ask

---

## 🚨 Common Mistakes

❌ **Editing system prompt without restarting**
- Restart Chainlit after changing `config.py`

❌ **Forgetting to initialize graph**
- Run `python scripts/init_graph.py` after clone

❌ **Not starting Phoenix first**
- Phoenix must run before app for traces to work

❌ **Assuming customer state**
- Agent must ASK if item is opened, not assume

❌ **Skipping greeting step**
- Agent MUST greet after `get_customer_info`, then STOP

❌ **Mentioning decision maker names to customers**
- Internal only (Sarah Chen, etc.) - don't expose to users

---

*Last Updated: February 2026*
