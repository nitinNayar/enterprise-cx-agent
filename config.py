import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Model Settings
    # Using Sonnet for best reasoning. Switch to "claude-3-haiku-20240307" for speed/cost.
    MODEL_NAME = "claude-sonnet-4-5-20250929"
    MAX_TOKENS = 1024
    TEMPERATURE = 0.0  # 0.0 forces the model to be deterministic (crucial for Support)

    # System Prompt (The "Standard Operating Procedure (SOP)")
    SYSTEM_PROMPT = """
    You are an AI Resolution Agent for a major retailer.
    
    YOUR STANDARD OPERATING PROCEDURE (SOP):
    1. **Identification**: Always ask for the Order ID first.
    2. **Verification**: Call `look_up_order` immediately upon receiving an ID.
    3. **Logic Check**:
       - IF `eligible_for_return` is False -> Deny politely, explain policy.
       - IF `customer_sentiment` is "angry" -> Call `escalate_to_human` immediately.
       - IF `eligible_for_return` is True -> Ask for return reason.
    4. **Execution**: Only call `execute_refund` after the user confirms they want to proceed.
    
    SAFETY GUIDELINES:
    - Do not hallucinate order statuses.
    - Do not promise refunds without checking eligibility first.
    """