# Hybrid Enforcement Architecture: Code-Gate + LLM

**Date:** February 2025
**Status:** Proposed Changes
**Scope:** Returns/Refunds workflow enforcement

---

## Executive Summary

The current architecture relies entirely on prompt-based enforcement for mandatory workflow steps. Based on the field consensus (Anthropic, Applied-LLMs, Eugene Yan, et al.), the recommended split is:

- **Code enforces:** Which steps MUST happen and in what order (state machine gates)
- **LLM handles:** The natural language quality of how each step happens
- **Code validates:** That each step actually completed before the next is allowed

This document details the exact changes needed to implement that split in this codebase.

---

## Current Architecture: What Is Prompt-Only Today

Every mandatory step in the Returns workflow is currently enforced solely by the `RETURNS_REFUNDS_PROMPT` in `prompts.py`. There is no code gate preventing the LLM from:

| Risk | Current State | Consequence |
|---|---|---|
| Calling `get_policy_info` before asking the customer about item condition | Only a prompt instruction | LLM could skip the condition question and run policy check anyway |
| Calling `execute_order_return` without capturing the customer's stated reason | Only a prompt instruction | Return processed with empty or fabricated reason in audit log |
| Calling `check_vip_status` before evaluating policy | Only a prompt instruction | VIP check runs unnecessarily (wrong sequence) |
| Calling `execute_order_return` before policy was evaluated | Only a prompt instruction | Return processed without policy check |
| Completing the workflow without the order ID step | Only a prompt instruction | Agent could attempt tool calls with null order_id |

**Fragile completion detection in `app.py` lines 215–221:**
```python
is_complete = (
    'refund processed' in response_lower or    # String match - brittle
    'return approved' in response_lower or      # String match - brittle
    'escalate' in response_lower or             # False positives likely
    'transfer' in response_lower or             # False positives likely
    (not is_asking_question and len(response) > 100)  # Very unreliable
)
```
This will miss completions and flag non-completions. It drives the `active_category` clearing logic, which determines whether the next message is treated as a continuation or a new topic.

---

## Proposed Architecture: 3-Layer Hybrid

```
┌──────────────────────────────────────────────────────┐
│  Layer 1: Code Gate (BEFORE tool executes)           │
│  - State machine: is this tool allowed right now?    │
│  - Return an error to the LLM if not                 │
└──────────────────────────────────────────────────────┘
           ↓ (allowed)
┌──────────────────────────────────────────────────────┐
│  Layer 2: LLM (the tool call itself)                 │
│  - Natural language, intent, tone                    │
│  - Guided by simplified prompt                       │
└──────────────────────────────────────────────────────┘
           ↓ (result returned)
┌──────────────────────────────────────────────────────┐
│  Layer 3: Code Validation (AFTER tool executes)      │
│  - Advance state machine based on tool result        │
│  - Validate required fields (e.g., reason)           │
│  - Drive workflow completion detection in app.py     │
└──────────────────────────────────────────────────────┘
```

---

## State Machine Design

The Returns workflow has a clear, linear sequence with two conditional branches. This is exactly the case that code enforcement is built for.

```
INIT
  │
  ├─► look_up_order → ORDER_FOUND
  │
  ├─► get_customer_info → CUSTOMER_GREETED
  │       (LLM outputs greeting, end_turn)
  │
  ├─► [next agent.run() call = customer responded] → INFO_COLLECTED
  │
  ├─► get_policy_info → POLICY_CHECKED
  │
  ├─► [if policy DENY] check_vip_status → VIP_CHECKED
  │
  ├─► [if VIP] check_precedents → PRECEDENT_CHECKED
  │
  ├─► [policy allows OR precedent approves]
  │     execute_order_return → COMPLETE
  │     process_exchange → COMPLETE
  │
  └─► [policy denies, no exception]
        escalate_order_issue → ESCALATED
```

### State Enum (new file: `workflow/returns_state_machine.py`)

```python
class ReturnWorkflowState(Enum):
    INIT = "init"
    ORDER_FOUND = "order_found"
    CUSTOMER_GREETED = "customer_greeted"
    INFO_COLLECTED = "info_collected"
    POLICY_CHECKED = "policy_checked"
    VIP_CHECKED = "vip_checked"
    PRECEDENT_CHECKED = "precedent_checked"
    COMPLETE = "complete"
    ESCALATED = "escalated"
```

---

## Exact Changes Required

### 1. New File: `workflow/returns_state_machine.py` (~90 lines)

**What it does:**
- Holds `ReturnWorkflowState` enum
- Holds `ReturnWorkflowStateMachine` class with:
  - `state`: current state
  - `order_id`: captured when `look_up_order` runs
  - `customer_id`: captured when `look_up_order` returns
  - `return_reason`: captured when `execute_order_return` is attempted
  - `policy_checked`: bool flag
  - `run_count_after_greeting`: int, increments each `agent.run()` call post-greeting
  - `can_call_tool(tool_name) → bool`: the gate method
  - `advance(tool_name, tool_result)`: updates state based on what just happened
  - `is_terminal() → bool`: True if COMPLETE or ESCALATED
  - `get_block_reason(tool_name) → str`: human-readable explanation for LLM

**The 5 concrete gates:**

| Tool | Gate Condition |
|---|---|
| `get_customer_info` | `state >= ORDER_FOUND` (i.e., `look_up_order` ran successfully) |
| `get_policy_info` | `state >= CUSTOMER_GREETED` AND `run_count_after_greeting >= 1` (customer responded) |
| `check_vip_status` | `state >= POLICY_CHECKED` |
| `check_precedents` | `state >= VIP_CHECKED` |
| `execute_order_return` | `state >= POLICY_CHECKED` AND `len(reason) > 5` AND `reason.lower() not in ['', 'unknown', 'n/a', 'none']` |
| `process_exchange` | `state >= POLICY_CHECKED` AND `return_reason` non-empty |
| `escalate_order_issue` | Always allowed (anger can trigger at any point) |
| `look_up_order` | Always allowed (first step) |
| `get_book_recommendations` | `state >= POLICY_CHECKED` |

**The `run_count_after_greeting` gate** is the critical one. Here's why it works:

The `SupportAgent.run()` is called once per user message (see `app.py` line 179/184). After the LLM sends the greeting (end_turn), the next call to `agent.run()` means the user has responded. The state machine increments `run_count_after_greeting` at the top of each `run()` call when `state == CUSTOMER_GREETED`. When `run_count_after_greeting >= 1`, the customer has definitively responded, and `get_policy_info` is allowed.

---

### 2. Modified: `agent/agent.py`

**Location of changes:**

**In `__init__` (after line 25):** Add two new instance variables:
```python
self.workflow_state = None      # ReturnWorkflowStateMachine, created for RETURNS_REFUNDS
self._category = None           # Track last category to detect workflow restarts
```

**In `run()`, after line 63 (`self.messages.append(...)`):**
```python
# Initialize or update state machine for Returns workflow
if category and category.value == "RETURNS_REFUNDS":
    if self.workflow_state is None or self._category != category:
        from workflow.returns_state_machine import ReturnWorkflowStateMachine
        self.workflow_state = ReturnWorkflowStateMachine()
        self._category = category
    else:
        # Increment run count so gate knows customer has responded
        self.workflow_state.on_new_run()
```

**In the tool execution loop (around line 178), before `result = None`:**
Add the gate check for RETURNS_REFUNDS category:
```python
# CODE GATE: Check if this tool call is allowed at the current workflow state
if self.workflow_state is not None:
    if not self.workflow_state.can_call_tool(tool_name, tool_input):
        block_reason = self.workflow_state.get_block_reason(tool_name)
        logger.warning(f"[STATE GATE] Blocked '{tool_name}': {block_reason}")
        audit_logger.info(
            f"Tool call blocked by state machine: {tool_name}",
            extra={
                'session_id': self.session_id,
                'tool_name': tool_name,
                'block_reason': block_reason,
                'current_state': self.workflow_state.state.value,
                'event_type': 'TOOL_BLOCKED'
            }
        )
        # Return a structured error to the LLM so it understands what to do
        tool_result_content.append({
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": json.dumps({
                "error": "step_out_of_order",
                "message": block_reason
            })
        })
        continue  # Skip actual tool execution
```

**After each tool result is obtained**, advance the state machine:
```python
# STATE MACHINE: Advance state based on tool result
if self.workflow_state is not None:
    self.workflow_state.advance(tool_name, result)
```

This `advance()` call is inserted once, right before the `tool_result_content.append(...)` at line 439. It runs for every successful tool call.

**Special validation for `execute_order_return` (after line 264):**
The `can_call_tool` gate already covers this, but add an explicit reason validation for audit purposes:
```python
elif tool_name == "execute_order_return":
    reason = tool_input.get("reason", "")
    if not reason or len(reason.strip()) < 5:
        # Log and inject a meaningful reason prompt back to LLM
        audit_logger.warning(
            "execute_order_return called with missing/thin reason",
            extra={
                'session_id': self.session_id,
                'reason_provided': reason,
                'event_type': 'VALIDATION_FAILURE'
            }
        )
        result = {
            "error": "reason_required",
            "message": "Return reason is required and must reflect the customer's stated reason. Please ask the customer for their reason before processing."
        }
    else:
        result = EnterpriseServices.execute_refund(
            tool_input.get("order_id"), reason
        )
```

---

### 3. Modified: `app.py`

**Lines 204–229: Replace fragile string-matching with state machine query**

Current (brittle):
```python
is_asking_question = (
    '?' in response or
    'please provide' in response_lower or
    ...
)
is_complete = (
    'refund processed' in response_lower or
    'return approved' in response_lower or
    ...
)
```

Replace with:
```python
# Determine completion using state machine (for Returns) or heuristics (for others)
agent: Any = cl.user_session.get("agent")

if (category == QuestionCategory.RETURNS_REFUNDS
        and agent.workflow_state is not None
        and agent.workflow_state.is_terminal()):
    # Code-authoritative: state machine says workflow is done
    is_complete = True
    is_asking_question = False
else:
    # Heuristic for non-returns workflows (ORDER_STATUS, GENERAL)
    is_asking_question = (
        '?' in response or
        'please provide' in response_lower or
        'could you' in response_lower or
        'can you share' in response_lower
    )
    is_complete = (
        not is_asking_question and len(response) > 100
    )
```

**Also add state machine reset when a new RETURNS_REFUNDS workflow starts:**
At line 156, after `cl.user_session.set("active_category", category)`:
```python
# Reset workflow state machine if starting a fresh Returns workflow
if category == QuestionCategory.RETURNS_REFUNDS:
    agent_instance = cl.user_session.get("agent")
    if agent_instance and agent_instance.workflow_state is not None:
        agent_instance.workflow_state = None  # Will be recreated on next run()
```

---

### 4. `prompts.py` — No Changes in First Pass

**Recommendation:** Keep the prompt enforcement language as-is for now.

**Reasoning:**
- The code gates are a new layer. During the initial rollout, you want defense-in-depth: prompt + code.
- Once you've run the code gates for several sessions and validated they work, you can simplify the prompt (remove the repeated `MANDATORY`, `DO NOT`, `CRITICAL` markers that were compensating for lack of code enforcement).
- The prompt is still valuable for the quality of the LLM's language, even if it no longer carries the guarantee burden alone.
- Anger detection language in the prompt is correctly placed there — detecting emotional nuance is what LLMs are genuinely good at. That part stays permanently.

**What can be simplified in a follow-on (after code gates are proven):**
- Remove the repeated `STOP and OUTPUT` markers (code gate handles the sequencing)
- Remove the `DO NOT call any other tools until customer responds` instruction (code gate blocks it)
- Remove `MANDATORY:` prefixes on tool sequences (code gate makes them mandatory)
- Consolidate the workflow SOP section from ~50 lines to ~15 lines focused on tone
- Keep: VIP exception response format, anger detection, recommendation offer guidance

---

## File-by-File Scope Summary

| File | Change Type | Lines Affected | Complexity |
|---|---|---|---|
| `workflow/returns_state_machine.py` | **New file** | ~90 lines | Medium |
| `agent/agent.py` | **Modified** | +60 lines (gate check + state advance) | Medium |
| `app.py` | **Modified** | ~20 lines replaced | Low |
| `prompts.py` | **No change** (Phase 1) | 0 | — |
| `config.py` | **No change** | 0 | — |
| `router.py` | **No change** | 0 | — |
| `tools.py` | **No change** | 0 | — |
| `services.py` | **No change** | 0 | — |

**Total new code:** ~170 lines
**Total modified code:** ~80 lines

---

## Edge Cases to Handle

### Edge Case 1: Customer provides Order ID and reason in the first message
> "I want to return ORD-123, I changed my mind about the book"

**Handling:** State machine starts at INIT. The reason is in the conversation history, but `execute_order_return` is still blocked until `POLICY_CHECKED`. The LLM will still go through the proper sequence (lookup, greeting, condition question, policy check), and by the time it calls `execute_order_return`, the reason is available in the conversation history for the LLM to include. No special handling needed.

### Edge Case 2: Customer opens with anger
> "This is RIDICULOUS, I want to return my order immediately!"

**Handling:** The anger detection in the prompt triggers `escalate_order_issue`, which is always allowed by the state machine (no gate). State advances to `ESCALATED`. The `is_terminal()` check returns True, so `app.py` correctly clears `active_category`. Works correctly with no change needed.

### Edge Case 3: Customer provides new Order ID mid-workflow
> Mid-conversation: "Actually, forget that, let me return ORD-456 instead"

**Handling:** The re-classification logic in `app.py` (lines 123–141) will detect this as a new question (`is_new_question = True`) because it contains "let me return" and is > 50 chars. This calls `router.classify_question()`, sets `active_category = RETURNS_REFUNDS` again. The state machine reset code (added at line 156) sets `agent.workflow_state = None`. On the next `agent.run()` call, a fresh state machine is created. ✓

### Edge Case 4: LLM tries `get_policy_info` in the same ReAct turn as `get_customer_info`
> (i.e., in one `agent.run()` call, the LLM calls both tools back-to-back without end_turn)

**Handling:** This is exactly what we're guarding against. After `get_customer_info` succeeds, state advances to `CUSTOMER_GREETED` with `run_count_after_greeting = 0`. When the LLM then tries `get_policy_info` in the same turn, the gate checks `run_count_after_greeting >= 1` → False → blocks with error. The LLM receives: `{"error": "step_out_of_order", "message": "Please ask the customer about the item condition and wait for their response before checking policy."}` The LLM then outputs the greeting (end_turn). Next `agent.run()` call: `run_count_after_greeting` increments to 1. `get_policy_info` is now allowed. ✓

### Edge Case 5: `execute_order_return` called before `check_vip_status` (VIP denial path)
> LLM tries to approve a return that should have been denied, skipping VIP check

**Handling:** The gate for `execute_order_return` requires `state >= POLICY_CHECKED`. `POLICY_CHECKED` is set only after `get_policy_info` succeeds. Once `get_policy_info` has run, the LLM has the policy information. If the policy says deny, the prompt guides the LLM to call `check_vip_status` next (which is gated to `state >= POLICY_CHECKED` ✓). If the LLM incorrectly tries to approve (calls `execute_order_return`) without doing the VIP check when policy said deny — the state machine **does not block this**. This is a semantic correctness issue, not a sequencing issue. The gate only enforces order, not semantic logic. However: the prompt is still in place as the semantic guard here. This is appropriate — complex conditional logic ("if policy denies, check VIP") is exactly what LLMs handle well.

### Edge Case 6: Workflow restarted within the same session (same Chainlit session, new return)
> Customer completes a return for ORD-123, then says "I also want to return ORD-456"

**Handling:** After ORD-123 is complete, `active_category` is cleared. The new message is classified as RETURNS_REFUNDS again. The state machine reset code at line 156 fires, setting `agent.workflow_state = None`. Fresh state machine created on next run. ✓ Note: `agent.messages` (conversation history) persists across the session — this is correct behavior, as the LLM can see the previous exchange for context.

### Edge Case 7: `reason` parameter passes length check but is LLM-fabricated
> LLM calls `execute_order_return(order_id="ORD-123", reason="Customer changed mind")`
> (LLM assumed reason instead of using customer's words)

**Handling:** Length validation (`len > 5`) passes. This is a prompt responsibility, not a code responsibility. The code gate ensures the tool is not called prematurely; the prompt ensures the reason reflects the customer's actual words. This is the appropriate split: code handles sequencing guarantees, prompt handles semantic quality. If this becomes a recurring audit issue, a secondary check can compare the reason to the last few messages in `self.messages` — but that's a Phase 2 enhancement.

---

## What This Does NOT Change

- **Router logic** (`router.py`): Classification is working correctly. No changes.
- **Tool definitions** (`tools.py`): Tool schemas are correct. No changes.
- **Services** (`services.py`): Backend implementations are correct. No changes.
- **VIP exception response format**: Still prompt-guided. Code handles sequencing, prompt handles formatting.
- **Book recommendation upsell**: Still prompt-guided (`get_book_recommendations` gate: `state >= POLICY_CHECKED`). The offer, tone, and handling of acceptance/decline remain LLM-controlled.
- **Anger detection sensitivity**: Still prompt-guided. Detecting emotional nuance from text is a genuine LLM strength. The code gate just ensures `escalate_order_issue` is always unblocked.
- **Non-VIP precedent handling** (holiday gifts, etc.): Still prompt-guided. The conditional logic for when to check non-VIP precedents is complex and context-dependent — appropriate for the LLM layer.

---

## Testing Approach After Implementation

### Unit Tests for State Machine (`workflow/returns_state_machine.py`)
1. Test each gate in isolation (tool X blocked before state Y, allowed after)
2. Test state advancement (tool X success → state Z)
3. Test `is_terminal()` for COMPLETE and ESCALATED states
4. Test `run_count_after_greeting` increment logic
5. Test `reason` validation: empty, short, "n/a", valid

### Integration Tests (extend existing test files)
1. **`test_return_reason_mandatory.py`**: Add test that `execute_order_return` returns error when called before `get_policy_info` (state gate)
2. **`test_complete_workflow.py`**: Verify state machine reaches COMPLETE on happy path
3. New test: Verify `get_policy_info` is blocked in same ReAct turn as `get_customer_info`
4. New test: Verify `execute_order_return` with empty reason returns error, not processes return

### Manual Smoke Tests
1. Run the book return happy path end-to-end (ORD-001 or similar from mock data)
2. Verify audit log shows `TOOL_BLOCKED` events are NOT present on normal happy path (gates should not fire if LLM follows sequence)
3. Run with a modified prompt that intentionally skips the condition question — verify `get_policy_info` is blocked and LLM recovers
4. Run angry customer scenario — verify escalation completes and `is_terminal()` returns True

---

## References

- [Anthropic - Building Effective Agents](https://www.anthropic.com/research/building-effective-agents): "You can add programmatic checks on any intermediate steps to ensure that the process is still on track."
- [Applied LLMs - What We Learned](https://applied-llms.org/): "LLMs will return output even when they shouldn't." Guardrails and prompt engineering serve different functions.
- [Eugene Yan - LLM Patterns](https://eugeneyan.com/writing/llm-patterns/): Syntactic guardrails (code) for categorical validation; semantic guardrails (LLM) for nuanced judgment.
- [sgnt.ai - Get the Hell Out of the LLM](https://sgnt.ai/p/hell-out-of-llms/): "Get into the LLM only for the parts that genuinely require natural language understanding. Get out as fast as possible."
- [Oso - Why Authorization Keeps LLMs in Check](https://www-webflow.osohq.com/post/why-authorization-keeps-llms-in-check): "LLMs don't enforce rules, they interpret them."
