import chainlit as cl
from agent.agent import SupportAgent
from observability.tracing import setup_phoenix_tracing 

# Initialize Tracing ONCE at startup
setup_phoenix_tracing()

@cl.on_chat_start
def start():
    # Initialize the agent and store it in the session
    cl.user_session.set("agent", SupportAgent())
    
@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    
    # Send an empty message to show the "Thinking" state
    msg = cl.Message(content="")
    await msg.send()
    
    # Run the Agent Logic (Synchronous call to Anthropic)
    response = agent.run(message.content)
    
    # Update the UI with the final response
    msg.content = response
    await msg.update()