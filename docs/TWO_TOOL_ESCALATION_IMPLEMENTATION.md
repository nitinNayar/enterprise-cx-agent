# Implementation Plan: Split escalate_to_human into Two Tools

**Issue:** C-2 - Tool schema contradiction (order_id marked "OPTIONAL" but required)
**Root Cause:** One tool serving two different contexts (order-related vs general)
**Solution:** Create two purpose-specific tools

---

## Why Two Tools Is The Right Approach

### Business Reality
- **Order escalations** go to Order Support team (2-4 hour SLA, needs order context)
- **General escalations** go to General Support team (24 hour SLA, no order context)
- These are DIFFERENT workflows with DIFFERENT requirements

### Technical Benefits
1. **Type Safety:** Each tool has appropriate required parameters
2. **Clear Intent:** Tool name signals context to LLM
3. **Better Routing:** Backend can route based on tool name
4. **Future Flexibility:** Can evolve independently
5. **Error Prevention:** Impossible to call with wrong parameters

---

## Implementation Steps

### Step 1: Add Two New Tools to tools/tools.py

**Location:** Add after the existing `escalate_to_human` tool (line 76)

```python
    # NEW TOOL 1: Order-specific escalation
    {
        "name": "escalate_order_issue",
        "description": "Escalate an order-related issue to the Order Support team. Use this when customer has an order ID and needs human assistance (angry customer, complex return dispute, delivery problem, VIP exception request, policy denial requiring manager review). This routes to specialized order support with full order context and higher SLA (2-4 hours).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The customer's order ID (e.g., 'ORD-123'). Required so support team can look up full order history, customer profile, and order context."
                },
                "reason": {
                    "type": "string",
                    "description": "Clear, detailed explanation of why escalating. Include key context. Examples: 'Customer is angry - delivery delayed 7+ days past estimate', 'VIP Gold customer requesting return exception for read book - precedent DEC-001 found', 'Customer disputing charge - claims book arrived damaged but no photo provided'"
                },
                "policy_check_confirmation": {
                    "type": "string",
                    "description": "Confirms you've verified this legitimately requires escalation. Always use 'verified_compliant'.",
                    "enum": ["verified_compliant"]
                }
            },
            "required": ["order_id", "reason", "policy_check_confirmation"]
        }
    },

    # NEW TOOL 2: General question escalation
    {
        "name": "escalate_general_question",
        "description": "Escalate a general question or account issue to the General Support team. Use this for non-order-related questions that you cannot answer (complex policy questions not in FAQs, account access problems, technical website issues, specific shipping questions like 'shipping to India'). This routes to general support queue with standard SLA (24 hours).",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Clear explanation of what customer needs help with and why you cannot answer. Examples: 'Customer asking about shipping policy to India - not covered in policy document', 'Account password reset failing - customer tried 3 times', 'Technical issue - payment page not loading in Safari browser', 'Customer wants to know if we ship perishable items - not in FAQ'"
                },
                "question_category": {
                    "type": "string",
                    "enum": ["policy_question", "account_issue", "technical_problem", "shipping_inquiry", "other"],
                    "description": "Category of the general question for proper routing to specialized support agent"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer's email address if they provided it (for follow-up). Optional but helpful for support team to contact customer."
                }
            },
            "required": ["reason", "question_category"]
        }
    },
```

**Note:** Keep the old `escalate_to_human` tool for now (backward compatibility during migration).

---

### Step 2: Update agent/agent.py Handlers

**Location:** In the `run()` method, add handlers after line 294

```python
                    elif tool_name == "escalate_order_issue":
                        result = EnterpriseServices.escalate_order_issue(
                            order_id=tool_input.get("order_id"),
                            reason=tool_input.get("reason"),
                            policy_check_confirmation=tool_input.get("policy_check_confirmation")
                        )

                        # Log tool result
                        audit_logger.info(
                            f"Order issue escalated for {tool_input.get('order_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'order_id': tool_input.get('order_id'),
                                'escalation_reason': tool_input.get('reason'),
                                'ticket_id': result.get('ticket_id') if result else None,
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                        # Record escalation to audit ledger
                        EnterpriseServices.record_decision_to_ledger(
                            order_id=tool_input.get("order_id"),
                            agent_decision="ESCALATE_ORDER",
                            rationale=tool_input.get("reason")
                        )

                    elif tool_name == "escalate_general_question":
                        result = EnterpriseServices.escalate_general_question(
                            reason=tool_input.get("reason"),
                            question_category=tool_input.get("question_category"),
                            customer_email=tool_input.get("customer_email")
                        )

                        # Log tool result
                        audit_logger.info(
                            f"General question escalated: {tool_input.get('question_category')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'question_category': tool_input.get('question_category'),
                                'ticket_id': result.get('ticket_id') if result else None,
                                'event_type': 'TOOL_RESULT'
                            }
                        )
```

---

### Step 3: Update services/services.py Backend

**Add two new methods:**

```python
    @staticmethod
    def escalate_order_issue(order_id: str, reason: str, policy_check_confirmation: str) -> dict:
        """
        Escalate an order-related issue to Order Support team.
        Routes to high-priority queue with full order context.
        """
        ticket_id = f"TICKET-ORDER-{uuid.uuid4().hex[:8].upper()}"

        # In production, this would:
        # - Create ticket in Order Support queue
        # - Include full order details from look_up_order(order_id)
        # - Set SLA to 2-4 hours
        # - Notify Order Support team

        return {
            "status": "escalated",
            "ticket_id": ticket_id,
            "queue": "order_support",
            "sla_hours": 4,
            "order_id": order_id,
            "message": f"Your request has been escalated to our Order Support team. Reference: {ticket_id}. A specialist will contact you within 2-4 hours."
        }

    @staticmethod
    def escalate_general_question(reason: str, question_category: str, customer_email: str = None) -> dict:
        """
        Escalate a general question to General Support team.
        Routes to standard queue without requiring order context.
        """
        ticket_id = f"TICKET-GEN-{uuid.uuid4().hex[:8].upper()}"

        # In production, this would:
        # - Create ticket in General Support queue
        # - Route based on question_category
        # - Set SLA to 24 hours
        # - Send confirmation email if customer_email provided

        return {
            "status": "escalated",
            "ticket_id": ticket_id,
            "queue": "general_support",
            "sla_hours": 24,
            "category": question_category,
            "message": f"Your question has been escalated to our support team. Reference: {ticket_id}. You'll receive a response within 24 hours" + (f" at {customer_email}" if customer_email else "") + "."
        }
```

---

### Step 4: Update prompts.py - All Three Prompts

#### 4A: ORDER_STATUS_PROMPT

**Replace existing escalate_to_human instructions (lines 54-75) with:**

```python
# ESCALATION PROTOCOL

**Escalate to order support if:**
- Customer is angry or frustrated
- Package is confirmed lost by carrier
- Delivery is significantly delayed (>7 days past estimate)
- Customer uses profanity or threatening language

**How to escalate:**
Call `escalate_order_issue` with THREE required parameters:
1. `order_id` (string): The customer's order ID
2. `reason` (string): Clear explanation of why you're escalating
3. `policy_check_confirmation` (enum): MUST be set to "verified_compliant"

**Example:**
```
escalate_order_issue(
    order_id="ORD-123",
    reason="Customer is frustrated - package confirmed lost by carrier, needs immediate resolution",
    policy_check_confirmation="verified_compliant"
)
```

**Note:** `policy_check_confirmation` confirms you've verified this is a legitimate escalation need. Always use "verified_compliant" as the value.
```

**Update AVAILABLE TOOLS section:**

```python
# AVAILABLE TOOLS

You have access to:

1. **`look_up_order`** - Get order details
   - Parameters: `order_id` (required)

2. **`get_customer_info`** - Get customer information for greeting
   - Parameters: `customer_id` (required, from look_up_order result)

3. **`escalate_order_issue`** - Escalate order-related issues to Order Support
   - Parameters:
     - `order_id` (required)
     - `reason` (required)
     - `policy_check_confirmation` (required, must be "verified_compliant")

Use these tools to help customers track their book orders efficiently.
```

#### 4B: RETURNS_REFUNDS_PROMPT

**Update Step 9 and Step 11 (lines 528-550) to use new tool:**

```python
10. **Risk Assessment:** If customer is angry or uses abusive language → Escalate immediately
   - Call `escalate_order_issue` with:
     ```
     escalate_order_issue(
         order_id="...",
         reason="Customer is [angry/frustrated/using abusive language] - requires human support",
         policy_check_confirmation="verified_compliant"
     )
     ```
   - Do NOT continue with return processing
   - Inform customer: "I'm going to transfer you to a specialist who can help resolve this right away."

11. **Decision Logic:**

   **IF Policy ALLOWS (from Step 8):**
   - You have condition + reason + policy compliance
   - Proceed to Step 12 (Approval flow)

   **IF Policy DENIES (from Step 8):**
   - Check VIP status and precedents (see AUTOMATIC VIP CHECK section above)
   - If customer is VIP AND you haven't asked return reason yet: Ask now for precedent checking
   - If VIP exception found: Proceed to Step 12 (Approval flow)
   - If no exception possible: Escalate for manager review using:
     ```
     escalate_order_issue(
         order_id="...",
         reason="VIP customer requesting return exception - no precedent found for [situation]. Customer has been [tier] VIP for [years] years.",
         policy_check_confirmation="verified_compliant"
     )
     ```
   - If non-VIP: Politely deny and explain policy
```

**Update VIP no precedent section (line 208-220):**

```python
4. IF customer is VIP but no precedent is found:
   - Acknowledge their VIP status
   - Explain that this particular exception requires human review
   - Offer to escalate to a manager
   - If customer agrees, call:
     ```
     escalate_order_issue(
         order_id="...",
         reason="VIP [tier] customer (member for [years] years) requesting exception for [item type]. Situation: [describe policy violation]. No matching precedent found. Customer remains polite and reasonable.",
         policy_check_confirmation="verified_compliant"
     )
     ```
```

**Update AVAILABLE TOOLS section:**

```python
6. **`escalate_order_issue`** - Escalate order-related issues to Order Support
   - Parameters:
     - `order_id` (required)
     - `reason` (required)
     - `policy_check_confirmation` (required, must be "verified_compliant")
```

#### 4C: GENERAL_PROMPT

**Replace escalation protocol (lines 658-693) with:**

```python
# ESCALATION PROTOCOL

**Escalate to general support if:**
- Customer is frustrated or angry
- Question requires account system access
- Technical issue is beyond basic troubleshooting
- Question involves sensitive personal information
- Policy question not covered in available policy documents

**How to escalate:**

Use `escalate_general_question` with:

```
escalate_general_question(
    reason="[Clear explanation of what customer needs and why you cannot help]",
    question_category="[policy_question|account_issue|technical_problem|shipping_inquiry|other]",
    customer_email="[customer email if available]"
)
```

**Examples:**

**Example 1: Policy Question**
```
Customer: "Do you ship to India? What are the customs fees?"
You: [Check get_policy_info("shipping") → No information about India]
You: "Let me connect you with our shipping specialist who can provide specific details about shipping to India and customs fees."

escalate_general_question(
    reason="Customer asking about shipping policy to India including customs fees - not covered in available policy documents",
    question_category="shipping_inquiry",
    customer_email="customer@email.com"
)
```

**Example 2: Account Issue**
```
Customer: "I've tried resetting my password 3 times but not receiving the email"
You: "I'm going to escalate this to our technical support team who can check your account."

escalate_general_question(
    reason="Customer unable to receive password reset email after 3 attempts - needs account system access to diagnose",
    question_category="account_issue",
    customer_email="customer@email.com"
)
```

**Example 3: Technical Problem**
```
Customer: "Your checkout page keeps crashing on Safari"
You: "I'm connecting you with our technical team to investigate this issue."

escalate_general_question(
    reason="Customer experiencing checkout page crash on Safari browser - requires technical investigation",
    question_category="technical_problem"
)
```

**Note:** If customer mentions an order ID during the conversation, you can use `look_up_order` to get context, but still use `escalate_general_question` if the question itself is general (not about that specific order).
```

**Update AVAILABLE TOOLS section:**

```python
# AVAILABLE TOOLS

You have access to:

1. **`get_policy_info`** - Retrieve policy documents
   - Parameters: `policy_type` (required, enum: "shipping", "returns", "privacy")

2. **`escalate_general_question`** - Escalate general questions to General Support
   - Parameters:
     - `reason` (required)
     - `question_category` (required, enum: "policy_question", "account_issue", "technical_problem", "shipping_inquiry", "other")
     - `customer_email` (optional but recommended)

Use these tools to provide accurate policy information and helpful guidance.
```

---

### Step 5: Update get_tools_for_category() Function

**Location:** prompts.py lines 631-672

```python
def get_tools_for_category(category):
    """
    Return the appropriate tool set for a given category.
    """
    from router.router import QuestionCategory

    if category == QuestionCategory.ORDER_STATUS:
        return [
            "look_up_order",
            "get_customer_info",
            "escalate_order_issue"  # Changed from escalate_to_human
        ]

    elif category == QuestionCategory.RETURNS_REFUNDS:
        return [
            "look_up_order",
            "get_customer_info",
            "get_policy_info",
            "execute_order_return",
            "escalate_order_issue",  # Changed from escalate_to_human
            "check_vip_status",
            "check_precedents",
            "get_book_recommendations",
            "process_exchange"
        ]

    elif category == QuestionCategory.GENERAL:
        return [
            "get_policy_info",
            "escalate_general_question"  # Changed from escalate_to_human
        ]

    else:
        return None
```

---

## Edge Cases & How They're Handled

### Case 1: Customer starts with general question, then mentions order

**Scenario:**
```
Customer: "Do you ship to India?"
[GENERAL agent, no order_id]
Customer: "Actually, I have order ORD-123, can you check if it's eligible?"
```

**Solution:**
- Agent can call `look_up_order("ORD-123")` mid-conversation
- Now has order context
- If needs escalation: Use `escalate_order_issue` (has order_id now)

### Case 2: Customer has order but question is general

**Scenario:**
```
Customer: "I have order ORD-123 but my question is about your privacy policy"
```

**Solution:**
- Question is about privacy (general), not about order ORD-123
- Use `escalate_general_question` with question_category="policy_question"
- Mention order in reason if relevant: "Customer with order ORD-123 asking about privacy policy - not order-related"

### Case 3: Customer angry about order issue

**Scenario:**
```
Customer: "WHERE IS MY BOOK? This is RIDICULOUS!"
```

**Solution:**
- RETURNS_REFUNDS or ORDER_STATUS agent
- Has order_id from initial lookup
- Use `escalate_order_issue` with reason clearly stating customer is angry

### Case 4: Unclear if order-related or general

**Scenario:**
```
Customer: "I need help"
```

**Solution:**
- Ask clarifying question: "I'd be happy to help! Do you have an order number, or is this a general question?"
- Route to appropriate tool based on response

---

## Migration Path

### Week 1: Add new tools (non-breaking)
- ✅ Add two new tools to tools.py
- ✅ Add handlers to agent.py
- ✅ Add backend methods to services.py
- ✅ Update all prompts to use new tools
- ⚠️ Keep old `escalate_to_human` for backward compatibility

### Week 2: Monitor usage
- 📊 Monitor logs to ensure new tools being used
- 🐛 Fix any issues with new tools
- ✅ Verify no calls to old `escalate_to_human`

### Week 3: Deprecate old tool
- 🗑️ Mark `escalate_to_human` as deprecated in tools.py
- 📧 Announce removal timeline

### Week 4: Remove old tool
- ❌ Remove `escalate_to_human` from tools.py
- ❌ Remove handler from agent.py
- ✅ Cleanup complete

---

## Testing Checklist

### Test Scenario 1: ORDER_STATUS escalation
- [ ] Customer angry about delivery delay → Uses `escalate_order_issue`
- [ ] All required parameters provided (order_id, reason, policy_check_confirmation)
- [ ] Backend receives escalation with order context
- [ ] Ticket created in Order Support queue

### Test Scenario 2: RETURNS_REFUNDS escalation (VIP no precedent)
- [ ] VIP customer return denial → Uses `escalate_order_issue`
- [ ] Reason includes VIP tier and years
- [ ] Order_id included for context

### Test Scenario 3: GENERAL escalation (policy question)
- [ ] Customer asks about India shipping → Uses `escalate_general_question`
- [ ] question_category = "shipping_inquiry"
- [ ] No order_id required or provided
- [ ] Ticket created in General Support queue

### Test Scenario 4: GENERAL escalation (account issue)
- [ ] Password reset failing → Uses `escalate_general_question`
- [ ] question_category = "account_issue"
- [ ] customer_email provided if available

### Test Scenario 5: Edge case - general question with order mentioned
- [ ] Customer has order but asks about privacy policy
- [ ] Uses `escalate_general_question` (question is general)
- [ ] Reason can mention order for context but doesn't use escalate_order_issue

---

## Metrics to Track

Post-implementation, track:
1. **Tool usage**: escalate_order_issue vs escalate_general_question vs old tool
2. **Error rate**: Failed escalations due to missing parameters
3. **Routing accuracy**: Are escalations going to correct team?
4. **SLA compliance**: Order issues resolved in 2-4h? General in 24h?
5. **Customer satisfaction**: Survey after escalation resolution

---

## Summary

**The two-tool approach is superior because:**
1. ✅ Eliminates schema contradiction
2. ✅ Provides type safety
3. ✅ Makes intent clear to LLM
4. ✅ Enables proper backend routing
5. ✅ Allows independent evolution
6. ✅ Reflects business reality (two different support teams)

**Cons are manageable:**
- More tools to maintain → But each is simpler
- Agent might call wrong tool → Clear naming prevents this
- Prompt updates needed → We're already updating prompts

**Recommendation: Proceed with implementation.** The benefits far outweigh the costs.
