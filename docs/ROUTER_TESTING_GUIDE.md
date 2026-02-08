# Question Router Testing Guide

## Overview

This guide provides comprehensive testing instructions for the Bookly Question Router, which classifies user questions into three categories:
1. **ORDER_STATUS** - Order tracking and delivery inquiries
2. **RETURNS_REFUNDS** - Return processing and refund requests
3. **GENERAL** - Policy questions, account help, and FAQs

---

## Quick Start Testing

### Prerequisites

1. **Environment Setup**
   ```bash
   # Ensure you're in the project root
   cd /Users/nitinnayar/projects/enterprise-cx-agent

   # Activate virtual environment (if using one)
   source enterprise-cx-agent/bin/activate  # or your venv path

   # Install dependencies
   pip install -r requirements.txt

   # Set up API key
   echo "ANTHROPIC_API_KEY=your-key-here" > .env
   ```

2. **Start the Application**
   ```bash
   # Terminal 1: Start observability (optional but recommended)
   python -m phoenix.server.main serve

   # Terminal 2: Start Bookly
   chainlit run app.py -w
   ```

3. **Access the UI**
   - Open http://localhost:8000
   - Select "Bookly Support" chat profile

---

## Test Suite 1: Router Classification Accuracy

### Test Category: ORDER_STATUS

Test these questions and verify they're classified as ORDER_STATUS:

| Test # | Input | Expected Category | Notes |
|--------|-------|-------------------|-------|
| OS-1 | "Where is my order?" | ORDER_STATUS | Basic tracking query |
| OS-2 | "Has my order ORD-123 shipped?" | ORDER_STATUS | Order ID reference |
| OS-3 | "When will my books arrive?" | ORDER_STATUS | Delivery inquiry |
| OS-4 | "Track my package" | ORDER_STATUS | Direct tracking request |
| OS-5 | "I haven't received my order yet" | ORDER_STATUS | Delivery concern |
| OS-6 | "What's the status of order ORD-456?" | ORDER_STATUS | Status with order ID |
| OS-7 | "Can you check on my shipment?" | ORDER_STATUS | Shipment inquiry |
| OS-8 | "My tracking number isn't working" | ORDER_STATUS | Tracking issue |

**How to Verify:**
1. Send each test message in the chat
2. Check the console logs for: `Question classified as: ORDER_STATUS`
3. Or check Phoenix traces at http://localhost:6006

### Test Category: RETURNS_REFUNDS

Test these questions and verify they're classified as RETURNS_REFUNDS:

| Test # | Input | Expected Category | Notes |
|--------|-------|-------------------|-------|
| RR-1 | "I want to return a book" | RETURNS_REFUNDS | Basic return request |
| RR-2 | "How do I get a refund?" | RETURNS_REFUNDS | Refund inquiry |
| RR-3 | "Process a return for ORD-789" | RETURNS_REFUNDS | Return with order ID |
| RR-4 | "I need to return order ORD-123" | RETURNS_REFUNDS | Return request |
| RR-5 | "Can I exchange this book?" | RETURNS_REFUNDS | Exchange query |
| RR-6 | "Cancel my order please" | RETURNS_REFUNDS | Cancellation request |
| RR-7 | "I want my money back" | RETURNS_REFUNDS | Refund request |
| RR-8 | "The book arrived damaged" | RETURNS_REFUNDS | Damage claim (return) |
| RR-9 | "Wrong book was delivered" | RETURNS_REFUNDS | Wrong item (return) |
| RR-10 | "I already read the book, can I return it?" | RETURNS_REFUNDS | Return with condition |

**How to Verify:**
1. Send each test message in the chat
2. Check the console logs for: `Question classified as: RETURNS_REFUNDS`
3. Agent should initiate return/refund workflow

### Test Category: GENERAL

Test these questions and verify they're classified as GENERAL:

| Test # | Input | Expected Category | Notes |
|--------|-------|-------------------|-------|
| GE-1 | "What's your shipping policy?" | GENERAL | Policy question |
| GE-2 | "How do I reset my password?" | GENERAL | Account help |
| GE-3 | "Do you sell audiobooks?" | GENERAL | Product inquiry |
| GE-4 | "How much is shipping?" | GENERAL | Shipping cost query |
| GE-5 | "What's your return policy?" | GENERAL | Policy (not active return) |
| GE-6 | "Can I change my email address?" | GENERAL | Account management |
| GE-7 | "Do you ship internationally?" | GENERAL | Shipping question |
| GE-8 | "How do I join the book club?" | GENERAL | Membership question |
| GE-9 | "Can you recommend a book?" | GENERAL | Recommendation request |
| GE-10 | "What are your business hours?" | GENERAL | General info |
| GE-11 | "I can't log in to my account" | GENERAL | Login issue |
| GE-12 | "How do I use a gift card?" | GENERAL | Gift card question |

**How to Verify:**
1. Send each test message in the chat
2. Check the console logs for: `Question classified as: GENERAL`
3. Agent should reference policy documents or provide general information

---

## Test Suite 2: Edge Cases & Ambiguous Queries

### Ambiguous Questions

These questions could belong to multiple categories. Test that the router makes reasonable decisions:

| Test # | Input | Primary Category | Secondary Category | Expected |
|--------|-------|------------------|-------------------|----------|
| AMB-1 | "I have a question about my order return" | RETURNS_REFUNDS | ORDER_STATUS | RETURNS_REFUNDS (return prioritized) |
| AMB-2 | "Can you help me?" | GENERAL | Any | GENERAL (default) |
| AMB-3 | "Order ORD-123" | ORDER_STATUS | N/A | ORDER_STATUS |
| AMB-4 | "I want to know about return shipping" | GENERAL | RETURNS_REFUNDS | GENERAL (policy, not active return) |
| AMB-5 | "Track my return" | RETURNS_REFUNDS | ORDER_STATUS | RETURNS_REFUNDS |
| AMB-6 | "What's the status of my refund?" | RETURNS_REFUNDS | ORDER_STATUS | RETURNS_REFUNDS |

### Empty and Invalid Inputs

| Test # | Input | Expected Behavior |
|--------|-------|-------------------|
| INV-1 | "" (empty string) | Default to GENERAL, handle gracefully |
| INV-2 | "???" | Default to GENERAL |
| INV-3 | "asdfghjkl" (gibberish) | Default to GENERAL, may ask for clarification |
| INV-4 | Very long message (1000+ words) | Should still classify correctly |

### Special Characters and Formatting

| Test # | Input | Expected Behavior |
|--------|-------|-------------------|
| FMT-1 | "WHERE IS MY ORDER???" (caps, punctuation) | ORDER_STATUS (ignore formatting) |
| FMT-2 | "i want 2 return my book" (informal) | RETURNS_REFUNDS (understand intent) |
| FMT-3 | "Order #ORD-123 - where is it?" (mixed format) | ORDER_STATUS |

---

## Test Suite 3: End-to-End Workflow Testing

### Scenario 1: Order Status Full Flow

1. **Input:** "Where is my order ORD-123?"
2. **Expected:**
   - ✅ Router classifies as ORDER_STATUS
   - ✅ Agent calls `look_up_order` tool
   - ✅ Agent provides tracking information
   - ✅ Response includes delivery estimate

### Scenario 2: Return Request Full Flow

1. **Input:** "I want to return order ORD-456"
2. **Expected:**
   - ✅ Router classifies as RETURNS_REFUNDS
   - ✅ Agent calls `look_up_order` tool
   - ✅ Agent calls `get_customer_info` tool
   - ✅ Agent provides personalized greeting
   - ✅ Agent asks about item condition
   - ✅ Agent checks policy
   - ✅ Agent processes return or explains denial

### Scenario 3: General Question Full Flow

1. **Input:** "What's your shipping policy for international orders?"
2. **Expected:**
   - ✅ Router classifies as GENERAL
   - ✅ Agent calls `get_policy_info` tool or reads shipping_policy.md
   - ✅ Agent provides detailed shipping information
   - ✅ Response includes international shipping details

### Scenario 4: Password Reset Flow

1. **Input:** "How do I reset my password?"
2. **Expected:**
   - ✅ Router classifies as GENERAL
   - ✅ Agent references password_reset.md
   - ✅ Agent provides step-by-step instructions
   - ✅ Response includes troubleshooting tips

---

## Test Suite 4: Performance Testing

### Latency Testing

Measure router classification time:

```python
import time
from router.router import QuestionRouter

router = QuestionRouter()

test_questions = [
    "Where is my order?",
    "I want to return a book",
    "What's your shipping policy?"
]

for question in test_questions:
    start = time.time()
    category = router.classify_question(question)
    elapsed = time.time() - start
    print(f"{question}: {category.value} ({elapsed*1000:.0f}ms)")
```

**Expected Performance:**
- ✅ Classification time: < 500ms per query
- ✅ Average: 200-400ms
- ✅ No timeouts or errors

### Load Testing

Test with rapid sequential requests:

```python
# Send 100 questions in quick succession
for i in range(100):
    category = router.classify_question("Where is my order?")
    assert category == QuestionCategory.ORDER_STATUS
```

**Expected:**
- ✅ All requests complete successfully
- ✅ No rate limiting issues
- ✅ Consistent classification results

---

## Test Suite 5: Cost Validation

### Verify Haiku Usage

Check logs to confirm router is using Haiku:

```bash
# Look for router initialization in logs
grep "QuestionRouter initialized" logs/app.log

# Should see: "QuestionRouter initialized with model: claude-haiku-4-5-20251001"
```

### Cost Estimation

Monitor API usage in Anthropic console:
- Router calls should use Haiku (cheaper)
- Agent calls should use Sonnet (more expensive)
- Verify cost breakdown

---

## Automated Testing Script

Save this as `tests/test_router.py`:

```python
import pytest
from router.router import QuestionRouter, QuestionCategory

@pytest.fixture
def router():
    return QuestionRouter()

class TestOrderStatus:
    """Test ORDER_STATUS classification"""

    def test_basic_tracking(self, router):
        assert router.classify_question("Where is my order?") == QuestionCategory.ORDER_STATUS

    def test_order_id_reference(self, router):
        assert router.classify_question("Track order ORD-123") == QuestionCategory.ORDER_STATUS

    def test_delivery_inquiry(self, router):
        assert router.classify_question("When will my books arrive?") == QuestionCategory.ORDER_STATUS

class TestReturnsRefunds:
    """Test RETURNS_REFUNDS classification"""

    def test_return_request(self, router):
        assert router.classify_question("I want to return a book") == QuestionCategory.RETURNS_REFUNDS

    def test_refund_inquiry(self, router):
        assert router.classify_question("How do I get a refund?") == QuestionCategory.RETURNS_REFUNDS

    def test_exchange_query(self, router):
        assert router.classify_question("Can I exchange this book?") == QuestionCategory.RETURNS_REFUNDS

class TestGeneral:
    """Test GENERAL classification"""

    def test_policy_question(self, router):
        assert router.classify_question("What's your shipping policy?") == QuestionCategory.GENERAL

    def test_password_reset(self, router):
        assert router.classify_question("How do I reset my password?") == QuestionCategory.GENERAL

    def test_product_inquiry(self, router):
        assert router.classify_question("Do you sell audiobooks?") == QuestionCategory.GENERAL

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message(self, router):
        result = router.classify_question("")
        assert result == QuestionCategory.GENERAL  # Should default to GENERAL

    def test_very_long_message(self, router):
        long_message = "I want to return " + "book " * 100 + "please"
        result = router.classify_question(long_message)
        assert result == QuestionCategory.RETURNS_REFUNDS

    def test_ambiguous_query(self, router):
        result = router.classify_question("Can you help me?")
        assert result == QuestionCategory.GENERAL  # Should default
```

**Run tests:**
```bash
pytest tests/test_router.py -v
```

---

## Monitoring & Analytics

### View Router Performance in Phoenix

1. Go to http://localhost:6006
2. Click "Traces" tab
3. Filter by "QuestionRouter"
4. View classification decisions and latency

### Check Console Logs

```bash
# View router classification logs
tail -f logs/app.log | grep "Question classified as"

# View routing audit logs
tail -f logs/audit.log | grep "QUESTION_ROUTED"
```

### Analytics Queries

Check routing distribution:
```bash
# Count classifications by category
grep "Question classified as" logs/app.log | cut -d: -f3 | sort | uniq -c
```

---

## Troubleshooting

### Router Not Working

**Symptom:** All questions go to same handler
**Solution:**
1. Check router initialization in logs
2. Verify Haiku API access
3. Check for import errors

### Incorrect Classifications

**Symptom:** Questions classified to wrong category
**Solution:**
1. Review router prompt in `router/router.py`
2. Add more examples to system prompt
3. Check for typos in category keywords

### Slow Performance

**Symptom:** Router takes > 1 second per query
**Solution:**
1. Check network latency to Anthropic API
2. Verify Haiku model is being used (not Sonnet)
3. Consider caching for repeated queries

### API Errors

**Symptom:** Router returns errors or defaults to GENERAL
**Solution:**
1. Verify ANTHROPIC_API_KEY is set
2. Check API quota and rate limits
3. Review error logs for specific error messages

---

## Success Criteria

The router implementation is successful if:

- ✅ **Accuracy:** 95%+ correct classifications on test suite
- ✅ **Performance:** < 500ms average latency
- ✅ **Reliability:** No errors or timeouts under normal load
- ✅ **Cost:** Using Haiku (not Sonnet) for classification
- ✅ **Integration:** Works seamlessly with existing agent
- ✅ **Monitoring:** Classifications logged and visible in Phoenix

---

## Next Steps

After testing:

1. **Monitor Production**: Track real-world classification accuracy
2. **Iterate Prompts**: Improve router prompt based on edge cases
3. **Add Categories**: Consider adding more specialized categories
4. **Optimize Costs**: Implement caching for repeated queries
5. **A/B Testing**: Compare router vs non-router performance

---

*Last Updated: February 2026*
*Version: 1.0 - Initial Router Testing Guide*
