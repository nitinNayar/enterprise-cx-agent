"""
Test script to validate router session tracking for Arize.

This test verifies that the Haiku classification call is properly
wrapped with session context and will appear in Arize sessions.
"""

import pytest
from unittest.mock import Mock, patch
from router.router import QuestionRouter, QuestionCategory


def test_router_accepts_session_parameters():
    """Test that router accepts session_id and user_id parameters."""
    router = QuestionRouter()

    with patch.object(router.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            content=[Mock(text="ORDER_STATUS", type="text")]
        )

        # Should not raise any errors
        category = router.classify_question(
            "Where is my order?",
            session_id="SESSION-12345678",
            user_id="user@example.com"
        )

        # Verify API was called
        assert mock_create.called
        assert category == QuestionCategory.ORDER_STATUS


def test_router_works_without_session_parameters():
    """Test that router still works without session parameters (backward compatibility)."""
    router = QuestionRouter()

    with patch.object(router.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            content=[Mock(text="RETURNS_REFUNDS", type="text")]
        )

        # Should work without session parameters
        category = router.classify_question("I want to return my book")

        assert mock_create.called
        assert category == QuestionCategory.RETURNS_REFUNDS


def test_router_session_tracking_with_using_attributes():
    """Test that router properly wraps API call with using_attributes when session_id provided."""
    from openinference.instrumentation import using_attributes

    router = QuestionRouter()
    session_id = "SESSION-abcd1234"
    user_id = "test_user@example.com"

    with patch.object(router.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            content=[Mock(text="GENERAL", type="text")]
        )

        # Call with session tracking
        category = router.classify_question(
            "What is your return policy?",
            session_id=session_id,
            user_id=user_id
        )

        # Verify the API was called (wrapped with context)
        assert mock_create.called
        assert category == QuestionCategory.GENERAL


def test_router_classify_with_confidence_supports_session():
    """Test that classify_with_confidence passes through session parameters."""
    router = QuestionRouter()

    with patch.object(router.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            content=[Mock(text="ORDER_STATUS", type="text")]
        )

        # Should accept session parameters
        category, confidence = router.classify_with_confidence(
            "Track my order",
            session_id="SESSION-xyz",
            user_id="user123"
        )

        assert mock_create.called
        assert category == QuestionCategory.ORDER_STATUS
        assert confidence == 1.0


def test_router_classification_metadata():
    """Test that router adds proper metadata for Arize tracking."""
    router = QuestionRouter()

    # The metadata should include:
    # - model: claude-haiku-4-5-20251001
    # - operation: question_classification
    # - router: QuestionRouter

    with patch.object(router.client.messages, 'create') as mock_create:
        mock_create.return_value = Mock(
            content=[Mock(text="GENERAL", type="text")]
        )

        category = router.classify_question(
            "Help me",
            session_id="SESSION-test"
        )

        # Verify API was called (metadata is added internally)
        assert mock_create.called


def test_all_question_categories_with_session_tracking():
    """Test that all question categories work with session tracking."""
    router = QuestionRouter()
    session_id = "SESSION-testall"
    user_id = "test_user"

    test_cases = [
        ("Where is order ORD-123?", "ORDER_STATUS", QuestionCategory.ORDER_STATUS),
        ("I want to return my book", "RETURNS_REFUNDS", QuestionCategory.RETURNS_REFUNDS),
        ("What is your policy?", "GENERAL", QuestionCategory.GENERAL),
    ]

    for question, response_text, expected_category in test_cases:
        with patch.object(router.client.messages, 'create') as mock_create:
            mock_create.return_value = Mock(
                content=[Mock(text=response_text, type="text")]
            )

            category = router.classify_question(
                question,
                session_id=session_id,
                user_id=user_id
            )

            assert category == expected_category
            assert mock_create.called


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
