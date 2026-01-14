import chainlit as cl
from agent.agent import SupportAgent
from observability.tracing import setup_phoenix_tracing
from logging_config import setup_logging
from admin.decision_reviewer import handle_admin_query

# Initialize Logging FIRST (before anything else)
audit_logger = setup_logging()

# Initialize Tracing ONCE at startup
setup_phoenix_tracing()

@cl.set_chat_profiles
async def chat_profile():
    """
    Define two chat profiles:
    - TrueCart Support: Normal agent interaction
    - TrueCart Admin: Decision trace investigation
    """
    return [
        cl.ChatProfile(
            name="TrueCart Support",
            markdown_description="Talk to our AI support agent to resolve your order issues.",
            icon="/public/TrueCart_Light.png"
        ),
        cl.ChatProfile(
            name="TrueCart Admin",
            markdown_description="**Admin Only**: View decision traces for any customer session. Enter a session ID to investigate agent decisions and precedent usage.",
            icon="/public/TrueCart_Light.png"
        )
    ]

@cl.on_chat_start
async def start():
    """
    Initialize session based on selected chat profile.
    Routes to either customer agent or admin viewer.
    """
    # Get selected profile from session
    chat_profile = cl.user_session.get("chat_profile")

    if chat_profile == "TrueCart Admin":
        # Admin mode: Store profile flag and send instructions
        cl.user_session.set("mode", "admin")

        await cl.Message(
            content="""# Decision Trace Viewer

Welcome to the decision review interface. This tool allows you to investigate agent decisions from any customer session.

**How to use:**
1. Enter a session ID in the format: `SESSION-xxxxxxxx`
2. I'll retrieve all decision events for that session
3. View precedent matches, agent decisions, and attribution

**Example Session IDs:**
- `SESSION-e87df8dd`
- `SESSION-56ee7734`
- `TEST-SESSION-001`

Enter a session ID to begin investigation:"""
        ).send()
    else:
        # Customer mode: Initialize agent (existing behavior)
        cl.user_session.set("mode", "customer")
        cl.user_session.set("agent", SupportAgent())
    
@cl.on_message
async def main(message: cl.Message):
    """
    Route message handling based on chat profile mode.
    """
    mode = cl.user_session.get("mode")

    if mode == "admin":
        # Handle admin session ID query
        await handle_admin_query(message.content)
    else:
        # Existing customer agent logic
        agent = cl.user_session.get("agent")

        # Send an empty message to show the "Thinking" state
        msg = cl.Message(content="")
        await msg.send()

        # Run the Agent Logic (Synchronous call to Anthropic)
        response = agent.run(message.content)

        # Update the UI with the final response
        msg.content = response
        await msg.update()