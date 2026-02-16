"""
Test Suite: Mandatory Return Reason Collection

This test suite verifies that the agent:
1. Always asks for a return reason
2. Re-prompts if the customer doesn't provide a reason
3. Does not proceed with return processing without a valid reason
4. Uses the customer's exact reason when calling tools

Test Scenarios:
- Customer provides reason upfront
- Customer doesn't provide reason initially (needs re-prompt)
- Customer provides vague response (needs re-prompt)
- Customer refuses after multiple attempts (escalates)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agent.agent import SupportAgent
from router.router import QuestionCategory


class TestReturnReasonMandatory:
    """
    Tests for mandatory return reason collection workflow
    """

    def test_agent_asks_for_reason_in_greeting(self):
        """
        SCENARIO: Agent should ask "why" in the greeting after looking up order

        EXPECTED: The agent's first response should include:
        - Personalized greeting with customer name
        - Question asking for return reason: "Could you please tell me why you'd like to return this item?"
        """
        # This is a manual test case - verify by observing agent behavior
        # When customer says "I want to return ORD-123", agent should:
        # 1. Ask for order ID (if not provided)
        # 2. Look up order
        # 3. Get customer info
        # 4. Output greeting + ask "Could you please tell me why you'd like to return this item?"
        pass

    def test_agent_reprompts_when_no_reason_provided(self):
        """
        SCENARIO: Customer says "Just process it" without giving a reason

        EXPECTED: Agent should detect missing reason and re-prompt with:
        "I understand. To process your return, I need to collect the reason for the return..."
        """
        # This is a manual test case - verify by testing conversation flow
        # Conversation:
        # Customer: "I want to return ORD-123"
        # Agent: [greets] "Could you please tell me why you'd like to return this item?"
        # Customer: "Just process it please"  ← NO REASON
        # Agent: Should use FIRST RE-PROMPT with explanation
        pass

    def test_agent_accepts_valid_reason(self):
        """
        SCENARIO: Customer provides a clear, specific reason

        VALID REASONS:
        - "It wasn't what I expected"
        - "Wrong book shipped"
        - "Changed my mind"
        - "No longer need it"
        - "Arrived damaged"

        EXPECTED: Agent captures reason and proceeds to ask condition question
        """
        # Manual test - verify agent accepts these reasons and moves forward
        pass

    def test_agent_rejects_vague_responses(self):
        """
        SCENARIO: Customer gives vague non-answer

        INVALID RESPONSES:
        - "Because"
        - "I don't know"
        - "Just because"
        - [Ignores question entirely]

        EXPECTED: Agent should re-prompt for a valid reason
        """
        # Manual test - verify agent doesn't accept these as valid reasons
        pass

    def test_agent_escalates_after_three_refusals(self):
        """
        SCENARIO: Customer refuses to provide reason after 3 prompts

        FLOW:
        1. First ask: "Could you please tell me why..."
        2. Customer refuses
        3. Second prompt: "I understand. To process your return, I need..."
        4. Customer refuses
        5. Third prompt: "I apologize for the inconvenience. Our return policy requires..."
        6. Customer refuses
        7. Fourth prompt: "I understand this may seem unnecessary, but I'm unable to process..."
        8. Offer escalation

        EXPECTED: After 3 refusals, agent should call escalate_to_human
        """
        # Manual test - verify escalation happens after persistence
        pass

    def test_tool_called_with_customer_provided_reason(self):
        """
        SCENARIO: Verify execute_order_return is called with the EXACT reason customer provided

        CUSTOMER SAYS: "The book arrived damaged"

        EXPECTED: Tool call should be:
        execute_order_return(order_id="ORD-123", reason="The book arrived damaged")

        NOT:
        execute_order_return(order_id="ORD-123", reason="damaged")  ← Shortened
        execute_order_return(order_id="ORD-123", reason="Customer dissatisfied")  ← Fabricated
        """
        # This requires examining agent logs to verify the tool call parameters
        pass

    def test_process_exchange_also_requires_reason(self):
        """
        SCENARIO: When using process_exchange for book recommendations

        EXPECTED: The process_exchange tool also requires return_reason parameter
        Verify that the agent includes the customer's reason when calling this tool
        """
        # Manual test - verify process_exchange includes return_reason from customer
        pass


class TestReturnReasonEdgeCases:
    """
    Edge case tests for return reason handling
    """

    def test_customer_provides_reason_in_initial_message(self):
        """
        SCENARIO: Customer says "I want to return ORD-123 because it arrived damaged"

        EXPECTED: Agent should:
        - Recognize reason was already provided ("arrived damaged")
        - NOT ask for reason again
        - Proceed directly to condition question after greeting
        """
        pass

    def test_customer_provides_multiple_reasons(self):
        """
        SCENARIO: Customer says "I want to return it because I ordered the wrong one and it also arrived late"

        EXPECTED: Agent should capture the full reason:
        "ordered the wrong one and it also arrived late"
        """
        pass

    def test_reason_collected_persists_through_workflow(self):
        """
        SCENARIO: Verify reason is not lost during the workflow

        FLOW:
        1. Customer provides reason: "Changed my mind"
        2. Agent asks condition question
        3. Customer responds about condition
        4. Agent checks policy
        5. Agent checks VIP status
        6. Agent processes return

        EXPECTED: When calling execute_order_return, the reason should still be "Changed my mind"
        (not lost or changed during the workflow)
        """
        pass


# Test Data Examples
VALID_REASONS = [
    "It wasn't what I expected",
    "Wrong book was shipped",
    "Changed my mind",
    "Duplicate order",
    "Found it cheaper elsewhere",
    "Book arrived damaged",
    "Delivery was too late",
    "No longer need it",
    "Ordered wrong item by mistake",
    "The cover is different than advertised",
    "Book has missing pages",
]

INVALID_RESPONSES = [
    "Just process it",
    "Because",
    "I don't know",
    "Just because",
    "I'd rather not say",
    "",  # Empty response
    "Can you just do it?",
    "Do I have to?",
]


if __name__ == "__main__":
    print("=" * 70)
    print("RETURN REASON MANDATORY - TEST CASES")
    print("=" * 70)
    print("\nThese are manual test cases to verify the agent properly:")
    print("1. ✓ Asks for return reason in greeting")
    print("2. ✓ Detects when reason is missing")
    print("3. ✓ Re-prompts with escalating messages")
    print("4. ✓ Captures exact reason from customer")
    print("5. ✓ Does not proceed without valid reason")
    print("6. ✓ Escalates after 3 refusals")
    print("\n" + "=" * 70)
    print("VALID REASONS (should be accepted):")
    print("=" * 70)
    for reason in VALID_REASONS:
        print(f"  ✓ '{reason}'")

    print("\n" + "=" * 70)
    print("INVALID RESPONSES (should trigger re-prompt):")
    print("=" * 70)
    for response in INVALID_RESPONSES:
        print(f"  ✗ '{response}'")

    print("\n" + "=" * 70)
    print("TEST INSTRUCTIONS:")
    print("=" * 70)
    print("""
To manually test:
1. Start the application: chainlit run app.py
2. Select "Bookly Support" profile
3. Test each scenario:

   TEST 1: Customer provides reason upfront
   You: "I want to return ORD-123 because it's damaged"
   Expected: Agent should capture "damaged" and not ask for reason again

   TEST 2: Customer doesn't provide reason
   You: "I want to return ORD-123"
   Agent: [Should ask for reason]
   You: "Just process it"  ← No reason
   Expected: Agent should re-prompt with explanation

   TEST 3: Customer provides reason after re-prompt
   You: "I want to return ORD-123"
   Agent: [Asks for reason]
   You: "Just do it"  ← No reason
   Agent: [Re-prompts with explanation]
   You: "Changed my mind"  ← Valid reason
   Expected: Agent accepts and proceeds

   TEST 4: Customer refuses multiple times
   You: "I want to return ORD-123"
   Agent: [Asks for reason]
   You: "I don't want to say"
   Agent: [Re-prompt 1]
   You: "No"
   Agent: [Re-prompt 2]
   You: "Still no"
   Agent: [Re-prompt 3 with escalation offer]
   Expected: Agent should offer to escalate

4. Verify in logs that execute_order_return is called with the exact reason
5. Check that agent NEVER proceeds without collecting a reason
""")
