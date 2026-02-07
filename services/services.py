import logging
import random
import os
import kuzu
from datetime import datetime
from typing import Any

from logging_config import get_session_id
from data.data_loader import MOCK_ORDERS, MOCK_CUSTOMERS

# Get loggers (logging configured by logging_config.py)
logger = logging.getLogger("BackendServices")
audit_logger = logging.getLogger("DecisionAudit")

class EnterpriseServices:
    """
    Simulates Core Enterprise Integrations / API with 
    structured logging
    """

    # Initialize DB Connection (Lazy loading or global)
    # Ensure init_graph.py has been run first!
    # ---------------------------------------------------------
    # 1. Get directory of this file (.../services)
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # 2. Go up one level to project root (.../enterprise-cx-agent)
    BASE_DIR = os.path.dirname(CURRENT_DIR)
    # 3. Point to the data folder
    DB_PATH = os.path.join(BASE_DIR, "data", "context_graph_db")

    # Initialize connection
    if os.path.exists(DB_PATH):
        try:
            db = kuzu.Database(DB_PATH)
            conn = kuzu.Connection(db)
            print(f"✅ Connected to Kùzu Graph at: {DB_PATH}")
        except Exception as e:
            conn = None
            print(f"❌ Connection Failed: {e}")
    else:
        conn = None
        print(f"⚠️  WARNING: Graph DB not found at {DB_PATH}. Run scripts/init_graph.py")

    @staticmethod
    def look_up_order(order_id):
        logger.info(f"API CALL: Querying OMS for Order ID: {order_id}")

        # Use mock order database loaded from JSON file
        result = MOCK_ORDERS.get(order_id)
        if result:
            logger.info(f"API SUCCESS: Order found: {order_id} | Status: {result['status']}")
            return result
        else:
            logger.warning(f"API FAIL: Order lookup failed: {order_id}")
            return {"error": "Order ID not found in system."}

    @staticmethod
    def execute_refund(order_id, reason):
        logger.info(f"API CALL: Initiating Refund | Order: {order_id} | Reason: {reason}")
        
        # Simulate Transaction
        return {
            "status": "success", 
            "transaction_id": f"txn_{random.randint(10000,99999)}", 
            "message": "Refund processed to original payment method."
        }

    @staticmethod
    def escalate_to_human(order_id, reason):
        logger.critical(f"API CALL: ESCALATION TRIGGERED | Order: {order_id} | Reason: {reason}")
        return {"status": "escalated", "ticket_id": f"TKT-{random.randint(100,999)}", "message": "Agent requested human intervention."}

    @staticmethod
    def check_vip_status(customer_id):
        """
        Check if a customer has VIP or high-value status.
        Mock service that simulates CRM/customer database lookup.

        In production, this would integrate with:
        - CRM system (Salesforce, HubSpot, etc.)
        - Customer data warehouse
        - Loyalty program database

        Args:
            customer_id: Customer identifier

        Returns:
            dict with is_vip status and optional metadata
        """
        logger.info(f"API CALL: Checking VIP status for Customer ID: {customer_id}")

        # Use customer database loaded from JSON file
        customer_data = MOCK_CUSTOMERS.get(customer_id)

        if customer_data and customer_data.get("is_vip"):
            logger.info(f"API SUCCESS: Customer {customer_id} is VIP - Tier: {customer_data['tier']}")
            return {
                "is_vip": True,
                "customer_id": customer_id,
                "tier": customer_data.get("tier"),
                "lifetime_value": customer_data.get("lifetime_value"),
                "years_active": customer_data.get("years_active")
            }
        else:
            logger.info(f"API SUCCESS: Customer {customer_id} is NOT VIP (regular customer)")
            return {
                "is_vip": False,
                "customer_id": customer_id,
                "message": "Customer does not have VIP status"
            }

    @staticmethod
    def get_customer_info(customer_id):
        """
        Retrieve comprehensive customer information for greeting and personalization.
        Returns customer details including name, VIP status, tier, and tenure.

        This is used for:
        - Personalized greeting after order lookup
        - Displaying customer loyalty information
        - VIP acknowledgment

        Args:
            customer_id: Customer identifier

        Returns:
            dict with customer_name, is_vip, tier (if VIP), years_active, member_since
        """
        logger.info(f"API CALL: Fetching customer info for Customer ID: {customer_id}")

        # Use customer database loaded from JSON file
        customer_data = MOCK_CUSTOMERS.get(customer_id)

        if customer_data:
            logger.info(
                f"API SUCCESS: Customer info retrieved for {customer_id} - "
                f"{customer_data['customer_name']} ({'VIP' if customer_data['is_vip'] else 'Regular'})"
            )
            return {
                "found": True,
                "customer_id": customer_id,
                "customer_name": customer_data.get("customer_name"),
                "is_vip": customer_data.get("is_vip", False),
                "tier": customer_data.get("tier"),  # Only for VIP customers
                "years_active": customer_data.get("years_active"),
                "member_since": customer_data.get("member_since"),
                "lifetime_value": customer_data.get("lifetime_value")  # Only for VIP customers
            }
        else:
            logger.warning(f"API FAIL: Customer not found: {customer_id}")
            return {
                "found": False,
                "customer_id": customer_id,
                "error": "Customer not found in system"
            }

    @staticmethod
    def get_policy_info(policy_type):
        """
        Reads a markdown policy file from the /policies directory.
        """
        logger.info(f"POLICY CHECK: Retrieving '{policy_type}' policy document.")
        
        # Map simple names to filenames
        policy_map = {
            "returns": "policies/return_policy.md",
            "shipping": "policies/shipping_policy.md",
            "privacy": "policies/privacy_policy.md"
        }
        
        filename = policy_map.get(policy_type)
        
        if not filename or not os.path.exists(filename):
            return {"error": "Policy document not found."}
        
        try:
            with open(filename, 'r') as f:
                content = f.read()
            return {"policy_text": content}
        except Exception as e:
            return {"error": f"Failed to read policy: {str(e)}"}

    @staticmethod
    def check_precedents(query_tags_str):
        logger.info(f"PRECEDENT CHECK: Starting precedent lookup with query_tags_str: '{query_tags_str}'")

        # Log to audit system
        audit_logger.info(
            "Precedent query initiated",
            extra={
                'session_id': get_session_id(),
                'query_tags': query_tags_str.split(),
                'event_type': 'PRECEDENT_QUERY'
            }
        )

        if not EnterpriseServices.conn:
            logger.error("PRECEDENT CHECK: Graph DB connection not initialized.")
            return {"error": "Graph DB not initialized."}

        input_tags = [t.strip().lower() for t in query_tags_str.split()]
        logger.info(f"PRECEDENT CHECK: Parsed input tags: {input_tags}")

        # NEW QUERY: Traverse Person→Decision→Tag relationships with attribution
        query = f"""
        MATCH (p:Person)-[m:MADE]->(d:Decision)-[ctx:HAS_CONTEXT]->(t:Tag)
        WHERE t.name IN {input_tags}
          AND (d.expires_at = 'NEVER' OR d.expires_at > '{datetime.now().isoformat()}')
          AND d.confidence_score >= 0.7
        WITH p, d, SUM(ctx.relevance_score) AS score
        ORDER BY score DESC, p.authority_level DESC
        LIMIT 1
        RETURN
            d.id AS decision_id,
            d.title AS decision_title,
            d.outcome AS decision,
            d.reasoning AS rationale,
            d.conditions AS conditions,
            p.id AS person_id,
            p.name AS person_name,
            p.role AS person_role,
            p.authority_level AS authority,
            score,
            d.confidence_score AS confidence
        """
        logger.debug(f"PRECEDENT CHECK: Executing query: {query}")

        try:
            result = EnterpriseServices.conn.execute(query)
            logger.debug("PRECEDENT CHECK: Query executed successfully, checking for results...")

            if result.has_next():
                row = result.get_next()
                (decision_id, decision_title, decision, rationale, conditions,
                 person_id, person_name, person_role, authority,
                 score, confidence) = row

                logger.info(
                    f"PRECEDENT CHECK: ✅ Found matching precedent - ID: {decision_id} "
                    f"by {person_name} ({person_role}) | Score: {score}"
                )

                # Log match with full attribution to audit system
                audit_logger.info(
                    f"Precedent matched: {decision_title}",
                    extra={
                        'session_id': get_session_id(),
                        'decision_id': decision_id,
                        'person_id': person_id,
                        'person_name': person_name,
                        'person_role': person_role,
                        'match_score': score,
                        'confidence': confidence,
                        'event_type': 'PRECEDENT_MATCH'
                    }
                )

                return {
                    "found": True,
                    "decision_id": decision_id,
                    "decision_title": decision_title,
                    "decision": decision,
                    "rationale": rationale,
                    "conditions": conditions,
                    "person_id": person_id,
                    "person_name": person_name,
                    "person_role": person_role,
                    "authority_level": authority,
                    "match_score": score,
                    "confidence": confidence
                }
            else:
                logger.warning(f"PRECEDENT CHECK: No matching precedents found for tags: {input_tags}")

                audit_logger.info(
                    "No precedent found",
                    extra={
                        'session_id': get_session_id(),
                        'query_tags': input_tags,
                        'event_type': 'NO_PRECEDENT'
                    }
                )

                return {"found": False, "message": "No matching precedents found."}

        except Exception as e:
            logger.error(f"PRECEDENT CHECK: Graph query failed with error: {str(e)}", exc_info=True)
            return {"error": f"Graph Query Failed: {str(e)}"}

    @staticmethod
    def record_decision_to_ledger(
        order_id: str,
        agent_decision: str,
        decision_id: str | None = None,
        person_id: str | None = None,
        rationale: str | None = None
    ) -> dict:
        """
        Record agent's final decision to audit log.
        Links agent action to precedent if used.

        Args:
            order_id: Order being processed
            agent_decision: APPROVE/DENY/ESCALATE
            decision_id: Decision ID from graph (if precedent was used)
            person_id: Person ID who made the precedent decision
            rationale: Reason for the decision

        Returns:
            dict with status and session_id
        """

        log_entry = {
            'session_id': get_session_id(),
            'order_id': order_id,
            'agent_decision': agent_decision,
            'rationale': rationale,
            'event_type': 'AGENT_DECISION'
        }

        if decision_id:
            log_entry['decision_id'] = decision_id

        if person_id:
            log_entry['person_id'] = person_id

            # Fetch person details from graph
            if EnterpriseServices.conn:
                try:
                    person_result = EnterpriseServices.conn.execute(f"""
                        MATCH (p:Person {{id: '{person_id}'}})
                        RETURN p.name, p.role
                    """)

                    if person_result.has_next():
                        name, role = person_result.get_next()
                        log_entry['person_name'] = name
                        log_entry['person_role'] = role
                except Exception as e:
                    logger.warning(f"Could not fetch person details: {e}")

        audit_logger.info(
            f"Agent decision: {agent_decision}",
            extra=log_entry
        )

        return {
            "status": "logged",
            "session_id": log_entry['session_id']
        }

    @staticmethod
    def get_decision_attribution(decision_id: str) -> dict:
        """
        Retrieve full attribution chain for a decision.
        Returns Person info and Decision details for audit purposes.

        Args:
            decision_id: The decision ID to look up

        Returns:
            dict with person and decision details, or error
        """

        if not EnterpriseServices.conn:
            return {"error": "Graph DB not initialized."}

        query = f"""
        MATCH (p:Person)-[m:MADE]->(d:Decision {{id: '{decision_id}'}})
        OPTIONAL MATCH (d)-[:APPLIES_TO]->(prod:Product)
        OPTIONAL MATCH (d)-[:HAS_CONTEXT]->(t:Tag)
        RETURN
            p.id AS person_id,
            p.name AS person_name,
            p.role AS person_role,
            p.email AS person_email,
            d.id AS decision_id,
            d.title AS title,
            d.outcome AS outcome,
            d.reasoning AS reasoning,
            d.conditions AS conditions,
            d.source_ref AS source_file,
            d.created_at AS created_at,
            m.decision_timestamp AS timestamp,
            COLLECT(DISTINCT prod.category_name) AS products,
            COLLECT(DISTINCT t.name) AS tags
        """

        try:
            result = EnterpriseServices.conn.execute(query)

            if result.has_next():
                row = result.get_next()
                return {
                    "found": True,
                    "person": {
                        "id": row[0],
                        "name": row[1],
                        "role": row[2],
                        "email": row[3]
                    },
                    "decision": {
                        "id": row[4],
                        "title": row[5],
                        "outcome": row[6],
                        "reasoning": row[7],
                        "conditions": row[8],
                        "source_file": row[9],
                        "created_at": row[10],
                        "timestamp": row[11]
                    },
                    "products": row[12],
                    "tags": row[13]
                }
            else:
                return {"found": False, "message": "Decision not found"}

        except Exception as e:
            logger.error(f"Attribution query failed: {e}", exc_info=True)
            return {"error": str(e)}