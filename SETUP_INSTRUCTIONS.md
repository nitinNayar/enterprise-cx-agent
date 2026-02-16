# Setup Instructions - Bookly AI Agent

**Get the agent running in 5 minutes**

---

## Prerequisites

- ✅ Python 3.10 or higher
- ✅ Anthropic API Key ([Get one here](https://console.anthropic.com/))

---

## Quick Setup

### Step 1: Install Dependencies

```bash
# Clone repository (if not already cloned)
git clone https://github.com/nitinnayar/enterprise-cx-agent.git
cd enterprise-cx-agent

# Install Python packages
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed anthropic chainlit kuzu python-dotenv opentelemetry-api arize-phoenix ...
```

---

### Step 2: Configure API Key

Create a `.env` file in the project root:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." > .env
```

**Or manually:**
1. Copy `.env.example` to `.env`
2. Edit `.env` and paste your API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```

---

### Step 3: Initialize Precedent Database

```bash
python scripts/init_graph.py
```

**Expected output:**
```
✅ Schema created successfully!
  → Converting PREC-VIP-001 (VIP Read Book)...
  → Converting PREC-HOL-002 (Holiday Gift Book)...
  → Converting PREC-AUDIO-003 (Book Club VIP Audiobook)...
  ✅ 3 precedents converted successfully

📊 Database Summary:
  - 3 Decisions
  - 3 People
  - 9 Tags
  - 3 MADE relationships
  - 15 HAS_CONTEXT relationships

🎉 Precedent graph database initialized at: data/context_graph_db
```

---

### Step 4: Start Observability (Optional but Recommended)

**Open Terminal 1:**

```bash
python -m phoenix.server.main serve
```

**Expected output:**
```
🌍 To view the Phoenix app, open: http://localhost:6006/
```

**Keep this terminal running** and open http://localhost:6006 in your browser.

---

### Step 5: Start the Agent

**Open Terminal 2 (or same terminal if skipping Phoenix):**

```bash
chainlit run app.py -w
```

**Expected output:**
```
Your app is available at http://localhost:8000
```

The Chainlit UI will automatically open in your browser at http://localhost:8000.

---

## Using the Agent

### Select Chat Profile

When the UI opens, you'll see two profiles:

1. **Bookly Support** - Customer-facing agent
   - Choose this to interact as a customer
   - Test returns, order tracking, policy questions

2. **Bookly Admin** - Decision trace viewer
   - Choose this to investigate agent sessions
   - View precedent matches, decision attribution

**For demo:** Select "Bookly Support"

---

## Demo Scenarios

### Scenario 1: Simple Return (Happy Path)

```
You: I want to return my order ORD-123
Agent: [Greets you as John McClane, Gold VIP]
       "Could you please tell me why you'd like to return this item?"
You: Changed my mind, book is unopened
Agent: "Good news! Your return is approved ✓"
```

**What to observe:**
- ✅ Personalized greeting with VIP acknowledgment
- ✅ Asks for return reason (mandatory)
- ✅ Asks about book condition
- ✅ Approves based on policy compliance

---

### Scenario 2: VIP Exception (The "Wow" Moment) ⭐

**Start a new chat** (click "New Chat" button)

```
You: I want to return order ORD-777
Agent: [Greets you as Sarah Connor, Platinum VIP, 10 years]
       "To process this return, I need to confirm: is the item still
       sealed in its original packaging, or has it been opened?"
You: I opened it and read the first chapter, but it wasn't what I expected
Agent: [Policy says DENY (read book + signed edition)]
       [Automatically checks VIP status]
       [Queries precedent graph]
       [Finds precedent: DEC-2024-001 by VP Customer Experience]

       "✅ Return approved and processed!

       **Important: This is a special exception to our standard policy**

       [Explains exception, conditions, attribution]"
```

**What to observe:**
- ✅ Agent automatically checks VIP status (doesn't wait for customer to mention it)
- ✅ Queries precedent graph for similar cases
- ✅ Finds human decision (DEC-2024-001 by Sarah Chen, VP)
- ✅ Applies exception with clear conditions
- ✅ Complete transparency about the decision

---

### Scenario 3: Late Return (Policy Denial)

**Start a new chat**

```
You: I need to return order ORD-456
Agent: [Greets you as Jason Bourne, regular customer]
You: The book is in perfect condition, I just forgot about it
Agent: [Checks policy: 30-day window]
       [Order is 45 days old]
       [Automatically checks VIP status: NOT VIP]
       [No precedent found]

       "I understand you'd like to return this book. However, our
       return policy requires returns within 30 days of delivery.
       Since this order was delivered 45 days ago, I'm unable to
       process the return."
```

**What to observe:**
- ✅ Policy enforcement for regular customers
- ✅ Automatic VIP check (even though customer isn't VIP)
- ✅ Polite, clear explanation of policy
- ✅ No arbitrary decisions

---

### Scenario 4: View Decision Trace

**If you started Phoenix (Terminal 1):**

1. Open http://localhost:6006
2. Click **"Traces"** tab
3. Find the Sarah Connor trace (ORD-777)
4. Click to expand
5. View the waterfall:
   - Tool calls in sequence
   - `check_precedents` query
   - Precedent result with attribution
   - Final response

**What to observe:**
- ✅ Complete visibility into agent's decision process
- ✅ Every tool call logged with inputs/outputs
- ✅ Precedent query and match visible
- ✅ Attribution to human decision maker (Sarah Chen, VP)

---

## Troubleshooting

### Error: "Order ID not found"

**Problem:** Trying to use a non-existent order ID
**Solution:** Use one of the test order IDs:
- `ORD-123` - John McClane (Gold VIP, simple return)
- `ORD-456` - Jason Bourne (Regular, late return)
- `ORD-777` - Sarah Connor (Platinum VIP, read book exception)
- `ORD-888` - Jack Ryan (Regular, holiday gift exception)

See `data/mock_orders.json` for all available orders.

---

### Error: "Graph DB not initialized"

**Problem:** Precedent database not created
**Solution:** Run the initialization script:
```bash
python scripts/init_graph.py
```

---

### Error: "ANTHROPIC_API_KEY not found"

**Problem:** API key not configured
**Solution:** Create `.env` file with your API key:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." > .env
```

---

### Phoenix not showing traces

**Problem:** Phoenix must be started BEFORE the agent
**Solution:** Restart in correct order:

1. Stop the agent (Ctrl+C in Terminal 2)
2. Terminal 1: `python -m phoenix.server.main serve`
3. Wait for "To view the Phoenix app, open: http://localhost:6006/"
4. Terminal 2: `chainlit run app.py -w`

---

### Agent giving unexpected responses

**Check logs:**
```bash
# View console logs
tail -f logs/console.log

# View audit logs
tail -f logs/decision_audit.log
```

**Verify configuration:**
```bash
# Check config.py
cat config.py | grep TEMPERATURE
# Should show: TEMPERATURE: float = 0.0

cat config.py | grep MODEL_NAME
# Should show: MODEL_NAME: str = "claude-sonnet-4-5-20250929"
```

---

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_specialized_routing.py

# Run with verbose output
pytest tests/ -v
```

---

## What's Next?

### Explore the Code

**Key files to review:**
- `AGENT_DESIGN_DOCUMENT.md` - Architecture overview
- `prompts.py` - System prompts (1100+ lines)
- `agent/agent.py` - Agent core logic
- `services/services.py` - Tool implementations
- `router/router.py` - Question routing

### Modify and Experiment

**Add a new order:**
1. Edit `data/mock_orders.json`
2. Add order with structure:
   ```json
   "ORD-XXX": {
     "order_id": "ORD-XXX",
     "customer_id": "CUST-001",
     "items": ["Book Title"],
     "status": "delivered",
     "eligible_for_return": true,
     "days_since_purchase": 10
   }
   ```

**Add a new precedent:**
1. Create email file in `data/decision_emails/`
2. Update `scripts/init_graph.py` to include new precedent
3. Run `python scripts/init_graph.py` to reinitialize

---

## Support

**Documentation:**
- `SUBMISSION_GUIDE.md` - Complete submission overview
- `docs/DEMO_GUIDE.md` - Full demo script
- `docs/TECHNICAL_OVERVIEW.md` - Detailed technical docs

**Issues:**
- GitHub Issues: https://github.com/nitinnayar/enterprise-cx-agent/issues

---

## Summary

You now have:
- ✅ A running AI agent with intelligent routing
- ✅ Precedent-based exception handling
- ✅ Complete observability via Phoenix
- ✅ Multiple demo scenarios to explore

**Estimated setup time:** 5 minutes
**Demo time:** 15 minutes
**Deep dive time:** 1+ hours

Enjoy exploring the Bookly AI Agent! 🎉
