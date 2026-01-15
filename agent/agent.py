import anthropic
import logging
import json
import uuid

from services.services import EnterpriseServices
from tools.tools import tools_schema
from config import Config
from logging_config import get_session_id, set_session_id

logger = logging.getLogger("Claude Agent")
audit_logger = logging.getLogger("DecisionAudit")

class SupportAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.messages = [] # conversation history
        self.session_id = None  # Track session for audit logging
        self.precedent_used = None  # Track if precedent was used in this conversation
    

    def run(self, user_input):
        """
        Executes the main agent loop.
        Handles:
        1. User Input -> Claude
        2. Claude -> Tool Call (Loop)
        3. Tool Result -> Claude (Loop)
        4. Claude -> Final Answer (Exit)
        """

        # --- 1. Setup (Outside the Loop) ---
        # Generate session ID for this conversation turn
        if not self.session_id:
            self.session_id = f"SESSION-{uuid.uuid4().hex[:8]}"
            set_session_id(self.session_id)

        logger.info(f"[{self.session_id}] User Input: {user_input}")

        # Log user message to audit log for conversation trace (only if non-empty)
        if user_input and user_input.strip():
            audit_logger.info(
                "User message",
                extra={
                    'session_id': self.session_id,
                    'user_message': user_input,
                    'event_type': 'USER_MESSAGE'
                }
            )

        self.messages.append({"role": "user", "content": user_input})

        # --- 2. The "Re-Act" Loop ---
        while True:
            
            # Call Claude with current history
            response = self.client.messages.create(
                model=Config.MODEL_NAME,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                system=Config.SYSTEM_PROMPT,
                messages=self.messages,
                tools=tools_schema
            )

            # Debug: See exactly what Claude is thinking/doing
            logger.debug("Full API Response:\n%s", json.dumps(response.__dict__, indent=2, default=str)) 

            # --- EXIT CONDITION: Claude wants to speak ---
            if response.stop_reason == "end_turn":
                final_text = response.content[0].text
                self.messages.append({"role": "assistant", "content": final_text})
                logger.info("CYCLE COMPLETE: Sent final response.")

                # Log agent response to audit log (only if non-empty)
                if final_text and final_text.strip():
                    audit_logger.info(
                        "Agent response to user",
                        extra={
                            'session_id': self.session_id,
                            'agent_response': final_text,
                            'response_type': 'final',
                            'event_type': 'AGENT_RESPONSE'
                        }
                    )

                # Check if response contains precedent citation (for audit logging)
                if self.precedent_used and ("precedent" in final_text.lower() or "exception" in final_text.lower()):
                    audit_logger.info(
                        "Agent cited precedent in response",
                        extra={
                            'session_id': self.session_id,
                            'response_excerpt': final_text[:200],
                            'decision_id': self.precedent_used.get('decision_id'),
                            'person_name': self.precedent_used.get('person_name'),
                            'event_type': 'PRECEDENT_CITED'
                        }
                    )

                return final_text

            # --- CONTINUE CONDITION: Claude wants to use tools ---
            elif response.stop_reason == "tool_use":

                # IMPORTANT: Add Claude's "Intent" to history so it remembers what it asked for
                self.messages.append({"role": "assistant", "content": response.content})

                # Extract and log any text blocks (agent thinking/reasoning)
                text_blocks = [block for block in response.content if block.type == "text"]
                if text_blocks:
                    thinking_text = "\n".join([block.text for block in text_blocks])
                    # Only log if there's actual content
                    if thinking_text and thinking_text.strip():
                        audit_logger.info(
                            "Agent reasoning/thinking",
                            extra={
                                'session_id': self.session_id,
                                'agent_response': thinking_text,
                                'response_type': 'thinking',
                                'event_type': 'AGENT_RESPONSE'
                            }
                        )

                tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
                tool_result_content = []

                for block in tool_use_blocks:
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    logger.info(f"DECISION: Agent called '{tool_name}' with input {tool_input}")

                    # Log tool call to audit log for complete trace
                    audit_logger.info(
                        f"Tool call: {tool_name}",
                        extra={
                            'session_id': self.session_id,
                            'tool_name': tool_name,
                            'tool_input': tool_input,
                            'event_type': 'TOOL_CALL'
                        }
                    )

                    # Execute the specific tool
                    result = None
                    if tool_name == "look_up_order":
                        result = EnterpriseServices.look_up_order(tool_input.get("order_id"))

                        # Log tool result
                        audit_logger.info(
                            f"Order lookup result for {tool_input.get('order_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'order_id': tool_input.get('order_id'),
                                'order_status': result.get('status') if result else None,
                                'items': result.get('items') if result else None,
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                    elif tool_name == "get_policy_info":
                        result = EnterpriseServices.get_policy_info(tool_input.get("policy_type"))

                        # Log tool result
                        audit_logger.info(
                            f"Policy lookup result for {tool_input.get('policy_type')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'policy_type': tool_input.get('policy_type'),
                                'policy_retrieved': bool(result),
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                    elif tool_name == "check_precedents":
                        result = EnterpriseServices.check_precedents(tool_input.get("query_tags_str"))

                        # Track precedent usage for audit logging
                        if result.get("found"):
                            self.precedent_used = result
                            audit_logger.info(
                                f"Agent using precedent: {result['decision_id']}",
                                extra={
                                    'session_id': self.session_id,
                                    'decision_id': result['decision_id'],
                                    'person_name': result['person_name'],
                                    'person_role': result['person_role'],
                                    'event_type': 'AGENT_USING_PRECEDENT'
                                }
                            )

                    elif tool_name == "execute_order_return":
                        result = EnterpriseServices.execute_refund(tool_input.get("order_id"), tool_input.get("reason"))

                        # Log tool result
                        audit_logger.info(
                            f"Return executed for order {tool_input.get('order_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'order_id': tool_input.get('order_id'),
                                'refund_status': result.get('status') if result else None,
                                'transaction_id': result.get('transaction_id') if result else None,
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                        # Record decision to audit ledger
                        decision_id = self.precedent_used.get('decision_id') if self.precedent_used else None
                        person_id = self.precedent_used.get('person_id') if self.precedent_used else None

                        EnterpriseServices.record_decision_to_ledger(
                            order_id=tool_input.get("order_id"),
                            agent_decision="APPROVE",
                            decision_id=decision_id,
                            person_id=person_id,
                            rationale=tool_input.get("reason")
                        )

                    elif tool_name == "escalate_to_human":
                        result = EnterpriseServices.escalate_to_human(tool_input.get("order_id"), tool_input.get("reason"))

                        # Log tool result
                        audit_logger.info(
                            f"Escalated to human for order {tool_input.get('order_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'order_id': tool_input.get('order_id'),
                                'escalation_reason': tool_input.get('reason'),
                                'ticket_id': result.get('ticket_id') if result else None,
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                        # Record escalation to audit ledger
                        EnterpriseServices.record_decision_to_ledger(
                            order_id=tool_input.get("order_id"),
                            agent_decision="ESCALATE",
                            rationale=tool_input.get("reason")
                        )

                    elif tool_name == "check_vip_status":
                        result = EnterpriseServices.check_vip_status(tool_input.get("customer_id"))

                        # Log tool result
                        audit_logger.info(
                            f"VIP status check for customer {tool_input.get('customer_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'customer_id': tool_input.get('customer_id'),
                                'is_vip': result.get('is_vip') if result else False,
                                'vip_tier': result.get('tier') if result else None,
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                    elif tool_name == "get_customer_info":
                        result = EnterpriseServices.get_customer_info(tool_input.get("customer_id"))

                        # Log tool result with proper null handling
                        audit_logger.info(
                            f"Customer info retrieved for {tool_input.get('customer_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'customer_id': tool_input.get('customer_id'),
                                'customer_name': result.get('customer_name', 'Unknown') if (result and result.get('found')) else 'Unknown',
                                'is_vip': result.get('is_vip', False) if (result and result.get('found')) else False,
                                'years_active': result.get('years_active', 0) if (result and result.get('found')) else 0,
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                    else:
                        logger.error(f"Unknown tool called: {tool_name}")
                        result = {"error": f"Tool '{tool_name}' not found."}

                    # Add result to the list of outputs
                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": json.dumps(result)
                    })

                # Add all tool outputs back to history as a User Message
                self.messages.append({"role": "user", "content": tool_result_content})
                
                # The loop now restarts automatically!
                # Claude will see the new history (Input + Tool Output) and decide the next step.









    # def run(self, user_input):
    #     logger.info(f"User Input {user_input}")
    #     self.messages.append({"role":"user", "content": user_input})

    #     # 1.    First call to Claude to determine Intent
    #     response = self.client.messages.create(
    #         model=Config.MODEL_NAME,
    #         max_tokens=Config.MAX_TOKENS,
    #         temperature=Config.TEMPERATURE,
    #         system=Config.SYSTEM_PROMPT,
    #         messages=self.messages,
    #         tools=tools_schema
    #     )

    #     # 1.5   for debugging, lets print out what response looks like
    #     # This converts the object to a pretty-printed string before passing to the logger
    #     logger.debug(
    #         "Full API Response:\n%s", 
    #         json.dumps(response.__dict__, indent=2, default=str)
    #     ) 

    #     # 2.    Add Assistant's response to history
    #     self.messages.append({"role": "assistant", "content": response.content})

    #     # 3.    Check if Claude wants to use tools
    #     tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

    #     if tool_use_blocks:
    #         tool_result_content = []

    #         for block in tool_use_blocks:
    #             tool_name = block.name
    #             tool_input = block.input
    #             tool_id = block.id

    #             logger.info(f"Decision: Agent Selected tool {tool_name} with input {tool_input}")

    #             result = None

    #             if tool_name == "look_up_order":
    #                 result = EnterpriseServices.look_up_order(tool_input.get("order_id"))
    #             elif tool_name == "get_policy_info":
    #                 result = EnterpriseServices.get_policy_info(tool_input.get("policy_type"))
    #             elif tool_name == "execute_order_return":
    #                 result = EnterpriseServices.execute_refund(tool_input.get("order_id"), tool_input.get("reason"))
    #             elif tool_name == "escalate_to_human":
    #                 result = EnterpriseServices.escalate_to_human(tool_input.get("order_id"), tool_input.get("reason"))
    #             else:
    #                 # Handle the "Hallucinated Tool" case safely
    #                 logger.error(f"Unknown tool called: {tool_name}")
    #                 result = {"error": f"Tool '{tool_name}' not found."}

    #             # Format Result for Anthropic
    #             tool_result_content.append({
    #                 "type": "tool_result",
    #                 "tool_use_id": tool_id,
    #                 "content": json.dumps(result)
    #             })

    #         # # 3.5   for debugging, lets print out what result looks like
    #         # # This converts the object to a pretty-printed string before passing to the logger
    #         # logger.debug(
    #         #     "Full Tool Result:\n%s", 
    #         #     json.dumps(result.__dict__, indent=2, default=str)
    #         # ) 

    #         # 4.    send tool results back to Claude
    #         self.messages.append({"role": "user", "content": tool_result_content})

    #         # 5.    Get Final result based on tool output
    #         final_response = self.client.messages.create(
    #             model=Config.MODEL_NAME,
    #             max_tokens=Config.MAX_TOKENS,
    #             temperature=Config.TEMPERATURE,
    #             system=Config.SYSTEM_PROMPT,
    #             messages=self.messages,
    #             tools=tools_schema
    #         )

    #         final_text = final_response.content[0].text
    #         self.messages.append({"role": "assistant", "content": final_text})
            
    #         logger.info("CYCLE COMPLETE: Sent final response to user.")
    #         return final_text

    #     else:
    #         # No tool used
    #         text_response = response.content[0].text
    #         logger.info("CYCLE COMPLETE: Sent text response (No tools).")
    #         return text_response