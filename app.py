import chainlit as cl
from agent.agent import SupportAgent
from observability.tracing import setup_phoenix_tracing
from logging_config import setup_logging
from admin.decision_reviewer import handle_admin_query
from router.router import QuestionRouter, QuestionCategory
from typing import Any
import logging
from dotenv import load_dotenv

# Load environment variables FIRST (before anything that uses them)
load_dotenv()

# Initialize Logging FIRST (before anything else)
audit_logger = setup_logging()
logger = logging.getLogger("Bookly App")

# Initialize Tracing ONCE at startup
setup_phoenix_tracing()

@cl.set_chat_profiles
async def chat_profile() -> list[cl.ChatProfile]:
    """
    Define two chat profiles:
    - Bookly Support: Normal agent interaction
    - Bookly Admin: Decision trace investigation
    """
    return [
        cl.ChatProfile(
            name="Bookly Support",
            markdown_description="Talk to our AI assistant for help with orders, returns, and bookshop questions."
            # icon parameter removed - text-only display
        ),
        cl.ChatProfile(
            name="Bookly Admin",
            markdown_description="**Admin Only**: View decision traces for any customer session. Enter a session ID to investigate agent decisions and precedent usage."
            # icon parameter removed - text-only display
        )
    ]

@cl.on_chat_start
async def start() -> None:
    """
    Initialize session based on selected chat profile.
    Routes to either customer agent or admin viewer.
    """
    # Get selected profile from session
    chat_profile: str | None = cl.user_session.get("chat_profile")

    # Capture Chainlit user for Arize session tracking (if authenticated)
    user = cl.user_session.get("user")
    if user:
        user_id = getattr(user, 'identifier', None) or getattr(user, 'id', None)
        cl.user_session.set("user_id", user_id)
        logger.info(f"User authenticated: {user_id}")

    if chat_profile == "Bookly Admin":
        # Admin mode: Store profile flag and send instructions
        cl.user_session.set("mode", "admin")

        await cl.Message(
            content="""# Decision Trace Viewer

Welcome to the INTERNAL decision review interface. This tool allows you to investigate agent decisions from any customer session.

**How to use:**
1. Enter a session ID in the format: `SESSION-xxxxxxxx`
2. I'll retrieve all decision events for that session
3. View precedent matches, agent decisions, and attribution

**Example Session IDs:**
- `SESSION-e87df8dd`
- `TEST-SESSION-001`

Enter a session ID to begin investigation:"""
        ).send()
    else:
        # Customer mode: Initialize agent and router
        cl.user_session.set("mode", "customer")
        cl.user_session.set("agent", SupportAgent())
        cl.user_session.set("router", QuestionRouter())
        cl.user_session.set("active_category", None)  # Track active workflow category
        logger.info("Customer support session initialized with question router")
    
@cl.on_message
async def main(message: cl.Message) -> None:
    """
    Route message handling based on chat profile mode.
    For customer messages, first classify the question type using the router.
    """
    mode: str | None = cl.user_session.get("mode")

    if mode == "admin":
        # Handle admin session ID query
        await handle_admin_query(message.content)
    else:
        # Customer support mode with question routing
        agent: Any = cl.user_session.get("agent")
        router: QuestionRouter = cl.user_session.get("router")
        user_id: str | None = cl.user_session.get("user_id")  # For Arize session tracking

        # Ensure agent has a session_id for Arize tracking (before router call)
        # This ensures router classification and agent calls share the same session
        if not agent.session_id:
            import uuid
            agent.session_id = f"SESSION-{uuid.uuid4().hex[:8]}"
            from logging_config import set_session_id
            set_session_id(agent.session_id)
            logger.info(f"Generated session ID for conversation: {agent.session_id}")

        # Send an empty message to show the "Thinking" state
        msg: cl.Message = cl.Message(content="")
        await msg.send()

        try:
            # Step 1: Check if we're in an active workflow
            active_category = cl.user_session.get("active_category")

            # Detect if this is a new question or a continuation response
            message_lower = message.content.lower().strip()

            # Indicators of a NEW question (should re-classify):
            is_new_question = (
                active_category is None or  # No active workflow
                any(word in message_lower for word in ['can i', 'how do i', 'what is', 'where is', 'when will', 'i want to', 'i need to', 'please help']) or  # Question phrases
                (len(message.content.strip()) > 50 and '?' in message.content)  # Long message with question mark
            )

            # Indicators of a CONTINUATION (should NOT re-classify):
            is_continuation = (
                active_category is not None and
                (
                    message_lower.startswith('ord-') or  # Order ID response
                    len(message.content.strip()) < 30 or  # Short response
                    message_lower in ['yes', 'no', 'ok', 'sure', 'thanks', 'thank you']  # Simple acknowledgments
                )
            )

            # Decision: Re-classify or continue with active category
            should_reclassify = is_new_question and not is_continuation

            if should_reclassify:
                # Classify the question using the router
                # Pass session_id and user_id for Arize session tracking
                logger.info(f"Routing question: {message.content[:100]}...")
                category = router.classify_question(
                    message.content,
                    session_id=agent.session_id,
                    user_id=user_id
                )
                category_desc = router.get_category_description(category)

                logger.info(f"Question classified as: {category.value} - {category_desc}")

                # Store the category for this workflow
                cl.user_session.set("active_category", category)
            else:
                # Continue with the active workflow category
                category = active_category
                category_desc = router.get_category_description(category)
                logger.info(f"📌 Continuing with active workflow: {category.value} (not re-classifying)")
                logger.info(f"   Reason: Detected continuation response, not a new question")

            # Log the routing decision (for analytics and monitoring)
            audit_logger.info(
                "Question routed",
                extra={
                    'user_message': message.content,
                    'category': category.value,
                    'category_description': category_desc,
                    'event_type': 'QUESTION_ROUTED'
                }
            )

            # Step 2: Handle based on category with specialized prompt and tools
            if category == QuestionCategory.ORDER_STATUS:
                # Order tracking: focused on delivery and tracking
                logger.info("Routing to ORDER_STATUS handler with specialized prompt and tools")
                response = agent.run(message.content, category=category, user_id=user_id)

            elif category == QuestionCategory.RETURNS_REFUNDS:
                # Returns/refunds: full agent with all tools and complex workflow
                logger.info("Routing to RETURNS_REFUNDS handler with full agent capabilities")
                response = agent.run(message.content, category=category, user_id=user_id)

            elif category == QuestionCategory.GENERAL:
                # General questions: focused on policy documents and information
                logger.info("Routing to GENERAL handler with policy-focused tools")
                response = agent.run(message.content, category=category, user_id=user_id)
            else:
                # Fallback (should not reach here)
                logger.warning(f"Unknown category: {category}, using default configuration")
                response = agent.run(message.content, user_id=user_id)

            # Step 3: Update the UI with the final response
            msg.content = response
            await msg.update()

            # Step 4: Check if workflow is complete or continuing
            # If agent asks a question, keep the active category for next message
            # If agent provides final answer, clear the category
            response_lower = response.lower()

            # Indicators that agent is asking for more info (workflow continues):
            is_asking_question = (
                '?' in response or
                'please provide' in response_lower or
                'could you' in response_lower or
                'can you' in response_lower or
                'i need' in response_lower or
                'what' in response_lower
            )

            # Indicators that workflow is complete:
            is_complete = (
                'refund processed' in response_lower or
                'return approved' in response_lower or
                'escalate' in response_lower or
                'transfer' in response_lower or
                (not is_asking_question and len(response) > 100)  # Long final answer
            )

            if is_complete:
                # Clear active category - workflow is done
                cl.user_session.set("active_category", None)
                logger.info(f"✓ Workflow complete, cleared active category")
            elif is_asking_question:
                # Keep active category - agent is waiting for response
                logger.info(f"📋 Workflow continuing, keeping active category: {category.value}")

        except Exception as e:
            logger.error(f"Error in message handling: {str(e)}", exc_info=True)
            msg.content = (
                "I apologize, but I encountered an error processing your request. "
                "Please try again, or contact our support team at support@bookly.com "
                "if the issue persists."
            )
            await msg.update()