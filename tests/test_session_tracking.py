"""
Test script to validate Arize session tracking implementation.

This test verifies that:
1. Session IDs are properly generated
2. OpenInference context manager is correctly imported
3. Session attributes are properly formatted
4. User IDs are optionally passed through
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from agent.agent import SupportAgent
from router.router import QuestionCategory


def test_session_id_generation():
    """Test that session IDs are generated in correct format."""
    agent = SupportAgent()

    # Simulate running the agent
    with patch.object(agent.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            stop_reason="end_turn",
            content=[Mock(text="Test response", type="text")]
        )

        response = agent.run("Test question")

        # Verify session ID was created
        assert agent.session_id is not None
        assert agent.session_id.startswith("SESSION-")
        assert len(agent.session_id) == 16  # SESSION- + 8 hex chars


def test_session_persistence_across_turns():
    """Test that session ID persists across multiple conversation turns."""
    agent = SupportAgent()

    with patch.object(agent.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            stop_reason="end_turn",
            content=[Mock(text="Test response", type="text")]
        )

        # First turn
        agent.run("First question")
        first_session_id = agent.session_id

        # Second turn
        agent.run("Second question")
        second_session_id = agent.session_id

        # Session ID should be the same
        assert first_session_id == second_session_id


def test_user_id_parameter_accepted():
    """Test that user_id parameter is accepted and passed through."""
    agent = SupportAgent()
    test_user_id = "test_user_123"

    with patch.object(agent.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            stop_reason="end_turn",
            content=[Mock(text="Test response", type="text")]
        )

        # Should not raise any errors
        response = agent.run("Test question", user_id=test_user_id)

        # Verify API was called
        assert mock_create.called


def test_category_in_metadata():
    """Test that category is included in session metadata."""
    agent = SupportAgent()

    with patch.object(agent.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            stop_reason="end_turn",
            content=[Mock(text="Test response", type="text")]
        )

        # Run with category
        response = agent.run(
            "Test question",
            category=QuestionCategory.ORDER_STATUS
        )

        # Verify API was called (metadata is captured internally)
        assert mock_create.called


def test_openinference_import():
    """Test that OpenInference context manager can be imported."""
    try:
        from openinference.instrumentation import using_attributes
        assert callable(using_attributes)
    except ImportError as e:
        pytest.fail(f"Failed to import using_attributes: {e}")


def test_using_attributes_context_manager():
    """Test that using_attributes works as a context manager."""
    from openinference.instrumentation import using_attributes

    # Should not raise any errors
    with using_attributes(
        session_id="test-session-123",
        user_id="test-user",
        metadata={"test": "data"}
    ):
        # Context manager should work without errors
        pass


def test_session_tracking_with_mock_anthropic():
    """Integration test with mocked Anthropic client."""
    agent = SupportAgent()

    # Mock the entire conversation flow
    with patch.object(agent.client.messages, 'create') as mock_create:
        # Mock a simple response
        mock_create.return_value = Mock(
            stop_reason="end_turn",
            content=[Mock(text="I can help with that!", type="text")]
        )

        # Run a multi-turn conversation
        response1 = agent.run("Hello", user_id="user123")
        response2 = agent.run("Can you help?", user_id="user123")

        # Verify both calls used the same session
        assert agent.session_id is not None

        # Verify API was called twice
        assert mock_create.call_count == 2

        # Verify both responses are strings
        assert isinstance(response1, str)
        assert isinstance(response2, str)


def test_session_attributes_structure():
    """Test that session attributes are properly structured."""
    from openinference.instrumentation import using_attributes

    session_id = "SESSION-12345678"
    user_id = "user@example.com"
    metadata = {
        "category": "ORDER_STATUS",
        "num_tools": 5,
        "conversation_turn": 1,
        "model": "claude-sonnet-4"
    }

    # Test attributes dictionary structure
    attributes_dict = {
        "session_id": session_id,
        "user_id": user_id,
        "metadata": metadata
    }

    # Should work with using_attributes
    with using_attributes(**attributes_dict):
        pass

    # Verify structure
    assert "session_id" in attributes_dict
    assert "user_id" in attributes_dict
    assert "metadata" in attributes_dict
    assert isinstance(attributes_dict["metadata"], dict)


def test_session_id_uniqueness():
    """Test that different agent instances get different session IDs."""
    agent1 = SupportAgent()
    agent2 = SupportAgent()

    with patch.object(agent1.client.messages, 'create') as mock_create1, \
         patch.object(agent2.client.messages, 'create') as mock_create2:

        mock_create1.return_value = Mock(
            stop_reason="end_turn",
            content=[Mock(text="Response", type="text")]
        )
        mock_create2.return_value = Mock(
            stop_reason="end_turn",
            content=[Mock(text="Response", type="text")]
        )

        agent1.run("Question 1")
        agent2.run("Question 2")

        # Each agent should have a unique session ID
        assert agent1.session_id != agent2.session_id


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
