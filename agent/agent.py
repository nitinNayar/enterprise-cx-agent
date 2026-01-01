import anthropic
import logging
import json

from services.services import EnterpriseServices
from tools.tools import tools_schema
from config import Config

logger = logging.getLogger("Claude Agent")

class SupportAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.messages = [] # conversation history
    
    def run(self, user_input):
        logger.info(f"User Input {user_input}")
        self.messages.append({"role":"user", "content": user_input})

        # 1.    First call to Claude to determine Intent
        response = self.client.messages.create(
            model=Config.MODEL_NAME,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
            system=Config.SYSTEM_PROMPT,
            messages=self.messages,
            tools=tools_schema
        )

        # 1.5   for debugging, lets print out what response looks like
        # This converts the object to a pretty-printed string before passing to the logger
        logger.debug(
            "Full API Response:\n%s", 
            json.dumps(response.__dict__, indent=2, default=str)
        ) 

        # 2.    Add Assistant's response to history
        self.messages.append({"role": "assistant", "content": response.content})

        # 3.    Check if Claude wants to use tools
        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

        if tool_use_blocks:
            tool_result_content = []

            for block in tool_use_blocks:
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                logger.info(f"Decision: Agent Selected tool {tool_name} with input {tool_input}")

                result = None

                if tool_name == "look_up_order":
                    result = EnterpriseServices.look_up_order(tool_input.get("order_id"))
                elif tool_name == "execute_order_return":
                    result = EnterpriseServices.execute_refund(tool_input.get("order_id"), tool_input.get("reason"))
                elif tool_name == "escalate_to_human":
                    result = EnterpriseServices.escalate_to_human(tool_input.get("order_id"), tool_input.get("reason"))
                else:
                    # Handle the "Hallucinated Tool" case safely
                    logger.error(f"Unknown tool called: {tool_name}")
                    result = {"error": f"Tool '{tool_name}' not found."}

                # Format Result for Anthropic
                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(result)
                })

            # # 3.5   for debugging, lets print out what result looks like
            # # This converts the object to a pretty-printed string before passing to the logger
            # logger.debug(
            #     "Full Tool Result:\n%s", 
            #     json.dumps(result.__dict__, indent=2, default=str)
            # ) 

            # 4.    send tool results back to Claude
            self.messages.append({"role": "user", "content": tool_result_content})

            # 5.    Get Final result based on tool output
            final_response = self.client.messages.create(
                model=Config.MODEL_NAME,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                system=Config.SYSTEM_PROMPT,
                messages=self.messages,
                tools=tools_schema
            )

            final_text = final_response.content[0].text
            self.messages.append({"role": "assistant", "content": final_text})
            
            logger.info("CYCLE COMPLETE: Sent final response to user.")
            return final_text

        else:
            # No tool used
            text_response = response.content[0].text
            logger.info("CYCLE COMPLETE: Sent text response (No tools).")
            return text_response