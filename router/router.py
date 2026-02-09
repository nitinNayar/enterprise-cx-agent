"""
Question Router for Bookly Customer Support

This module classifies incoming user questions into one of three categories:
1. ORDER_STATUS - Questions about order tracking, delivery, shipping status
2. RETURNS_REFUNDS - Requests to return items, process refunds, exchanges
3. GENERAL - Questions about policies, account help, password reset, etc.

Uses Claude Haiku 4.5 for cost-effective, fast classification.
"""

import anthropic
import logging
from enum import Enum
from config import Config

logger = logging.getLogger("QuestionRouter")


class QuestionCategory(Enum):
    """Enumeration of possible question categories"""
    ORDER_STATUS = "ORDER_STATUS"
    RETURNS_REFUNDS = "RETURNS_REFUNDS"
    GENERAL = "GENERAL"


class QuestionRouter:
    """
    Routes customer questions to appropriate categories using AI classification.

    Uses Claude Haiku 4.5 for cost-effective intent classification.
    """

    # Model configuration for router (using Haiku for cost efficiency)
    ROUTER_MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 100  # Small output needed
    TEMPERATURE = 0.0  # Deterministic classification

    # Classification prompt
    SYSTEM_PROMPT = """You are a question classifier for Bookly, an online bookshop's customer support system.

Your ONLY task is to classify the user's question into ONE of these three categories:

1. ORDER_STATUS
   - Questions about order tracking, delivery status, shipping updates
   - "Where is my order?", "Has my package shipped?", "When will it arrive?"
   - Looking up order information
   - Checking order history

2. RETURNS_REFUNDS
   - Requests to return books or items
   - Questions about refunds, exchanges, cancellations
   - "I want to return this book", "How do I get a refund?", "Cancel my order"
   - Return policy questions specific to a return request

3. GENERAL
   - Questions about policies (shipping, privacy, returns - general info)
   - Account help, password resets, login issues
   - Product information, recommendations
   - General "how to" questions
   - Anything else not covered by the above two categories

IMPORTANT RULES:
- Respond with ONLY the category name (ORDER_STATUS, RETURNS_REFUNDS, or GENERAL)
- Do not include any explanation, punctuation, or additional text
- If the question mentions both order tracking AND returns, prioritize RETURNS_REFUNDS
- If the question is ambiguous or unclear, default to GENERAL
- Order ID patterns like "ORD-123" usually indicate ORDER_STATUS or RETURNS_REFUNDS

Examples:
User: "Where is my order ORD-456?"
Response: ORDER_STATUS

User: "I want to return the book I ordered"
Response: RETURNS_REFUNDS

User: "What's your shipping policy?"
Response: GENERAL

User: "How do I reset my password?"
Response: GENERAL

User: "Can you help me?"
Response: GENERAL"""

    def __init__(self):
        """Initialize the router with Anthropic client"""
        self.client = anthropic.Anthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            max_retries=3,  # Retry failed requests up to 3 times
            timeout=60.0    # Increase timeout to 60 seconds
        )
        logger.info(f"QuestionRouter initialized with model: {self.ROUTER_MODEL}")

    def classify_question(self, user_message: str) -> QuestionCategory:
        """
        Classify a user question into one of the three categories.

        Args:
            user_message: The user's question text

        Returns:
            QuestionCategory enum value

        Raises:
            ValueError: If classification fails or returns invalid category
        """
        if not user_message or not user_message.strip():
            logger.warning("Empty message received, defaulting to GENERAL")
            return QuestionCategory.GENERAL

        try:
            logger.info(f"Classifying question: {user_message[:100]}...")

            # Call Claude Haiku for classification
            response = self.client.messages.create(
                model=self.ROUTER_MODEL,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            # Extract the classification result
            classification = response.content[0].text.strip().upper()

            # Validate and return the category
            if classification == "ORDER_STATUS":
                logger.info(f"✓ Classified as: ORDER_STATUS")
                return QuestionCategory.ORDER_STATUS
            elif classification == "RETURNS_REFUNDS":
                logger.info(f"✓ Classified as: RETURNS_REFUNDS")
                return QuestionCategory.RETURNS_REFUNDS
            elif classification == "GENERAL":
                logger.info(f"✓ Classified as: GENERAL")
                return QuestionCategory.GENERAL
            else:
                # Invalid response, default to GENERAL
                logger.warning(
                    f"Invalid classification result: '{classification}', "
                    f"defaulting to GENERAL"
                )
                return QuestionCategory.GENERAL

        except Exception as e:
            logger.error(f"Error during classification: {str(e)}", exc_info=True)
            # On error, default to GENERAL (safest fallback)
            logger.warning("Classification failed, defaulting to GENERAL")
            return QuestionCategory.GENERAL

    def classify_with_confidence(self, user_message: str) -> tuple[QuestionCategory, float]:
        """
        Classify a question and return confidence score.

        This is a placeholder for future enhancement. Currently returns
        classification with confidence of 1.0 (high confidence).

        Args:
            user_message: The user's question text

        Returns:
            Tuple of (QuestionCategory, confidence_score)
        """
        category = self.classify_question(user_message)
        # Future enhancement: extract actual confidence from model
        return category, 1.0

    def get_category_description(self, category: QuestionCategory) -> str:
        """
        Get a human-readable description of a category.

        Args:
            category: The question category

        Returns:
            Description string
        """
        descriptions = {
            QuestionCategory.ORDER_STATUS: "Order tracking and delivery status inquiries",
            QuestionCategory.RETURNS_REFUNDS: "Return and refund processing requests",
            QuestionCategory.GENERAL: "General questions about policies and account support"
        }
        return descriptions.get(category, "Unknown category")


# Convenience function for simple usage
def route_question(user_message: str) -> QuestionCategory:
    """
    Convenience function to classify a question without creating a router instance.

    Args:
        user_message: The user's question text

    Returns:
        QuestionCategory enum value

    Note: Creates a new router instance each time. For repeated calls,
        create a QuestionRouter instance and reuse it.
    """
    router = QuestionRouter()
    return router.classify_question(user_message)
