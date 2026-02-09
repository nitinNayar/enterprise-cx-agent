import anthropic
import logging
import json
import uuid

from services.services import EnterpriseServices
from tools.tools import tools_schema
from config import Config
from logging_config import get_session_id, set_session_id
from prompts import get_prompt_for_category, get_tools_for_category

logger = logging.getLogger("Claude Agent")
audit_logger = logging.getLogger("DecisionAudit")

class SupportAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            max_retries=3,  # Retry failed requests up to 3 times
            timeout=60.0    # Increase timeout to 60 seconds
        )
        self.messages = [] # conversation history
        self.session_id = None  # Track session for audit logging
        self.precedent_used = None  # Track if precedent was used in this conversation
    

    def run(self, user_input, category=None):
        """
        Executes the main agent loop with optional category-specific optimization.

        Args:
            user_input: The user's message/question
            category: Optional QuestionCategory enum for specialized handling

        Handles:
        1. User Input -> Claude (with category-specific prompt and tools)
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

        # --- Category-Specific Configuration ---
        # Select system prompt and tools based on category (if provided)
        if category:
            system_prompt = get_prompt_for_category(category)
            allowed_tool_names = get_tools_for_category(category)

            # Filter tools based on category
            if allowed_tool_names:
                filtered_tools = [
                    tool for tool in tools_schema
                    if tool['name'] in allowed_tool_names
                ]
                logger.info(f"Using {len(filtered_tools)} tools for category {category.value}")
            else:
                filtered_tools = tools_schema  # Use all tools if no filtering
                logger.info(f"Using all {len(filtered_tools)} tools (no category filtering)")
        else:
            # No category provided, use default full configuration
            system_prompt = Config.SYSTEM_PROMPT
            filtered_tools = tools_schema
            logger.info("No category provided, using default configuration")

        # --- 2. The "Re-Act" Loop ---
        while True:

            # Call Claude with current history and category-specific configuration
            response = self.client.messages.create(
                model=Config.MODEL_NAME,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                system=system_prompt,  # <-- Category-specific prompt
                messages=self.messages,
                tools=filtered_tools  # <-- Category-specific tools
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

                    elif tool_name == "get_book_recommendations":
                        result = EnterpriseServices.get_book_recommendations(
                            customer_id=tool_input.get("customer_id"),
                            num_recommendations=tool_input.get("num_recommendations", 3),
                            context=tool_input.get("context")
                        )

                        audit_logger.info(
                            f"Book recommendations generated for customer {tool_input.get('customer_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'customer_id': tool_input.get('customer_id'),
                                'num_recommendations': len(result.get('recommendations', [])),
                                'event_type': 'TOOL_RESULT'
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

                    elif tool_name == "process_exchange":
                        result = EnterpriseServices.process_exchange(
                            original_order_id=tool_input.get("original_order_id"),
                            new_book_id=tool_input.get("new_book_id"),
                            new_book_title=tool_input.get("new_book_title"),
                            customer_id=tool_input.get("customer_id"),
                            return_reason=tool_input.get("return_reason")
                        )

                        # Log tool result with full exchange details
                        audit_logger.info(
                            f"Exchange processed: {tool_input.get('original_order_id')} → {result.get('new_order', {}).get('order_id')}",
                            extra={
                                'session_id': self.session_id,
                                'tool_name': tool_name,
                                'original_order_id': tool_input.get('original_order_id'),
                                'new_order_id': result.get('new_order', {}).get('order_id'),
                                'new_book_id': tool_input.get('new_book_id'),
                                'new_book_title': tool_input.get('new_book_title'),
                                'customer_id': tool_input.get('customer_id'),
                                'exchange_status': result.get('status'),
                                'return_txn_id': result.get('return_transaction', {}).get('transaction_id'),
                                'payment_txn_id': result.get('payment', {}).get('transaction_id'),
                                'price_difference': result.get('payment', {}).get('price_difference'),
                                'event_type': 'TOOL_RESULT'
                            }
                        )

                        # Record decision to audit ledger
                        decision_id = self.precedent_used.get('decision_id') if self.precedent_used else None
                        person_id = self.precedent_used.get('person_id') if self.precedent_used else None

                        EnterpriseServices.record_decision_to_ledger(
                            order_id=tool_input.get("original_order_id"),
                            agent_decision="EXCHANGE",
                            decision_id=decision_id,
                            person_id=person_id,
                            rationale=f"Exchange for {tool_input.get('new_book_title')}"
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
