# Comprehensive Prompt Engineering Review: prompts.py
**Date:** February 16, 2026
**Reviewer:** AI Code Review Agent
**Scope:** System prompts for ORDER_STATUS, RETURNS_REFUNDS, and GENERAL categories

---

## Executive Summary

This review identified **27 issues** across 4 severity levels in the prompts.py file. The most critical finding is a **consistent failure to document required tool parameters** across all three prompts, which could lead to runtime errors similar to the missing return_reason bug we just fixed.

**Issue Breakdown:**
- 🔴 **Critical (Immediate Fix Required):** 5 issues
- 🟠 **High Priority (Fix Before Production):** 8 issues
- 🟡 **Medium Priority (Consistency & Clarity):** 9 issues
- 🟢 **Low Priority (Enhancement):** 5 issues

---

## 🔴 CRITICAL ISSUES (Fix Immediately)

### C-1: Missing `policy_check_confirmation` Parameter in escalate_to_human (ALL PROMPTS)
**Location:** ORDER_STATUS (line 55), RETURNS_REFUNDS (lines 448, 184, 273), GENERAL (line 583)
**Severity:** Critical - Will cause tool call failures

**Problem:**
All three prompts instruct agents to use `escalate_to_human` but **never mention** the required `policy_check_confirmation` parameter. According to tools.py:74, this parameter is REQUIRED and must be set to the enum value `"verified_compliant"`.

**Why This Matters:**
Just like the missing `reason` parameter we fixed, the agent will attempt to call `escalate_to_human` without providing this required field, causing the tool call to fail. This will block escalations and leave customers stuck.

**Example of Current Failure:**
```python
# What agent tries to do (FAILS):
escalate_to_human(order_id="ORD-123", reason="Customer is angry")

# What's required (tools.py:74):
escalate_to_human(
    order_id="ORD-123",
    reason="Customer is angry",
    policy_check_confirmation="verified_compliant"  # ← MISSING!
)
```

**Root Cause:**
None of the prompts document the tool parameters. They list tool names (e.g., "1. `escalate_to_human` - Escalate if needed") but don't specify what parameters are required.

**Recommended Fix:**
1. Add a "TOOL PARAMETERS" section to each prompt listing required parameters for each tool
2. In escalation instructions, explicitly state: "When calling escalate_to_human, you must provide: order_id, reason, and policy_check_confirmation='verified_compliant'"
3. Explain WHY this parameter exists: "This confirms you've checked the policy before escalating"

---

### C-2: Tool Schema Contradiction - escalate_to_human order_id Field
**Location:** tools.py:66 vs tools.py:74
**Severity:** Critical - Schema inconsistency causes confusion

**Problem:**
The `escalate_to_human` tool has conflicting requirements:
- Line 66 (description): `"OPTIONAL order_id"`
- Line 74 (schema): `"required": ["order_id", "reason", "policy_check_confirmation"]`

**Why This Matters:**
The LLM reads both the description and schema. Conflicting information causes undefined behavior - the agent might skip order_id thinking it's optional, then fail when the API enforces it as required.

**Evidence:**
GENERAL_PROMPT may not have an order_id available (e.g., policy questions, account support), but tools.py:74 marks it as required. This makes escalation impossible from GENERAL category.

**Recommended Fix:**
1. Decide: Is order_id truly optional or required?
2. If optional: Update tools.py:74 to remove it from required list, add validation logic in backend
3. If required: Update tools.py:66 description to say "REQUIRED" and ensure GENERAL prompt collects order_id before escalating
4. Most likely: Make it optional and update schema accordingly

---

### C-3: RETURNS_REFUNDS Step 8 (Policy Check) Occurs Too Late
**Location:** prompts.py:446 (RETURNS_REFUNDS Step 8)
**Severity:** Critical - Workflow inefficiency and logic error

**Problem:**
The policy check happens AFTER asking the customer for:
1. Item condition (Step 4)
2. Return reason (Step 7)

**Current Flow:**
```
Step 4: Ask "Is the book in original condition?"
Step 5: Wait for answer → Customer: "Yes"
Step 7: Ask "Why do you want to return?"
Step 5: Wait for answer → Customer: "Changed my mind"
Step 8: Call get_policy_info ← CHECK POLICY HERE
```

**Why This Is Wrong:**
If `get_policy_info` reveals the item is **non-returnable** (e.g., digital products, gift cards), you've already wasted the customer's time collecting condition and reason information that won't be used.

**Example Scenario:**
- Customer wants to return a downloaded e-book
- Agent asks: "Have you downloaded it?" → Customer: "Yes"
- Agent asks: "Why return it?" → Customer: "Didn't like it"
- Agent checks policy → **Digital products are non-returnable once downloaded**
- Result: Customer frustrated they answered questions for nothing

**Recommended Flow:**
```
Step 4: Output greeting and condition question
Step 5: Wait for condition answer
Step 6: IMMEDIATELY call get_policy_info ← MOVE HERE
Step 7: IF policy allows, THEN ask return reason
Step 8: Proceed with approval/denial logic
```

**Additional Issue:**
Line 198 says "After the customer confirms the item condition **and you verify it meets policy**" - but policy isn't checked until Step 8! This creates a logical contradiction in the prompt itself.

---

### C-4: Missing Error Handling for Tool Failures
**Location:** All prompts
**Severity:** Critical - No recovery path when tools fail

**Problem:**
None of the prompts provide instructions for handling tool failures:
- What if `look_up_order` returns `{"error": "Order not found"}`?
- What if `get_customer_info` returns empty or null?
- What if `get_policy_info` call fails?
- What if `execute_order_return` returns an error?

**Why This Matters:**
Without error handling instructions, the agent will have undefined behavior. It might:
- Proceed with a null value and crash
- Hallucinate fake data
- Get stuck in a loop retrying the same failed call
- Provide confusing responses to the customer

**Example Current Failure:**
```
Agent: [Calls look_up_order("ORD-999")]
System: {"error": "Order not found", "found": false}
Agent: [Has no instruction on what to do]
Agent: [Might say] "Hello ! Thank you for being a customer for  years..." ← Broken output
```

**Recommended Fix:**
Add error handling section to each prompt:

```
## ERROR HANDLING

**If look_up_order returns error or not found:**
- Politely say: "I couldn't find that order number. Could you double-check the order ID?"
- Suggest checking confirmation email
- If customer insists it's correct, escalate to human

**If get_customer_info fails:**
- Proceed with generic greeting: "Hello! I can help you with your order."
- Continue workflow but skip personalization

**If get_policy_info fails:**
- Escalate to human with reason: "Unable to retrieve policy document"
- Do NOT proceed with approval/denial without policy

**If execute_order_return fails:**
- Inform customer there was a technical issue
- Escalate immediately with full context
```

---

### C-5: Ambiguous "Approval" vs "Processing" Terminology
**Location:** prompts.py:455-473 (RETURNS_REFUNDS Steps 11-12)
**Severity:** Critical - Logic confusion

**Problem:**
Step 11 says "IF RETURN IS APPROVED" and instructs agent to say "Your return is approved ✓" with refund details. But Step 12 is when `execute_order_return` is actually called.

**Why This Matters:**
The word "approved" is ambiguous:
1. **Decision made** (approval granted, but not yet processed)
2. **Transaction completed** (tool called, refund initiated)

The agent might think:
- "I said approved, so I don't need to call the tool"
- Or: "I called the tool, so I should say 'processed' not 'approved'"

**Evidence from Bug:**
In the bug we just fixed, the agent approved and offered upsell WITHOUT calling execute_order_return. This suggests the agent interpreted "approved" as the final state.

**Recommended Fix:**
Use precise terminology:

```
Step 11: DECISION PHASE (IF RETURN MEETS POLICY):

    **A. Inform customer of decision:**
    "Good news! Your return qualifies for approval ✓"
    [Provide refund details]

    **B. Offer recommendations (optional):**
    [Soft offer as currently written]

Step 12: EXECUTION PHASE:

    **CRITICAL:** The return is NOT complete until you call the tool!

    - If customer wants exchange → Call process_exchange WITH return_reason
    - If customer wants refund → Call execute_order_return WITH return_reason
    - ONLY AFTER tool call succeeds, say: "Your return has been processed"
```

---

## 🟠 HIGH PRIORITY ISSUES (Fix Before Production)

### H-1: Redundant VIP Status Checking
**Location:** prompts.py:148 (RETURNS_REFUNDS) vs line 425 (Step 3)
**Severity:** High - Inefficiency and potential data inconsistency

**Problem:**
The workflow calls `get_customer_info` in Step 3 (line 425), which likely returns VIP status (evident from greeting formats on lines 113-117 that mention VIP tiers). Then line 148 says to call `check_vip_status` again when a denial occurs.

**Why This Is Problematic:**
1. **Unnecessary API call** - VIP status already retrieved
2. **Data inconsistency risk** - What if get_customer_info says VIP=Gold but check_vip_status says VIP=false?
3. **Confusion** - Two sources of truth for same data

**Questions to Answer:**
- Does `get_customer_info` return VIP status or not?
- If yes: Remove check_vip_status and use cached data
- If no: Why does greeting mention VIP tier (lines 113-117)?

**Recommended Fix:**
1. Document what data each tool returns (add to prompt or create data schema doc)
2. If get_customer_info includes VIP status: Remove check_vip_status calls, use cached data
3. If separate calls needed: Explain WHY in prompt (e.g., "get_customer_info shows tier, check_vip_status shows real-time spend")

---

### H-2: Missing Validation for Ambiguous Customer Responses
**Location:** prompts.py:437 (RETURNS_REFUNDS Step 6)
**Severity:** High - Leads to incorrect decisions

**Problem:**
Step 6 says "confirm you have critical information about item condition" but doesn't specify what to do if customer's response is ambiguous.

**Example Problematic Responses:**
- Q: "Is the book in original condition?"
- A: "I think so" ← Ambiguous
- A: "Mostly" ← Ambiguous
- A: "What do you mean by original?" ← Needs clarification
- A: "I'm not sure" ← Insufficient information

**Why This Matters:**
Without clear guidance, agent might:
- Accept "I think so" as "Yes" and approve incorrectly
- Deny based on "mostly" when item might actually be returnable
- Proceed without sufficient information

**Recommended Fix:**
Add validation guidance:

```
Step 6: Information Validation

After customer responds to condition question:

**If response is CLEAR (Yes/No/specific details):**
- Proceed to Step 7

**If response is AMBIGUOUS ("I think so", "mostly", "probably"):**
- Ask clarifying question: "To confirm - does the book have any bent spines, markings, or signs of reading?"
- Wait for clearer response

**If customer is UNCERTAIN ("I'm not sure", "I don't know"):**
- Provide examples: "For example, can you check if the spine is straight and pages are unread?"
- If still uncertain after clarification: Escalate for photo verification

**If response is QUESTION ("What do you mean by original?"):**
- Provide definition from policy
- Re-ask condition question
```

---

### H-3: process_exchange return_reason Inconsistency
**Location:** prompts.py:331 vs line 470
**Severity:** High - Agent receives conflicting instructions

**Problem:**
Two different instructions for what `return_reason` should contain:

**Line 331 (in example):**
```
return_reason: Brief reason (e.g., "Customer exchanging for different title")
```
This suggests a generic, system-generated reason.

**Line 470 (in step 12):**
```
Call process_exchange (with return_reason from step 7)
```
This says to use the customer's actual reason collected in Step 7.

**Why This Matters:**
Agent doesn't know which instruction to follow. It might:
- Use generic "exchanging for different title" (loses customer's actual reason)
- Use customer's reason "I hate this book" (unprofessional in logs?)
- Get confused and make something up

**Recommended Fix:**
Clarify the intention and update both sections to match:

**Option 1 (Use actual customer reason):**
```
Line 331: return_reason: The actual return reason from Step 7 that customer provided
Line 470: ✓ Already correct
```

**Option 2 (Use formatted reason):**
```
Line 331: ✓ Already correct
Line 470: Call process_exchange with return_reason: "Customer exchanging for [new title] - Original reason: [customer's reason from step 7]"
```

Recommend **Option 1** for simplicity and data accuracy.

---

### H-4: No Guidance for Multiple Precedents with Conflicting Decisions
**Location:** prompts.py:160 (RETURNS_REFUNDS)
**Severity:** High - Undefined behavior on precedent conflicts

**Problem:**
Line 160 says "IF the Graph returns a precedent with decision: 'APPROVE'" but doesn't specify:
- What if multiple precedents are found?
- What if one precedent says "APPROVE" and another says "DENY"?
- What if precedent says "DENY" (not just absence of "APPROVE")?

**Why This Matters:**
The precedent database may contain multiple relevant cases. Without tie-breaking logic, agent behavior is undefined.

**Example Scenario:**
```
check_precedents("vip book read late") returns:
[
  {decision_id: "DEC-001", decision: "APPROVE", person_role: "Manager"},
  {decision_id: "DEC-002", decision: "DENY", person_role: "Supervisor"}
]
```
What should agent do?

**Recommended Fix:**
Add precedent handling logic:

```
3. IF check_precedents returns results:

   **A. Single precedent with "APPROVE":**
   - Proceed with exception approval as currently documented

   **B. Multiple precedents with ALL "APPROVE":**
   - Use the most recent precedent
   - Proceed with exception approval

   **C. Multiple precedents with MIXED decisions:**
   - Default to most restrictive (DENY)
   - Acknowledge VIP status: "I see you're a valued [tier] VIP"
   - Explain: "This situation requires manager review due to conflicting precedents"
   - Escalate with reason: "VIP return - conflicting precedents [DEC-001: APPROVE, DEC-002: DENY]"

   **D. Precedent exists with "DENY":**
   - Politely enforce denial
   - Acknowledge VIP status but explain precedent shows this exception was reviewed and denied previously
   - Offer to escalate if they want a new review

   **E. Precedent exists with other decision values:**
   - Treat as "no precedent found" (continue to step 4)
```

---

### H-5: Missing Instruction for Order ID Collection
**Location:** ORDER_STATUS (line 25), RETURNS_REFUNDS (line 421)
**Severity:** High - Conversation can get stuck

**Problem:**
Both prompts say "Get Order ID" as Step 1, but don't specify **how** to ask if customer doesn't provide it upfront.

**Why This Matters:**
Customer might say:
- "Where's my book?" ← No order ID provided
- "I want to return something" ← No order ID provided

Agent needs clear instruction on how to request it.

**Current State:**
- Step 1 just says "Get Order ID"
- No example phrasing
- No handling for when customer doesn't have it

**Recommended Fix:**
Expand Step 1:

```
Step 1: Order ID Collection

**If customer provides order ID in first message:**
- Extract it and proceed to Step 2
- Common formats: ORD-123, ORD-1234, order 123, #123

**If customer does NOT provide order ID:**
- Ask: "I'd be happy to help! Could you provide your order number? You can find it in your confirmation email or order history."
- Wait for response

**If customer says they don't have order ID:**
- Ask alternative identifiers: "No problem! What email address did you use for the order?"
- Or: "Do you remember approximately when you placed the order and what book it was?"
- Inform: "Let me check if I can find it - alternatively, you can log into your account at bookly.com/orders"
- If cannot proceed: Escalate to human support with reason "Customer unable to provide order ID"

**If customer provides invalid order ID format:**
- Gently correct: "Order IDs typically look like ORD-123. Could you double-check the format?"
```

---

### H-6: No Examples for Denial Scenarios
**Location:** prompts.py:358-417 (RETURNS_REFUNDS examples)
**Severity:** High - Agent under-trained for denial path

**Problem:**
Both example scenarios (Scenario 1 & 2) show **approved returns**. There are **zero examples** showing:
- Policy denial for non-VIP customer
- VIP check → No precedent → Escalation
- VIP check → Precedent found → Exception approval with conditions
- Customer becoming angry → Immediate escalation

**Why This Matters:**
Examples are crucial for LLM training. The agent learns primarily from examples. Without denial examples, the agent is under-trained on the most complex paths through the workflow.

**Evidence:**
The approval path is simple and has 2 examples. The denial path is complex (check VIP → check precedent → multiple outcomes) but has 0 examples. This imbalance means agent will be biased toward approvals.

**Recommended Fix:**
Add 3 more example scenarios:

```
**Scenario 3: Non-VIP Denial**

Customer: "I want to return my e-book"
Agent: [Greets, asks condition]
Customer: "I already downloaded it"
Agent: [Asks return reason]
Customer: "Didn't like it"
Agent: [Calls get_policy_info, sees digital products are non-returnable once downloaded]
Agent: [Calls check_vip_status → is_vip: false]
Agent: "I understand your concern. Unfortunately, our return policy doesn't allow returns for digital products once they've been downloaded. This ensures we can protect the content for authors while offering instant access.

Is there anything else I can help you with today?"

---

**Scenario 4: VIP Exception Granted via Precedent**

Customer: "I want to return this book but I read it already"
Agent: [Greets, asks condition]
Customer: "I read it, it's not in original condition"
Agent: [Asks return reason]
Customer: "Turned out to be completely different from the description"
Agent: [Calls get_policy_info → read books not returnable]
Agent: [Calls check_vip_status → is_vip: true, tier: "Platinum"]
Agent: [Calls check_precedents("vip book read misleading_description") → Found DEC-001: APPROVE]
Agent: "Thank you for being a valued Platinum VIP member for 4 years, Sarah.

While our standard policy doesn't allow returns for read books, I can make a one-time exception in this case as a courtesy to our VIP members. I've approved your return.

**Important:** This is a one-time exception. Future returns will need to follow standard policy (unread condition).

**Refund Details:**
[Standard refund details...]"

---

**Scenario 5: VIP No Precedent → Escalate**

Customer: "I want to return this gift card"
Agent: [Greets, asks condition]
Customer: "It's unused"
Agent: [Asks return reason]
Customer: "Bought wrong amount"
Agent: [Calls get_policy_info → gift cards are non-returnable]
Agent: [Calls check_vip_status → is_vip: true, tier: "Gold"]
Agent: [Calls check_precedents("vip gift_card unused wrong_amount") → No precedents found]
Agent: "Thank you for being a valued Gold VIP member for 3 years, Michael.

Our standard policy doesn't cover returns on gift cards. However, as a VIP member, I'd like to escalate your request to our VIP support team who can review your specific situation.

Would you like me to escalate this for a manager review?"
Customer: "Yes please"
Agent: [Calls escalate_to_human]
"I've escalated your case. A VIP support specialist will contact you within 24 hours at your email on file (m***@email.com). Your case reference is [ticket_id].

Is there anything else I can help you with?"
```

---

### H-7: Missing Collection of Order ID in GENERAL Prompt
**Location:** prompts.py:548-549 (GENERAL)
**Severity:** High - Escalation will fail

**Problem:**
GENERAL_PROMPT line 548 says if customer wants return, tell them "please let me know the order number and I'll transfer you to our returns team."

But:
1. There's no "transfer" tool - only `escalate_to_human`
2. `escalate_to_human` requires `order_id` (tools.py:74)
3. No instruction on what to do after customer provides order_id

**Why This Matters:**
1. Agent doesn't know how to "transfer" (no such tool exists)
2. If agent calls escalate_to_human without order_id, it will fail
3. Customer experience is broken - they're told to provide order_id but nothing happens after

**Recommended Fix:**
Clarify the handoff process:

```
**Do NOT handle:**
- ❌ **Active Returns/Refunds:** If customer wants to return an item:

  STEP 1: Collect order ID
  "I can help you with that! Could you provide your order number so I can transfer you to our returns team?"

  STEP 2: After customer provides order_id
  - Acknowledge: "Thank you! Let me transfer you to our returns specialist."
  - Escalate with: escalate_to_human(
      order_id=[customer's order ID],
      reason="Customer requesting return - transferring from GENERAL to RETURNS",
      policy_check_confirmation="verified_compliant"
    )

  STEP 3: Confirm
  "I've transferred your request to our returns team. They'll continue assisting you with order [order_id]."
```

---

### H-8: Greeting Timing Inconsistency Between ORDER_STATUS and RETURNS_REFUNDS
**Location:** ORDER_STATUS (line 28-37) vs RETURNS_REFUNDS (line 427-433)
**Severity:** High - User experience inconsistency

**Problem:**
The two prompts have different instructions for when to greet and what to include:

**ORDER_STATUS (lines 28-37):**
- Says to greet AFTER calling get_customer_info
- Greeting includes tracking information immediately: "I can help you track your order [order_id] - [items]. [Provide tracking info]"

**RETURNS_REFUNDS (lines 427-433):**
- Says to output greeting IMMEDIATELY after get_customer_info
- Greeting includes condition question, NOT refund details
- Says "DO NOT call any other tools yet" and "OUTPUT THE GREETING TEXT AND STOP"

**Why This Matters:**
1. **Inconsistent user experience** - Why does order tracking give info immediately but returns requires Q&A?
2. **ORDER_STATUS ambiguity** - If tracking info is in greeting (line 35-37), why is there a separate Step 3 "Provide Tracking Information" (line 39-44)?

**Evidence of Confusion:**
Looking at ORDER_STATUS:
- Line 35: Greeting says "I can help you track your order [order_id] - [items]. **[Provide tracking info]**"
- Line 39: Step 3 is literally "Provide Tracking Information"

This is redundant - either tracking info is in greeting OR it's a separate step, not both.

**Recommended Fix:**

**For ORDER_STATUS** - Choose one approach:

**Option A (Info in greeting):**
```
Step 2: Call get_customer_info and IMMEDIATELY provide greeting with tracking info
- Include: name, VIP status, order status, tracking number, delivery estimate
- Example: "Hello John! Thank you for being a Gold VIP for 3 years. Your order ORD-123 (The Great Gatsby) shipped yesterday via FedEx. Tracking: 1Z999AA10123456784. Expected delivery: Feb 20."
- Then STOP and wait for customer to ask follow-up questions
```

**Option B (Info separate):**
```
Step 2: Call get_customer_info and output brief greeting only
- Example: "Hello John! Thank you for being a Gold VIP for 3 years. I can help you track order ORD-123."
- Then proceed directly to Step 3 (provide detailed tracking)
```

Recommend **Option A** for efficiency.

---

## 🟡 MEDIUM PRIORITY ISSUES (Consistency & Clarity)

### M-1: Tool Descriptions Not Documented in Prompts
**Location:** All prompts - tool listings (ORDER_STATUS line 80-85, RETURNS_REFUNDS line 486-497, GENERAL line 619-624)
**Severity:** Medium - Reduces agent understanding

**Problem:**
All three prompts list available tools by name only, with minimal descriptions:

```
# AVAILABLE TOOLS
You have access to:
1. `look_up_order` - Get order details
2. `get_customer_info` - Get customer information for greeting
3. `escalate_to_human` - Escalate if customer is angry or issue is complex
```

**What's Missing:**
- Required parameters for each tool
- What data each tool returns
- When exactly to use each tool (beyond what's in workflow steps)

**Why This Matters:**
The agent learns tool usage from:
1. Tool schema (from API)
2. Tool descriptions in prompt
3. Examples in prompt

Without detailed tool descriptions in the prompt, the agent relies heavily on the schema, which is isolated from the workflow context.

**Recommended Fix:**
Create detailed tool reference section:

```
# AVAILABLE TOOLS & PARAMETERS

## look_up_order
**Purpose:** Fetch complete order details
**When to use:** MANDATORY first step for any order-related query
**Parameters:**
- order_id (required, string): The order ID from customer
**Returns:**
- order_id, customer_id, items[], status, tracking_number, delivery_estimate, eligible_for_return, etc.
**Example:**
look_up_order(order_id="ORD-123")

## get_customer_info
**Purpose:** Retrieve customer profile for personalized greeting
**When to use:** MANDATORY after look_up_order, before greeting customer
**Parameters:**
- customer_id (required, string): From look_up_order result
**Returns:**
- customer_name, email, years_active, is_vip, tier, reading_preferences, purchase_history
**Example:**
get_customer_info(customer_id="CUST-456")

## escalate_to_human
**Purpose:** Escalate to human agent when issue requires manual review
**When to use:** Customer angry, complex policy question, technical issue, or VIP exception needed
**Parameters:**
- order_id (required, string): The relevant order ID
- reason (required, string): Clear explanation of why escalating
- policy_check_confirmation (required, enum): Must be "verified_compliant" - confirms you checked policy
**Returns:**
- ticket_id, escalation_status, estimated_response_time
**Example:**
escalate_to_human(
  order_id="ORD-123",
  reason="VIP customer requesting exception for late return - requires manager approval",
  policy_check_confirmation="verified_compliant"
)
```

Repeat for all tools in each prompt.

---

### M-2: Ambiguous "Tone Assessment" Criteria
**Location:** prompts.py:226-233 (RETURNS_REFUNDS)
**Severity:** Medium - Subjective interpretation

**Problem:**
Lines 226-233 use subjective language to determine when to offer recommendations:

```
**Consider offering if:**
- Customer tone is neutral or positive (not angry/frustrated)

**DO NOT offer recommendations if:**
- Customer is angry/escalated
- Customer seems impatient or frustrated
```

**Why This Is Problematic:**
"Tone", "seems", "frustrated" are all subjective. In text-based chat, how does the agent assess tone?

**Example Ambiguous Cases:**
- "Just process it" - Impatient or just direct?
- "ok" - Neutral or frustrated?
- "I guess that works" - Positive or resigned?
- "Fine" - Acceptable or annoyed?

**Recommended Fix:**
Provide concrete signals:

```
## WHEN TO OFFER RECOMMENDATIONS

**DO offer recommendations if customer:**
- Uses neutral/positive language: "yes", "sure", "okay", "sounds good"
- Asks questions: "What are my options?", "Can I exchange?"
- Provides detailed responses (not one-word answers)
- Uses polite language: "please", "thank you"

**DO NOT offer recommendations if customer:**
- Uses negative language: "just", "hurry", "quickly", "whatever", "fine" (single word)
- Uses capital letters: "JUST PROCESS IT"
- Mentions time pressure: "I'm in a rush", "quickly", "fast"
- Uses complaint language: "disappointed", "frustrated", "annoyed", "terrible"
- Gives one-word responses repeatedly: "ok", "yes", "no"
- Uses profanity or angry tone

**When unsure:**
- Default to NOT offering (respect customer's time)
- Simply proceed with return
```

---

### M-3: "Policy Overrides Database" Directive Needs Examples
**Location:** prompts.py:136-139 (RETURNS_REFUNDS)
**Severity:** Medium - Important concept but abstract

**Problem:**
Lines 136-139 explain "Policy Overrides Database" principle:

```
1. You will receive an order status from `look_up_order`.
2. Even if `eligible_for_return` is TRUE, you **MUST** check the item name against the Policy.
3. **CONFLICT RESOLUTION:** If `look_up_order` says YES, but `get_policy_info` lists the item as "Non-Returnable", the **Policy WINS**.
```

This is a critical principle but it's abstract. No concrete examples are provided.

**Why This Matters:**
This handles the common database vs business logic conflict. Without examples, agent might not understand how to apply this in real situations.

**Recommended Fix:**
Add concrete examples:

```
# YOUR PRIME DIRECTIVE: "Policy Overrides Database"

## The Rule
1. You will receive an order status from `look_up_order`
2. Even if `eligible_for_return` is TRUE, you **MUST** check the item name against Policy
3. **CONFLICT RESOLUTION:** If `look_up_order` says YES but `get_policy_info` lists the item as "Non-Returnable", **Policy WINS**

## Why This Matters
The database eligible_for_return flag is based on basic rules (e.g., within 30 days). It doesn't know about special exclusions like digital products, opened items, or gift cards.

## Examples

**Example 1: Digital Product**
```
look_up_order("ORD-123") returns:
{
  items: ["The Great Gatsby - E-book"],
  eligible_for_return: true,  ← Database says YES (within 30 days)
  days_since_order: 5
}

get_policy_info("returns") says:
"Digital Products (e-books, audiobooks) are non-returnable once downloaded"

Customer confirms: "Yes, I downloaded it"

DECISION: DENY return - Policy overrides database
```

**Example 2: Opened Item**
```
look_up_order("ORD-456") returns:
{
  items: ["Headphones - Wireless"],
  eligible_for_return: true,  ← Database says YES
}

get_policy_info("returns") says:
"Electronics are non-returnable once opened due to hygiene and resale concerns"

Customer says: "I opened the box to test them"

DECISION: DENY return - Policy overrides database
```

**Example 3: Database Correct**
```
look_up_order("ORD-789") returns:
{
  items: ["The Great Gatsby - Hardcover"],
  eligible_for_return: false,  ← Database says NO (past 30 days)
  days_since_order: 45
}

get_policy_info("returns") says:
"Physical books: 30-day return window"

Customer confirms book is unopened

DECISION: DENY return - Past return window (both database and policy agree)
Note: If customer is VIP, check precedents for late return exception
```
```

---

### M-4: Missing Definition of "Non-Compliant" in Decision Logic
**Location:** prompts.py:452 (RETURNS_REFUNDS Step 10)
**Severity:** Medium - Vague terminology

**Problem:**
Step 10 says:
```
- IF Non-Compliant → Check VIP status and precedents, then approve or deny
- IF Compliant → Proceed to Step 11
```

"Non-Compliant" is never defined. Does it mean:
- Customer violated policy rules?
- Item doesn't meet return criteria?
- Outside return window?
- All of the above?

**Why This Matters:**
Without a clear definition, agent doesn't know when to trigger the VIP exception path.

**Recommended Fix:**

```
Step 10: Decision Logic

After reviewing policy (Step 8), categorize the return request:

**COMPLIANT WITH POLICY (Approve):**
- Item is within return window (30 days)
- Item is in returnable condition (unopened, unread, unused)
- Item type is returnable (not digital, not gift card, not opened electronics)
→ Proceed to Step 11 (Approve and offer recommendations)

**NON-COMPLIANT WITH POLICY (Requires VIP Check):**
Any of the following:
- Past return window (>30 days since order)
- Item is in non-returnable condition (read, opened, used)
- Item type is non-returnable (digital product downloaded, gift card, opened electronics)
→ Check VIP status (Step 10A below)

**UNCLEAR / EDGE CASE:**
- Policy doesn't clearly address this situation
- Customer situation is unusual
- You're unsure how to apply policy
→ Escalate to human for policy interpretation

## Step 10A: VIP Exception Check (For Non-Compliant Cases)

[Existing VIP check process from lines 145-188]
```

---

### M-5: No Instruction on Handling Multiple Items in Same Order
**Location:** All prompts
**Severity:** Medium - Common real-world scenario

**Problem:**
None of the prompts address what happens if an order contains multiple items and customer wants to return only some of them.

**Example Scenario:**
```
Customer: "I want to return items from order ORD-123"
look_up_order returns:
{
  items: [
    {title: "Book A", price: 20},
    {title: "Book B", price: 25},
    {title: "Book C", price: 30}
  ]
}
Customer: "Just Book A and Book C"
```

Current prompts don't address:
- How to ask which items to return
- How to process partial returns
- Whether execute_order_return handles partial or full order only

**Recommended Fix:**
Add section to RETURNS_REFUNDS:

```
## HANDLING MULTI-ITEM ORDERS

**If order contains multiple items:**

1. **Ask customer to specify:**
   "I see your order contains [X] items. Which item(s) would you like to return?"
   - List items clearly with titles
   - Ask customer to specify

2. **For each item being returned:**
   - Ask condition question: "Is [Item A] in its original condition?"
   - Ask return reason: "Why would you like to return [Item A]?"
   - Check policy compliance for that specific item

3. **Process returns:**
   - If tools support partial returns: Call execute_order_return with item-specific parameters
   - If tools only support full order returns: Inform customer and escalate for manual processing:
     "I can process a full return for order ORD-123, or I can have our team handle the partial return for specific items. Which would you prefer?"
```

**Note:** This requires checking whether execute_order_return backend supports partial returns. If not, document the limitation.

---

### M-6: ORDER_STATUS Prompt Missing Greeting STOP Instruction
**Location:** prompts.py:28-37 (ORDER_STATUS)
**Severity:** Medium - Workflow inconsistency with RETURNS_REFUNDS

**Problem:**
RETURNS_REFUNDS has explicit STOP instruction (lines 427-433):
```
4. 🛑 MANDATORY STOP - Output Greeting NOW!
   - ⚠️ OUTPUT THE GREETING TEXT AND STOP!
```

ORDER_STATUS doesn't have this. It just says "Greet them by name" but doesn't say to STOP before proceeding.

**Why This Matters:**
Without STOP instruction, ORDER_STATUS agent might call tools before customer responds. While this might be acceptable for order status (info is static), it creates inconsistency in the system.

**Recommended Fix:**
Decide on consistent approach:

**Option A: Add STOP to ORDER_STATUS** (Recommended for consistency)
```
## Step 2: Personalized Greeting
**MANDATORY:** After looking up the order, call `get_customer_info(customer_id="...")`

Then IMMEDIATELY output greeting with tracking information:
[Existing greeting formats...]

**🛑 OUTPUT GREETING AND WAIT:**
After providing tracking information, STOP and wait for customer to ask follow-up questions.
DO NOT call additional tools until customer responds.
```

**Option B: Remove STOP from RETURNS_REFUNDS**
Only do this if you want agents to be more proactive. Not recommended as it led to the bug we just fixed.

---

### M-7: Inconsistent Capitalization in Tool Names
**Location:** Various - escalate_to_human tool
**Severity:** Medium - Potential parsing issues

**Problem:**
Throughout the prompts, there's inconsistent formatting of tool names:
- Sometimes backticks: `` `escalate_to_human` ``
- Sometimes plain text: "escalate to human"
- Sometimes with parentheses: `escalate_to_human()`

**Why This Matters:**
While LLMs are generally robust to formatting, consistent syntax helps prevent edge cases where the model might not recognize a tool reference.

**Recommended Fix:**
Establish and follow consistent convention:
- Tool references in instructions: `` `tool_name` `` (with backticks, no parentheses)
- Tool examples/calls: `` `tool_name(param="value")` ``
- Tool listings: `` `tool_name` - Description ``

Update all prompts to follow this convention.

---

### M-8: GENERAL Prompt Example Contradicts Boundaries
**Location:** prompts.py:614-617 (GENERAL)
**Severity:** Medium - Confusing instructions

**Problem:**
Line 548 says GENERAL agent should NOT process returns:
```
- ❌ **Active Returns/Refunds:** If customer wants to return an item, say: "I can help you with the general return policy, but to process an actual return, please let me know the order number and I'll transfer you to our returns team."
```

But line 617 example says:
```
Response: "For physical books, we accept returns within 30 days if they're in unread, resellable condition... **If you have a specific book you'd like to return, I can help process that!**"
```

**"I can help process that" contradicts "I can't process returns"**

**Recommended Fix:**
Update line 617 example to match boundaries:

```
**Return Policy (General):**
User: "What's your return policy?"
You: [Call get_policy_info(policy_type="returns")]
Response: "For physical books, we accept returns within 30 days if they're in unread, resellable condition with no bent spines or markings. Digital products (e-books, audiobooks) are non-returnable once downloaded.

If you have a specific book you'd like to return, I'll need your order number so I can transfer you to our returns specialist who can help process that for you. Do you have an order number handy?"
```

---

### M-9: Missing Explanation of Why VIP Exceptions Exist
**Location:** prompts.py:141-189 (RETURNS_REFUNDS VIP section)
**Severity:** Medium - Agent may not understand the "why"

**Problem:**
The VIP exception protocol is detailed but never explains WHY exceptions are made for VIPs. This is important context for the agent to:
1. Understand the business logic
2. Communicate appropriately with VIP customers
3. Know when exceptions are appropriate vs. inappropriate

**Why This Matters:**
Without understanding the rationale, the agent is just following rules mechanically. Understanding "why" helps the agent:
- Make better judgment calls in edge cases
- Communicate more authentically with customers
- Recognize when to escalate (e.g., VIP request is outside even exception bounds)

**Recommended Fix:**
Add context section:

```
# EXCEPTION PROTOCOL (DECISION LEDGER)

## Why VIP Exceptions Exist

VIP customers are highly valuable to Bookly:
- Gold VIP: $500+ annual spend, 2+ years loyalty
- Platinum VIP: $1000+ annual spend, 3+ years loyalty

**Business Rationale:**
1. **Customer Lifetime Value:** VIP customers generate 10x more revenue than average customers
2. **Retention:** Small exceptions prevent churn of high-value customers
3. **Word of Mouth:** VIP customers are brand advocates - good experiences lead to referrals
4. **Competitive Advantage:** Premium service differentiates Bookly from competitors

**When to Grant Exceptions:**
- Reasonable requests (late return by a few days, genuine dissatisfaction)
- Customer has clean return history (not abusing policy)
- Situation has precedent from human decisions

**When NOT to Grant (Escalate Instead):**
- Suspected fraud or abuse
- Request far outside reasonable bounds (return after 6 months)
- High-value items (>$100)
- Customer has history of excessive returns

## Automatic VIP Check (MANDATORY)

[Rest of existing VIP protocol...]
```

---

## 🟢 LOW PRIORITY ISSUES (Enhancements)

### L-1: No Instruction on PII Handling
**Location:** All prompts
**Severity:** Low - Security best practice

**Problem:**
None of the prompts instruct agents on handling sensitive information like credit card numbers, passwords, or social security numbers that customers might share in chat.

**Recommended Fix:**
Add security section to all prompts:

```
# SECURITY & PRIVACY

**If customer shares sensitive information in chat:**
- Credit card numbers
- Passwords
- Social Security Numbers
- Account credentials

**Immediately respond:**
"For your security, please don't share [sensitive info type] in this chat. I don't need that information to help you, and it's important to keep it private.

If you've already shared it, I recommend you [change your password / call your card issuer] as a precaution."

**Then:** Continue helping without using the sensitive data.
```

---

### L-2: No Instruction on Handling Abusive Language
**Location:** RETURNS_REFUNDS, GENERAL (Only ORDER_STATUS mentions it on line 58)
**Severity:** Low - Important for agent safety guidelines

**Problem:**
Only ORDER_STATUS mentions profanity/threatening language (line 58). RETURNS_REFUNDS and GENERAL don't address this.

**Recommended Fix:**
Add to all prompts under Escalation Protocol:

```
**Immediate escalation triggers:**
- Profanity or abusive language directed at you
- Threatening language ("I'll sue", threats of harm)
- Discriminatory language
- Sexual harassment

**Response:**
"I understand you're frustrated. To ensure you get the best assistance, I'm going to transfer you to a supervisor who can help resolve this. One moment please."

[Call escalate_to_human with reason clearly documenting the behavior]
```

---

### L-3: No Instruction on Business Hours / Response Time Expectations
**Location:** All prompts
**Severity:** Low - Customer expectation management

**Problem:**
Prompts don't address:
- When are human agents available?
- How long does escalation take?
- What if customer escalation is outside business hours?

**Recommended Fix:**
Add to escalation sections:

```
**After escalating:**
Inform customer of response time:
- During business hours (9am-6pm ET, Mon-Fri): "A specialist will respond within 2-4 hours"
- Outside business hours: "A specialist will respond on the next business day"
- VIP escalations: "A VIP specialist will contact you within 24 hours"

**Provide ticket ID for reference:**
"Your case number is [ticket_id]. You'll receive updates via email at [customer_email]."
```

---

### L-4: No Instruction on Conversation Closing
**Location:** All prompts
**Severity:** Low - Improved customer experience

**Problem:**
Prompts don't instruct agents on how to politely close conversations or check if customer needs additional help.

**Recommended Fix:**
Add to all prompts:

```
# CONVERSATION CLOSING

**After completing primary request:**
Always ask: "Is there anything else I can help you with today?"

**If customer says no:**
- Thank them: "You're welcome! Thank you for choosing Bookly."
- If VIP: "Thank you for being a valued [tier] member."
- If they made a purchase or had positive interaction: "Enjoy your book(s)!"

**If customer says yes:**
Continue assisting with new request.

**If customer doesn't respond for 2+ exchanges:**
Prompt gently: "I'm still here if you need any additional help! Just let me know."
```

---

### L-5: No Instruction on Handling Jokes or Off-Topic Conversations
**Location:** All prompts
**Severity:** Low - Edge case handling

**Problem:**
What if customer makes a joke, asks about the weather, or goes off-topic?

**Current State:** No guidance.

**Recommended Fix:**
Add brief section:

```
# OFF-TOPIC REQUESTS

**If customer makes small talk or jokes:**
- Brief friendly response is okay: "Ha! Good one. 😊"
- Then redirect gently: "Now, about your order..."

**If customer asks unrelated questions (weather, sports, personal advice):**
- Polite redirect: "I'm specialized in helping with Bookly orders and bookshop questions. Is there anything book-related I can help you with today?"

**If customer persists in off-topic conversation:**
- Stay professional: "I'd love to chat, but I'm here specifically for book orders. Let me know if you need help with an order!"

**Do NOT:**
- Engage in lengthy off-topic conversations
- Give personal advice
- Discuss politics, religion, or controversial topics
```

---

## Summary of Recommendations by Priority

### Immediate Action Required (Critical - 5 issues):
1. **C-1:** Document `policy_check_confirmation` parameter for escalate_to_human in ALL prompts
2. **C-2:** Resolve escalate_to_human tool schema contradiction (order_id required vs optional)
3. **C-3:** Move policy check earlier in RETURNS_REFUNDS workflow (before collecting reason)
4. **C-4:** Add error handling instructions for all tool failures
5. **C-5:** Clarify "approval" vs "processing" terminology to prevent premature completion

### Before Production (High Priority - 8 issues):
6. **H-1:** Resolve redundant VIP checking (check_vip_status vs get_customer_info)
7. **H-2:** Add validation for ambiguous customer responses
8. **H-3:** Fix process_exchange return_reason inconsistency
9. **H-4:** Add guidance for multiple/conflicting precedents
10. **H-5:** Expand order ID collection instructions
11. **H-6:** Add denial scenario examples (non-VIP, VIP exception, VIP escalation)
12. **H-7:** Fix GENERAL prompt's broken return handoff workflow
13. **H-8:** Resolve greeting timing inconsistency between ORDER_STATUS and RETURNS_REFUNDS

### Polish & Consistency (Medium Priority - 9 issues):
14-22. Tool documentation, tone assessment, policy examples, terminology clarification, multi-item orders, workflow consistency, formatting, contradictions, VIP context

### Nice to Have (Low Priority - 5 issues):
23-27. PII handling, abusive language, business hours, conversation closing, off-topic handling

---

## Root Cause Analysis

### Pattern: Missing Tool Parameter Documentation

**The Bug We Fixed:**
- Tool `execute_order_return` requires `reason` parameter
- Prompt never mentioned this requirement
- Agent skipped asking for reason → Tool call failed

**Same Pattern Found 3 More Times:**
1. `escalate_to_human` requires `policy_check_confirmation` - Never mentioned
2. `escalate_to_human` requires `order_id` - Mentioned in tools.py as "OPTIONAL" but schema says required
3. `process_exchange` parameter example contradicts step instructions

**Systemic Issue:**
Tool schemas (tools.py) and prompt instructions (prompts.py) are **not cross-validated**. There's no automated check ensuring:
- Every required parameter is collected in the workflow
- Parameter descriptions match between tool schema and prompt
- Tool return values used in prompts actually exist

**Recommendation:**
Create a validation script that:
1. Parses tools.py to extract required parameters
2. Parses prompts.py to check each tool is documented with ALL required parameters
3. Runs as pre-commit hook or CI check
4. Fails build if mismatch found

Example pseudocode:
```python
def validate_tool_prompt_alignment():
    tool_schemas = parse_tools_py()
    prompts = parse_prompts_py()

    for tool in tool_schemas:
        for prompt in prompts:
            if tool.name in prompt.tool_list:
                # Check all required params are documented
                for param in tool.required_params:
                    if param not in prompt.tool_documentation[tool.name]:
                        raise ValidationError(
                            f"Prompt {prompt.name} uses tool {tool.name} "
                            f"but doesn't document required parameter: {param}"
                        )
```

---

## Conclusion

This review identified **27 distinct issues** in the prompt engineering, with **5 critical issues** requiring immediate attention to prevent runtime failures similar to the return_reason bug we just fixed.

The most urgent systemic fix is establishing cross-validation between tool schemas and prompt instructions to ensure all required parameters are documented and collected.

**Next Steps:**
1. Review and prioritize these findings with the team
2. Create tickets for Critical and High Priority issues
3. Consider implementing automated tool-prompt validation
4. Schedule prompt review as part of tool schema changes going forward

---

**Document Version:** 1.0
**Last Updated:** February 16, 2026
**Review Conducted By:** Expert Code Review Agent
**Files Reviewed:** prompts.py (687 lines), tools.py (161 lines)
