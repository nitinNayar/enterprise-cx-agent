"""
Decision Reviewer Module

Provides admin functionality for reviewing agent decision traces,
including audit log retrieval, event parsing, and trace formatting.
"""

import chainlit as cl
import json
from pathlib import Path
from logging_config import setup_logging
from services.services import EnterpriseServices

# Initialize audit logger
audit_logger = setup_logging()


async def handle_admin_query(session_id_input: str):
    """
    Parse session ID, retrieve events from audit log, enrich with graph data,
    and display formatted trace.

    Args:
        session_id_input: User input (should be SESSION-xxxxxxxx format)
    """
    # 1. Validate session ID format
    session_id = session_id_input.strip()

    if not session_id.startswith("SESSION-") and not session_id.startswith("TEST-"):
        await cl.Message(
            content=f"❌ **Invalid Format**\n\nExpected format: `SESSION-xxxxxxxx` or `TEST-SESSION-xxx`\n\nYou entered: `{session_id}`"
        ).send()
        return

    # 2. Query audit log
    msg = cl.Message(content="🔍 Searching audit logs...")
    await msg.send()

    events = get_session_events(session_id)

    if not events:
        msg.content = f"❌ **No Events Found**\n\nNo decision trace exists for session: `{session_id}`\n\n**Possible reasons:**\n- Session ID doesn't exist\n- No decisions were made in this session\n- Audit log was cleared\n\nTry another session ID."
        await msg.update()
        return

    # 3. Build decision trace display
    msg.content = format_decision_trace(session_id, events)
    await msg.update()


def get_session_events(session_id: str) -> list:
    """
    Read audit log and filter events by session_id.

    Returns:
        List of event dictionaries, ordered chronologically
    """
    log_file = Path(__file__).parent.parent / "logs" / "decision_audit.log"

    if not log_file.exists():
        return []

    events = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    if event.get('session_id') == session_id:
                        events.append(event)
                except json.JSONDecodeError:
                    continue  # Skip malformed lines
    except Exception as e:
        audit_logger.error(f"Error reading audit log: {e}")
        return []

    return events


def format_decision_trace(session_id: str, events: list) -> str:
    """
    Format events into readable markdown display.
    Enrich with graph database attribution where available.

    Args:
        session_id: The session being investigated
        events: List of audit log events

    Returns:
        Markdown-formatted string for display
    """
    # Use HTML with inline styles for proper dark mode visibility
    output = f'<h1 style="color: #f9fafb; margin-bottom: 1rem;">Decision Trace: <code>{session_id}</code></h1>\n\n'

    # Deduplicate consecutive identical events
    deduplicated_events = []
    prev_event = None

    for event in events:
        event_type = event.get('event_type', 'UNKNOWN')

        # Skip empty conversation events
        if event_type == "USER_MESSAGE":
            user_message = event.get('user_message', '')
            if not user_message or not user_message.strip():
                continue
        elif event_type == "AGENT_RESPONSE":
            agent_response = event.get('agent_response', '')
            if not agent_response or not agent_response.strip():
                continue

        # Check if this is a duplicate of the previous event
        is_duplicate = False
        if prev_event:
            # Same event type
            if event_type == prev_event.get('event_type'):
                # Check specific fields based on event type
                if event_type == "TOOL_CALL":
                    if (event.get('tool_name') == prev_event.get('tool_name') and
                        json.dumps(event.get('tool_input', {})) == json.dumps(prev_event.get('tool_input', {}))):
                        is_duplicate = True
                elif event_type == "TOOL_RESULT":
                    # For tool results, check tool_name and relevant ID field
                    tool_name = event.get('tool_name')
                    prev_tool_name = prev_event.get('tool_name')

                    if tool_name == prev_tool_name:
                        # Different tools have different identifying fields
                        if tool_name in ["look_up_order", "execute_order_return", "escalate_to_human"]:
                            # These tools use order_id
                            if event.get('order_id') == prev_event.get('order_id'):
                                is_duplicate = True
                        elif tool_name in ["check_vip_status", "get_customer_info"]:
                            # These tools use customer_id
                            if event.get('customer_id') == prev_event.get('customer_id'):
                                is_duplicate = True
                        elif tool_name == "get_policy_info":
                            # This tool uses policy_type
                            if event.get('policy_type') == prev_event.get('policy_type'):
                                is_duplicate = True
                        else:
                            # Generic fallback - mark as duplicate if same tool_name
                            is_duplicate = True
                elif event_type == "USER_MESSAGE":
                    if event.get('user_message') == prev_event.get('user_message'):
                        is_duplicate = True
                elif event_type == "AGENT_RESPONSE":
                    if event.get('agent_response') == prev_event.get('agent_response'):
                        is_duplicate = True
                elif event_type == "PRECEDENT_QUERY":
                    if event.get('query_tags') == prev_event.get('query_tags'):
                        is_duplicate = True
                elif event_type == "PRECEDENT_MATCH":
                    if event.get('decision_id') == prev_event.get('decision_id'):
                        is_duplicate = True
                elif event_type == "AGENT_USING_PRECEDENT":
                    if event.get('decision_id') == prev_event.get('decision_id'):
                        is_duplicate = True
                elif event_type == "AGENT_DECISION":
                    if (event.get('order_id') == prev_event.get('order_id') and
                        event.get('agent_decision') == prev_event.get('agent_decision')):
                        is_duplicate = True
                elif event_type == "PRECEDENT_CITED":
                    if (event.get('decision_id') == prev_event.get('decision_id') and
                        event.get('response_excerpt') == prev_event.get('response_excerpt')):
                        is_duplicate = True

        if not is_duplicate:
            deduplicated_events.append(event)
            prev_event = event
        else:
            # If it's a duplicate TOOL_RESULT, replace the previous entry with this one
            # (later entries have more complete data after formatter was updated)
            if event_type == "TOOL_RESULT" and deduplicated_events:
                # Replace the last entry if it was the same tool
                if deduplicated_events[-1].get('event_type') == 'TOOL_RESULT' and \
                   deduplicated_events[-1].get('tool_name') == event.get('tool_name'):
                    deduplicated_events[-1] = event
                    prev_event = event

    # Display total count (after deduplication)
    output += f"**Total Events:** {len(deduplicated_events)}\n\n"
    output += "---\n\n"

    # Group events by type for better organization
    event_num = 0
    for event in deduplicated_events:
        event_type = event.get('event_type', 'UNKNOWN')
        timestamp = event.get('timestamp', '')
        message = event.get('message', '')

        # Increment event number only for events we're displaying
        event_num += 1

        # Use HTML with inline styles to ensure proper color in dark mode
        output += f'<h2 style="color: #f9fafb; margin-top: 1.5rem; margin-bottom: 0.5rem;">Event {event_num}: {event_type}</h2>\n\n'
        output += f"**Time:** {timestamp}\n"
        output += f"**Message:** {message}\n\n"

        # Display event-specific details
        if event_type == "USER_MESSAGE":
            user_message = event.get('user_message', '')
            output += f"**User said:**\n> {user_message}\n\n"

        elif event_type == "AGENT_RESPONSE":
            agent_response = event.get('agent_response', '')
            response_type = event.get('response_type', 'unknown')

            if response_type == 'thinking':
                output += f"**Agent thinking:**\n> {agent_response[:300]}{'...' if len(agent_response) > 300 else ''}\n\n"
            elif response_type == 'final':
                output += f"**Agent replied:**\n> {agent_response[:300]}{'...' if len(agent_response) > 300 else ''}\n\n"
            else:
                output += f"**Agent response:**\n> {agent_response[:300]}{'...' if len(agent_response) > 300 else ''}\n\n"

        elif event_type == "TOOL_CALL":
            tool_name = event.get('tool_name', 'unknown')
            tool_input = event.get('tool_input', {})
            output += f"**Tool:** `{tool_name}`\n"
            output += f"**Input:** {json.dumps(tool_input, indent=2)}\n\n"

        elif event_type == "TOOL_RESULT":
            tool_name = event.get('tool_name', 'unknown')
            output += f"**Tool:** `{tool_name}`\n"

            if tool_name == "look_up_order":
                order_id = event.get('order_id')
                order_status = event.get('order_status')
                items = event.get('items', [])
                output += f"**Order ID:** {order_id}\n"
                output += f"**Status:** {order_status}\n"
                if items:
                    output += f"**Items:** {', '.join(items)}\n\n"
                else:
                    output += "**Items:** None\n\n"

            elif tool_name == "get_policy_info":
                policy_type = event.get('policy_type')
                policy_retrieved = event.get('policy_retrieved')
                output += f"**Policy Type:** {policy_type}\n"
                output += f"**Retrieved:** {'✅ Yes' if policy_retrieved else '❌ No'}\n\n"

            elif tool_name == "execute_order_return":
                order_id = event.get('order_id')
                refund_status = event.get('refund_status')
                transaction_id = event.get('transaction_id')
                output += f"**Order ID:** {order_id}\n"
                output += f"**Status:** {refund_status}\n"
                output += f"**Transaction ID:** {transaction_id}\n\n"

            elif tool_name == "escalate_to_human":
                order_id = event.get('order_id')
                escalation_reason = event.get('escalation_reason')
                ticket_id = event.get('ticket_id')
                output += f"**Order ID:** {order_id}\n"
                output += f"**Reason:** {escalation_reason}\n"
                output += f"**Ticket ID:** {ticket_id}\n\n"

            elif tool_name == "check_vip_status":
                customer_id = event.get('customer_id')
                is_vip = event.get('is_vip', False)
                vip_tier = event.get('vip_tier')
                output += f"**Customer ID:** {customer_id}\n"
                if is_vip:
                    output += f"**VIP Status:** ✅ Yes ({vip_tier} tier)\n\n"
                else:
                    output += f"**VIP Status:** ❌ No (Regular customer)\n\n"

            elif tool_name == "get_customer_info":
                customer_id = event.get('customer_id', 'Unknown')
                customer_name = event.get('customer_name', 'Unknown')
                is_vip = event.get('is_vip', False)
                years_active = event.get('years_active', 0)

                # Display customer info
                if customer_name != 'Unknown' and customer_id != 'Unknown':
                    output += f"**Customer:** {customer_name} (`{customer_id}`)\n"
                else:
                    output += f"**Customer ID:** {customer_id}\n"
                    output += f"**Name:** {customer_name}\n"

                # VIP Status
                if is_vip:
                    output += f"**VIP Status:** ✅ Yes\n"
                else:
                    output += f"**VIP Status:** ❌ No\n"

                # Format tenure display
                if years_active and years_active >= 1:
                    output += f"**Tenure:** {years_active:.1f} years\n\n"
                elif years_active and years_active > 0:
                    months = int(years_active * 12)
                    output += f"**Tenure:** {months} months\n\n"
                else:
                    output += f"**Tenure:** Not available\n\n"

            else:
                output += "**Result:** Completed\n\n"

        elif event_type == "PRECEDENT_QUERY":
            tags = event.get('query_tags', [])
            output += f"**Query Tags:** {', '.join(tags)}\n\n"

        elif event_type == "PRECEDENT_MATCH":
            decision_id = event.get('decision_id')
            person_name = event.get('person_name')
            person_role = event.get('person_role')
            match_score = event.get('match_score')
            confidence = event.get('confidence')

            output += f"**Decision ID:** `{decision_id}`\n"
            output += f"**Person:** {person_name} ({person_role})\n"
            output += f"**Match Score:** {match_score}\n"
            output += f"**Confidence:** {confidence}\n\n"

            # Enrich with graph attribution data
            if decision_id:
                attribution = EnterpriseServices.get_decision_attribution(decision_id)
                if attribution.get('found'):
                    output += "**📋 Full Decision Details:**\n"
                    decision = attribution['decision']
                    person = attribution['person']
                    output += f"- **Title:** {decision.get('title')}\n"
                    output += f"- **Outcome:** {decision.get('outcome')}\n"
                    reasoning = decision.get('reasoning', '')
                    if len(reasoning) > 200:
                        output += f"- **Reasoning:** {reasoning[:200]}...\n"
                    else:
                        output += f"- **Reasoning:** {reasoning}\n"
                    conditions = decision.get('conditions', '')
                    if len(conditions) > 200:
                        output += f"- **Conditions:** {conditions[:200]}...\n"
                    else:
                        output += f"- **Conditions:** {conditions}\n"
                    output += f"- **Source File:** {decision.get('source_file')}\n"
                    output += f"- **Created:** {decision.get('created_at')}\n"
                    output += f"- **Decision Maker:** {person.get('name')} ({person.get('email')})\n"
                    products = attribution.get('products', [])
                    if products:
                        output += f"- **Products:** {', '.join(products)}\n"
                    tags_list = attribution.get('tags', [])
                    if tags_list:
                        output += f"- **Tags:** {', '.join(tags_list)}\n"
                    output += "\n"

        elif event_type == "NO_PRECEDENT":
            tags = event.get('query_tags', [])
            output += f"**Searched Tags:** {', '.join(tags)}\n"
            output += f"**Result:** No matching precedent found in graph\n\n"

        elif event_type == "AGENT_USING_PRECEDENT":
            decision_id = event.get('decision_id')
            person_name = event.get('person_name')
            person_role = event.get('person_role')
            output += f"**Using Decision:** `{decision_id}`\n"
            output += f"**Authority:** {person_name} ({person_role})\n\n"

        elif event_type == "AGENT_DECISION":
            order_id = event.get('order_id')
            decision = event.get('agent_decision')
            rationale = event.get('rationale')
            decision_id = event.get('decision_id')
            person_name = event.get('person_name')

            output += f"**Order:** `{order_id}`\n"
            output += f"**Decision:** {decision}\n"
            output += f"**Rationale:** {rationale}\n"
            if decision_id:
                output += f"**Based on Precedent:** `{decision_id}` by {person_name}\n"
            output += "\n"

        elif event_type == "PRECEDENT_CITED":
            decision_id = event.get('decision_id')
            person_name = event.get('person_name')
            excerpt = event.get('response_excerpt', '')
            output += f"**Precedent Cited:** `{decision_id}` by {person_name}\n"
            output += f"**Response Excerpt:**\n> {excerpt}\n\n"

        output += "---\n\n"

    output += f"\n**End of trace for `{session_id}`**\n\n"
    output += "Enter another session ID to investigate:"

    return output
