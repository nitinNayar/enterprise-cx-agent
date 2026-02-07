from typing import Any
from pathlib import Path

"""
Centralized logging configuration for Decision Ledger feature.

Provides dual logging system:
1. Console logs - Human-readable text format for development
2. Audit logs - JSON structured format for monitoring tools

Usage:
    from logging_config import setup_logging, get_session_id, set_session_id

    # Initialize logging (call once at startup)
    audit_logger = setup_logging()

    # Set session ID for tracking
    set_session_id("SESSION-12345")

    # Log with decision attribution
    audit_logger.info(
        "Agent approved return",
        extra={
            'session_id': get_session_id(),
            'decision_id': 'DEC-2024-001',
            'person_name': 'Sarah Chen',
            'event_type': 'AGENT_DECISION'
        }
    )
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Logging directories
LOG_DIR: Path = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

AUDIT_LOG_FILE: Path = LOG_DIR / "decision_audit.log"
CONSOLE_LOG_FILE: Path = LOG_DIR / "console.log"


class DecisionAuditFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logs.
    Each log entry is a complete JSON object on one line (JSONL format).
    """

    def format(self, record: logging.LogRecord) -> str:
        # Base structure
        log_entry: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Add decision-specific fields if present
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id

        if hasattr(record, 'decision_id'):
            log_entry['decision_id'] = record.decision_id

        if hasattr(record, 'person_id'):
            log_entry['person_id'] = record.person_id

        if hasattr(record, 'person_name'):
            log_entry['person_name'] = record.person_name

        if hasattr(record, 'person_role'):
            log_entry['person_role'] = record.person_role

        if hasattr(record, 'precedent_id'):
            log_entry['precedent_id'] = record.precedent_id

        if hasattr(record, 'order_id'):
            log_entry['order_id'] = record.order_id

        if hasattr(record, 'agent_decision'):
            log_entry['agent_decision'] = record.agent_decision

        if hasattr(record, 'rationale'):
            log_entry['rationale'] = record.rationale

        if hasattr(record, 'confidence'):
            log_entry['confidence'] = record.confidence

        if hasattr(record, 'query_tags'):
            log_entry['query_tags'] = record.query_tags

        if hasattr(record, 'match_score'):
            log_entry['match_score'] = record.match_score

        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type

        if hasattr(record, 'response_excerpt'):
            log_entry['response_excerpt'] = record.response_excerpt

        # Tool call related fields
        if hasattr(record, 'tool_name'):
            log_entry['tool_name'] = record.tool_name

        if hasattr(record, 'tool_input'):
            log_entry['tool_input'] = record.tool_input

        if hasattr(record, 'order_status'):
            log_entry['order_status'] = record.order_status

        if hasattr(record, 'items'):
            log_entry['items'] = record.items

        if hasattr(record, 'policy_type'):
            log_entry['policy_type'] = record.policy_type

        if hasattr(record, 'policy_retrieved'):
            log_entry['policy_retrieved'] = record.policy_retrieved

        if hasattr(record, 'refund_status'):
            log_entry['refund_status'] = record.refund_status

        if hasattr(record, 'transaction_id'):
            log_entry['transaction_id'] = record.transaction_id

        if hasattr(record, 'escalation_reason'):
            log_entry['escalation_reason'] = record.escalation_reason

        if hasattr(record, 'ticket_id'):
            log_entry['ticket_id'] = record.ticket_id

        # VIP and customer related fields
        if hasattr(record, 'customer_id'):
            log_entry['customer_id'] = record.customer_id

        if hasattr(record, 'is_vip'):
            log_entry['is_vip'] = record.is_vip

        if hasattr(record, 'vip_tier'):
            log_entry['vip_tier'] = record.vip_tier

        if hasattr(record, 'customer_name'):
            log_entry['customer_name'] = record.customer_name

        if hasattr(record, 'years_active'):
            log_entry['years_active'] = record.years_active

        # Conversation related fields
        if hasattr(record, 'user_message'):
            log_entry['user_message'] = record.user_message

        if hasattr(record, 'agent_response'):
            log_entry['agent_response'] = record.agent_response

        if hasattr(record, 'response_type'):
            log_entry['response_type'] = record.response_type

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging():
    """
    Configure dual logging system:
    1. Console logs (human-readable)
    2. File console log (debug output)
    3. Audit logs (JSON structured, for monitoring tools)

    Returns:
        logging.Logger: DecisionAudit logger for decision attribution logging
    """

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # ========================================
    # HANDLER 1: Console (Human-Readable)
    # ========================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) 
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ========================================
    # HANDLER 2: File Console Log (Debugging)
    # ========================================
    file_handler = RotatingFileHandler(
        CONSOLE_LOG_FILE,
        maxBytes=10_000_000,  # 10MB per file
        backupCount=5,        # Keep 5 old files
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(console_formatter)
    root_logger.addHandler(file_handler)

    # ========================================
    # HANDLER 3: Audit Log (JSON Structured)
    # ========================================
    audit_handler = RotatingFileHandler(
        AUDIT_LOG_FILE,
        maxBytes=10_000_000,  # 10MB per file
        backupCount=50,       # Keep 50 old files = 500MB history
        encoding='utf-8'
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(DecisionAuditFormatter())

    # Only attach to decision-related loggers
    decision_logger = logging.getLogger("DecisionAudit")
    decision_logger.addHandler(audit_handler)
    decision_logger.setLevel(logging.INFO)
    decision_logger.propagate = False  # Don't send to root logger

    print(f"✅ Logging configured:")
    print(f"   - Console: stdout + {CONSOLE_LOG_FILE}")
    print(f"   - Audit: {AUDIT_LOG_FILE}")

    return decision_logger


# Session tracking
_current_session_id = None


def set_session_id(session_id: str):
    """Set current session for all subsequent logs."""
    global _current_session_id
    _current_session_id = session_id


def get_session_id() -> str:
    """Get current session ID."""
    global _current_session_id
    if _current_session_id is None:
        _current_session_id = f"SESSION-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    return _current_session_id
