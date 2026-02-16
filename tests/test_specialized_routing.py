"""
Test suite for specialized routing with dynamic prompts and tool filtering.

This test verifies that:
1. Different categories use different system prompts
2. Different categories have different tool sets
3. The router correctly classifies questions
4. The agent uses category-specific configuration
"""

import pytest
from router.router import QuestionRouter, QuestionCategory
from prompts import get_prompt_for_category, get_tools_for_category


class TestPromptSelection:
    """Test that correct prompts are selected for each category"""

    def test_order_status_prompt(self):
        """ORDER_STATUS should get tracking-focused prompt"""
        prompt = get_prompt_for_category(QuestionCategory.ORDER_STATUS)
        assert "Order Tracking Specialist" in prompt
        assert "look_up_order" in prompt
        assert "tracking" in prompt.lower()

    def test_returns_refunds_prompt(self):
        """RETURNS_REFUNDS should get full workflow prompt"""
        prompt = get_prompt_for_category(QuestionCategory.RETURNS_REFUNDS)
        assert "Returns & Refunds Specialist" in prompt
        assert "VIP" in prompt
        assert "check_precedents" in prompt
        assert "PRIME DIRECTIVE" in prompt

    def test_general_prompt(self):
        """GENERAL should get policy-focused prompt"""
        prompt = get_prompt_for_category(QuestionCategory.GENERAL)
        assert "Information Assistant" in prompt
        assert "get_policy_info" in prompt
        assert "policy" in prompt.lower()

    def test_prompts_are_different(self):
        """Each category should have a distinct prompt"""
        order_prompt = get_prompt_for_category(QuestionCategory.ORDER_STATUS)
        returns_prompt = get_prompt_for_category(QuestionCategory.RETURNS_REFUNDS)
        general_prompt = get_prompt_for_category(QuestionCategory.GENERAL)

        assert order_prompt != returns_prompt
        assert returns_prompt != general_prompt
        assert order_prompt != general_prompt


class TestToolFiltering:
    """Test that correct tools are available for each category"""

    def test_order_status_tools(self):
        """ORDER_STATUS should have limited tool set"""
        tools = get_tools_for_category(QuestionCategory.ORDER_STATUS)
        assert "look_up_order" in tools
        assert "get_customer_info" in tools
        assert "escalate_to_human" in tools

        # Should NOT have these tools
        assert "execute_order_return" not in tools
        assert "check_vip_status" not in tools
        assert "check_precedents" not in tools

    def test_returns_refunds_tools(self):
        """RETURNS_REFUNDS should have ALL tools"""
        tools = get_tools_for_category(QuestionCategory.RETURNS_REFUNDS)

        # Should have all 9 tools (includes recommendation and exchange features)
        assert "look_up_order" in tools
        assert "get_customer_info" in tools
        assert "get_policy_info" in tools
        assert "execute_order_return" in tools
        assert "escalate_to_human" in tools
        assert "check_vip_status" in tools
        assert "check_precedents" in tools
        assert "get_book_recommendations" in tools
        assert "process_exchange" in tools

        assert len(tools) == 9

    def test_general_tools(self):
        """GENERAL should have minimal tool set"""
        tools = get_tools_for_category(QuestionCategory.GENERAL)
        assert "get_policy_info" in tools
        assert "escalate_to_human" in tools

        # Should NOT have these tools
        assert "look_up_order" not in tools
        assert "execute_order_return" not in tools
        assert "check_vip_status" not in tools
        assert "check_precedents" not in tools

    def test_tool_counts(self):
        """Verify tool counts are as expected"""
        order_tools = get_tools_for_category(QuestionCategory.ORDER_STATUS)
        returns_tools = get_tools_for_category(QuestionCategory.RETURNS_REFUNDS)
        general_tools = get_tools_for_category(QuestionCategory.GENERAL)

        assert len(order_tools) == 3  # Limited set
        assert len(returns_tools) == 9  # All tools (includes recommendations & exchange)
        assert len(general_tools) == 2  # Minimal set


class TestRouterIntegration:
    """Test that router correctly classifies questions for specialized handling"""

    @pytest.fixture
    def router(self):
        return QuestionRouter()

    def test_order_status_classification(self, router):
        """Order tracking questions should route to ORDER_STATUS"""
        questions = [
            "Where is my order?",
            "Track order ORD-123",
            "Has my package shipped?",
            "When will my books arrive?"
        ]
        for question in questions:
            category = router.classify_question(question)
            assert category == QuestionCategory.ORDER_STATUS, \
                f"'{question}' should be ORDER_STATUS, got {category}"

    def test_returns_refunds_classification(self, router):
        """Return requests should route to RETURNS_REFUNDS"""
        questions = [
            "I want to return a book",
            "How do I get a refund?",
            "Process return for ORD-456",
            "Can I exchange this book?"
        ]
        for question in questions:
            category = router.classify_question(question)
            assert category == QuestionCategory.RETURNS_REFUNDS, \
                f"'{question}' should be RETURNS_REFUNDS, got {category}"

    def test_general_classification(self, router):
        """General questions should route to GENERAL"""
        questions = [
            "What's your shipping policy?",
            "How do I reset my password?",
            "Do you sell audiobooks?",
            "What are your business hours?"
        ]
        for question in questions:
            category = router.classify_question(question)
            assert category == QuestionCategory.GENERAL, \
                f"'{question}' should be GENERAL, got {category}"


class TestEndToEndSpecialization:
    """Test the complete flow of specialized routing"""

    def test_order_status_gets_limited_tools(self):
        """ORDER_STATUS category should result in limited tool availability"""
        category = QuestionCategory.ORDER_STATUS
        tools = get_tools_for_category(category)
        prompt = get_prompt_for_category(category)

        # Verify tools are limited
        assert len(tools) < 5
        assert "execute_order_return" not in tools

        # Verify prompt is tracking-focused
        assert "tracking" in prompt.lower() or "order" in prompt.lower()

    def test_returns_refunds_gets_full_capability(self):
        """RETURNS_REFUNDS should get complete tool set and comprehensive prompt"""
        category = QuestionCategory.RETURNS_REFUNDS
        tools = get_tools_for_category(category)
        prompt = get_prompt_for_category(category)

        # Verify full tool set (9 tools includes recommendations & exchange)
        assert len(tools) == 9
        assert "check_vip_status" in tools
        assert "check_precedents" in tools
        assert "get_book_recommendations" in tools
        assert "process_exchange" in tools

        # Verify comprehensive prompt
        assert "VIP" in prompt
        assert "precedent" in prompt.lower()

    def test_general_gets_policy_focus(self):
        """GENERAL should get policy-focused tools and prompt"""
        category = QuestionCategory.GENERAL
        tools = get_tools_for_category(category)
        prompt = get_prompt_for_category(category)

        # Verify policy-focused tools
        assert "get_policy_info" in tools
        assert len(tools) == 2

        # Verify information-focused prompt
        assert "policy" in prompt.lower() or "information" in prompt.lower()


class TestPromptContent:
    """Test that prompts contain appropriate instructions"""

    def test_order_status_prompt_boundaries(self):
        """ORDER_STATUS prompt should clearly define what NOT to handle"""
        prompt = get_prompt_for_category(QuestionCategory.ORDER_STATUS)

        # Should mention what NOT to handle
        assert "Do NOT" in prompt or "NOT handle" in prompt
        # Should mention returns are out of scope
        assert "return" in prompt.lower()

    def test_returns_refunds_prompt_has_vip_protocol(self):
        """RETURNS_REFUNDS prompt should have VIP exception protocol"""
        prompt = get_prompt_for_category(QuestionCategory.RETURNS_REFUNDS)

        assert "check_vip_status" in prompt
        assert "check_precedents" in prompt
        assert "AUTOMATIC" in prompt or "MANDATORY" in prompt

    def test_general_prompt_has_policy_instructions(self):
        """GENERAL prompt should have policy retrieval instructions"""
        prompt = get_prompt_for_category(QuestionCategory.GENERAL)

        assert "get_policy_info" in prompt
        assert "shipping" in prompt.lower()
        assert "privacy" in prompt.lower() or "return" in prompt.lower()


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_none_category_returns_default(self):
        """Passing None should return a default prompt and all tools"""
        prompt = get_prompt_for_category(None)
        tools = get_tools_for_category(None)

        assert prompt is not None
        assert tools is None  # Should use all tools by default

    def test_invalid_category_handles_gracefully(self):
        """Invalid category should not crash"""
        try:
            # Create a mock invalid category
            class FakeCategory:
                value = "INVALID"

            prompt = get_prompt_for_category(FakeCategory())
            tools = get_tools_for_category(FakeCategory())

            # Should return defaults without crashing
            assert prompt is not None
            assert tools is not None or tools is None
        except Exception as e:
            pytest.fail(f"Should handle invalid category gracefully, but got: {e}")


# Performance and efficiency tests
class TestEfficiencyGains:
    """Test that specialization provides efficiency gains"""

    def test_reduced_tool_set_for_simple_tasks(self):
        """Simple tasks should have fewer tools to reduce token usage"""
        order_tools = get_tools_for_category(QuestionCategory.ORDER_STATUS)
        general_tools = get_tools_for_category(QuestionCategory.GENERAL)
        returns_tools = get_tools_for_category(QuestionCategory.RETURNS_REFUNDS)

        # Simple tasks should have fewer tools
        assert len(order_tools) < len(returns_tools)
        assert len(general_tools) < len(returns_tools)

    def test_focused_prompts_are_shorter(self):
        """Specialized prompts should be more focused than full prompt"""
        order_prompt = get_prompt_for_category(QuestionCategory.ORDER_STATUS)
        returns_prompt = get_prompt_for_category(QuestionCategory.RETURNS_REFUNDS)

        # ORDER_STATUS prompt should be shorter (more focused)
        # RETURNS_REFUNDS is the complex workflow, so it's naturally longer
        assert len(order_prompt) < len(returns_prompt)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
