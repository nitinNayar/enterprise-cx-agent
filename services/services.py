import logging
import random
import os
import re
import kuzu
from datetime import datetime
from typing import Any

from logging_config import get_session_id
from data.data_loader import MOCK_ORDERS, MOCK_CUSTOMERS, MOCK_BOOKS

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
    def _normalize_order_id(order_id: str) -> str:
        """
        Normalize order ID to canonical format for robust lookup.

        Handles common user input variations:
        - Case insensitive: "ord-123" → "ORD-123"
        - Delimiter flexible: "ORD_123" / "ORD:123" / "ORD 123" → "ORD-123"
        - No delimiter: "ORD123" → "ORD-123"
        - Whitespace tolerant: " ORD-123 " → "ORD-123"
        - Internal spaces: "ord 123" → "ORD-123"

        Args:
            order_id: Raw order ID from user input

        Returns:
            Normalized order ID in format "ORD-XXX"
        """
        if not order_id:
            return order_id

        # Strip leading/trailing whitespace and convert to uppercase
        normalized = order_id.strip().upper()

        # Replace various delimiters with hyphens
        # Handle: underscores, spaces, colons, dots, etc.
        normalized = normalized.replace('_', '-')
        normalized = normalized.replace(' ', '-')
        normalized = normalized.replace(':', '-')
        normalized = normalized.replace('.', '-')

        # Clean up multiple consecutive hyphens (e.g., "ORD--123" → "ORD-123")
        while '--' in normalized:
            normalized = normalized.replace('--', '-')

        # Handle no-delimiter case: insert hyphen between letters and digits
        # e.g., "ORD123" → "ORD-123"
        # Use regex to find letter-to-digit boundary and insert hyphen
        normalized = re.sub(r'([A-Z]+)(\d+)', r'\1-\2', normalized)

        return normalized

    @staticmethod
    def look_up_order(order_id):
        original_input = order_id

        # Normalize order ID for robust lookup
        order_id = EnterpriseServices._normalize_order_id(order_id)

        logger.info(f"API CALL: Querying OMS for Order ID: {order_id} (original input: {original_input})")

        # Use mock order database loaded from JSON file
        result = MOCK_ORDERS.get(order_id)
        if result:
            logger.info(f"API SUCCESS: Order found: {order_id} | Status: {result['status']}")

            # Filter out internal fields that agent shouldn't see
            # Notes are for testing/documentation only - agent must ASK about condition
            filtered_result = {k: v for k, v in result.items() if k != "notes"}
            return filtered_result
        else:
            logger.warning(f"API FAIL: Order lookup failed: {order_id} (original: {original_input})")
            return {"error": "Order ID not found in system."}

    @staticmethod
    def execute_refund(order_id, reason):
        original_input = order_id

        # Normalize order ID for robust processing
        order_id = EnterpriseServices._normalize_order_id(order_id)

        logger.info(f"API CALL: Initiating Refund | Order: {order_id} (original input: {original_input}) | Reason: {reason}")

        # Simulate Transaction
        return {
            "status": "success",
            "transaction_id": f"txn_{random.randint(10000,99999)}",
            "message": "Refund processed to original payment method."
        }

    @staticmethod
    def escalate_to_human(order_id, reason):
        original_input = order_id

        # Normalize order ID for robust processing
        order_id = EnterpriseServices._normalize_order_id(order_id)

        logger.critical(f"API CALL: ESCALATION TRIGGERED | Order: {order_id} (original input: {original_input}) | Reason: {reason}")
        return {"status": "escalated", "ticket_id": f"TKT-{random.randint(100,999)}", "message": "Agent requested human intervention."}

    @staticmethod
    def escalate_order_issue(order_id, reason, policy_check_confirmation):
        """
        Escalate an order-related issue to the Order Support team.
        Routes to high-priority queue with full order context.

        In production, this would:
        - Create ticket in Order Support queue (Zendesk, Intercom, etc.)
        - Include full order details from look_up_order(order_id)
        - Set SLA to 2-4 hours based on issue severity
        - Notify Order Support team via Slack/email
        - Attach customer profile and order history
        """
        ticket_id = f"TICKET-ORDER-{random.randint(1000,9999)}"

        logger.critical(f"API CALL: ORDER ESCALATION | Order: {order_id} | Ticket: {ticket_id} | Reason: {reason}")

        return {
            "status": "escalated",
            "ticket_id": ticket_id,
            "queue": "order_support",
            "sla_hours": 4,
            "order_id": order_id,
            "message": f"Your request has been escalated to our Order Support team. Reference: {ticket_id}. A specialist will contact you within 2-4 hours."
        }

    @staticmethod
    def escalate_general_question(reason, question_category, customer_email=None):
        """
        Escalate a general question to the General Support team.
        Routes to standard queue without requiring order context.

        In production, this would:
        - Create ticket in General Support queue
        - Route based on question_category to specialized team
        - Set SLA to 24 hours
        - Send confirmation email if customer_email provided
        - Tag with category for analytics
        """
        ticket_id = f"TICKET-GEN-{random.randint(1000,9999)}"

        logger.critical(f"API CALL: GENERAL ESCALATION | Category: {question_category} | Ticket: {ticket_id} | Reason: {reason}")

        return {
            "status": "escalated",
            "ticket_id": ticket_id,
            "queue": "general_support",
            "sla_hours": 24,
            "category": question_category,
            "message": f"Your question has been escalated to our support team. Reference: {ticket_id}. You'll receive a response within 24 hours" + (f" at {customer_email}" if customer_email else "") + "."
        }

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
        Returns customer details including name, VIP status, tier, tenure, AND reading preferences.

        This is used for:
        - Personalized greeting after order lookup
        - Displaying customer loyalty information
        - VIP acknowledgment
        - Crafting personalized recommendation offers (genres/authors)

        Args:
            customer_id: Customer identifier

        Returns:
            dict with customer_name, is_vip, tier, years_active, reading_preferences, purchase_summary
        """
        logger.info(f"API CALL: Fetching customer info for Customer ID: {customer_id}")

        # Use customer database loaded from JSON file
        customer_data = MOCK_CUSTOMERS.get(customer_id)

        if customer_data:
            logger.info(
                f"API SUCCESS: Customer info retrieved for {customer_id} - "
                f"{customer_data['customer_name']} ({'VIP' if customer_data['is_vip'] else 'Regular'})"
            )

            # Extract reading preferences if available
            reading_prefs = customer_data.get("reading_preferences", {})
            purchase_history = customer_data.get("purchase_history", [])

            # Create purchase summary (top authors and highly-rated books)
            top_authors = []
            highly_rated_books = []

            if purchase_history:
                # Get authors from purchases
                author_counts = {}
                for book in purchase_history:
                    author = book.get("author")
                    if author:
                        author_counts[author] = author_counts.get(author, 0) + 1

                # Top 3 authors by purchase count
                top_authors = sorted(author_counts.keys(), key=lambda a: author_counts[a], reverse=True)[:3]

                # Books rated 4 or 5 stars
                highly_rated_books = [
                    {
                        "title": book.get("title"),
                        "author": book.get("author"),
                        "rating": book.get("rating")
                    }
                    for book in purchase_history
                    if (book.get("rating") or 0) >= 4
                ][:3]  # Top 3 highly-rated

            return {
                "found": True,
                "customer_id": customer_id,
                "customer_name": customer_data.get("customer_name"),
                "is_vip": customer_data.get("is_vip", False),
                "tier": customer_data.get("tier"),
                "years_active": customer_data.get("years_active"),
                "member_since": customer_data.get("member_since"),
                "lifetime_value": customer_data.get("lifetime_value"),

                # NEW: Reading preferences for personalization
                "reading_preferences": {
                    "favorite_genres": reading_prefs.get("favorite_genres", []),
                    "favorite_authors": reading_prefs.get("favorite_authors", []),
                    "preferred_formats": reading_prefs.get("preferred_formats", [])
                },

                # NEW: Purchase summary for personalization
                "purchase_summary": {
                    "top_authors": top_authors,
                    "highly_rated_books": highly_rated_books
                }
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

    @staticmethod
    def get_book_recommendations(customer_id: str, num_recommendations: int = 3, context: str | None = None) -> dict:
        """
        Generate personalized book recommendations for a customer using rule-based algorithm.

        Recommendation algorithm (3 prioritized rules):
        1. Books by same authors customer rated 4+ stars (strongest signal)
        2. Top-rated books in customer's favorite genres (not yet purchased)
        3. Popular books in similar genres (trending)

        Applies tier-based discounts:
        - Silver: 10%
        - Gold: 15%
        - Platinum: 25%
        - Regular: 0%

        Args:
            customer_id: Customer identifier
            num_recommendations: Number of recommendations to return (default: 3)
            context: Optional context about what they're returning (e.g., 'thriller', 'sci-fi')

        Returns:
            dict with recommendations list, customer info, and discount percentage
        """
        logger.info(f"RECOMMENDATION ENGINE: Generating recommendations for customer {customer_id}")

        # Load customer profile
        customer_data = MOCK_CUSTOMERS.get(customer_id)

        if not customer_data:
            logger.warning(f"RECOMMENDATION ENGINE: Customer {customer_id} not found")
            return {
                "status": "error",
                "error": "Customer not found"
            }

        customer_name = customer_data.get("customer_name", "Customer")
        is_vip = customer_data.get("is_vip", False)
        tier = customer_data.get("tier") if is_vip else "Regular"

        # Determine discount percentage based on tier
        discount_map = {
            "Silver": 10,
            "Gold": 15,
            "Platinum": 25,
            "Regular": 0
        }
        discount_percentage = discount_map.get(tier, 0)

        logger.info(f"RECOMMENDATION ENGINE: Customer {customer_name} - Tier: {tier}, Discount: {discount_percentage}%")

        # Get purchased titles to exclude
        purchase_history = customer_data.get("purchase_history", [])
        purchased_titles = {book.get("title", "").lower() for book in purchase_history}

        logger.info(f"RECOMMENDATION ENGINE: Customer has purchased {len(purchased_titles)} books")

        # Initialize recommendations list
        recommendations = []

        # RULE 1: Books by same authors customer rated 4+ stars
        liked_authors = [
            book.get("author")
            for book in purchase_history
            if (book.get("rating") or 0) >= 4 and book.get("author")
        ]

        if liked_authors:
            logger.info(f"RECOMMENDATION ENGINE: Rule 1 - Searching for books by liked authors: {liked_authors}")
            same_author_books = EnterpriseServices._find_books_by_authors(liked_authors, purchased_titles)
            recommendations.extend(same_author_books[:2])  # Top 2
            logger.info(f"RECOMMENDATION ENGINE: Rule 1 found {len(same_author_books)} books, added top 2")

        # RULE 2: Top-rated books in favorite genres
        reading_preferences = customer_data.get("reading_preferences", {})
        favorite_genres = reading_preferences.get("favorite_genres", [])

        if favorite_genres:
            logger.info(f"RECOMMENDATION ENGINE: Rule 2 - Searching in favorite genres: {favorite_genres}")
            genre_books = EnterpriseServices._find_top_rated_in_genres(favorite_genres, purchased_titles)
            recommendations.extend(genre_books[:2])  # Top 2
            logger.info(f"RECOMMENDATION ENGINE: Rule 2 found {len(genre_books)} books, added top 2")

        # RULE 3: Popular books in similar genres
        if favorite_genres:
            logger.info(f"RECOMMENDATION ENGINE: Rule 3 - Searching popular books in similar genres")
            popular_books = EnterpriseServices._find_popular_in_similar_genres(favorite_genres, purchased_titles)
            recommendations.extend(popular_books[:1])  # Top 1
            logger.info(f"RECOMMENDATION ENGINE: Rule 3 found {len(popular_books)} books, added top 1")

        # Deduplicate and limit to requested number
        unique_recommendations = EnterpriseServices._unique_books(recommendations)
        final_recommendations = unique_recommendations[:num_recommendations]

        logger.info(f"RECOMMENDATION ENGINE: Returning {len(final_recommendations)} unique recommendations")

        # Format recommendations with pricing
        formatted_recommendations = []
        for rec in final_recommendations:
            book_data = rec["book_data"]
            original_price = book_data.get("price", 0.0)
            discounted_price = original_price * (1 - discount_percentage / 100)
            savings = original_price - discounted_price

            formatted_recommendations.append({
                "book_id": rec["book_id"],
                "title": book_data.get("title"),
                "author": book_data.get("author"),
                "genre": book_data.get("genre"),
                "price": original_price,
                "discounted_price": round(discounted_price, 2),
                "savings": round(savings, 2),
                "format": book_data.get("formats", ["Hardcover"])[0],  # Default to first format
                "rating": book_data.get("rating"),
                "reason_code": rec["reason_code"],
                "match_data": rec.get("match_data", {})
            })

        audit_logger.info(
            f"Recommendations generated for {customer_id}",
            extra={
                'session_id': get_session_id(),
                'customer_id': customer_id,
                'customer_tier': tier,
                'discount_percentage': discount_percentage,
                'num_recommendations': len(formatted_recommendations),
                'event_type': 'RECOMMENDATIONS_GENERATED'
            }
        )

        return {
            "status": "success",
            "customer_name": customer_name,
            "customer_tier": tier,
            "discount_percentage": discount_percentage,
            "recommendations": formatted_recommendations
        }

    @staticmethod
    def _find_books_by_authors(authors: list[str], exclude_titles: set[str]) -> list[dict]:
        """
        Find books by specified authors, excluding already purchased titles.

        Args:
            authors: List of author names
            exclude_titles: Set of book titles (lowercase) to exclude

        Returns:
            List of dicts with book_id, book_data, reason_code, and match_data
        """
        results = []

        for book_id, book_data in MOCK_BOOKS.items():
            book_author = book_data.get("author", "")
            book_title = book_data.get("title", "").lower()

            # Check if book is by one of the liked authors and not already purchased
            if book_author in authors and book_title not in exclude_titles:
                results.append({
                    "book_id": book_id,
                    "book_data": book_data,
                    "reason_code": "same_author",
                    "match_data": {
                        "matched_author": book_author
                    }
                })

        # Sort by rating (highest first)
        results.sort(key=lambda x: x["book_data"].get("rating", 0), reverse=True)

        return results

    @staticmethod
    def _find_top_rated_in_genres(genres: list[str], exclude_titles: set[str]) -> list[dict]:
        """
        Find top-rated books in specified genres, excluding already purchased titles.

        Args:
            genres: List of genre names
            exclude_titles: Set of book titles (lowercase) to exclude

        Returns:
            List of dicts with book_id, book_data, reason_code, and match_data
        """
        results = []

        for book_id, book_data in MOCK_BOOKS.items():
            book_genre = book_data.get("genre", "")
            book_title = book_data.get("title", "").lower()
            book_tags = book_data.get("tags", [])

            # Check if book matches any of the favorite genres
            # Match on exact genre or if genre appears in tags
            genre_match = None
            for genre in genres:
                if genre.lower() in book_genre.lower() or any(genre.lower() in tag.lower() for tag in book_tags):
                    genre_match = genre
                    break

            if genre_match and book_title not in exclude_titles:
                results.append({
                    "book_id": book_id,
                    "book_data": book_data,
                    "reason_code": "favorite_genre",
                    "match_data": {
                        "matched_genre": genre_match
                    }
                })

        # Sort by rating (highest first)
        results.sort(key=lambda x: x["book_data"].get("rating", 0), reverse=True)

        return results

    @staticmethod
    def _find_popular_in_similar_genres(genres: list[str], exclude_titles: set[str]) -> list[dict]:
        """
        Find popular books in similar genres based on popularity score.

        Args:
            genres: List of genre names
            exclude_titles: Set of book titles (lowercase) to exclude

        Returns:
            List of dicts with book_id, book_data, reason_code, and match_data
        """
        results = []

        for book_id, book_data in MOCK_BOOKS.items():
            book_genre = book_data.get("genre", "")
            book_title = book_data.get("title", "").lower()
            book_tags = book_data.get("tags", [])

            # Check if book matches any of the favorite genres
            genre_match = None
            for genre in genres:
                if genre.lower() in book_genre.lower() or any(genre.lower() in tag.lower() for tag in book_tags):
                    genre_match = genre
                    break

            if genre_match and book_title not in exclude_titles:
                results.append({
                    "book_id": book_id,
                    "book_data": book_data,
                    "reason_code": "trending",
                    "match_data": {
                        "matched_genre": genre_match,
                        "popularity_score": book_data.get("popularity_score", 0)
                    }
                })

        # Sort by popularity score (highest first)
        results.sort(key=lambda x: x["book_data"].get("popularity_score", 0), reverse=True)

        return results

    @staticmethod
    def _unique_books(book_list: list[dict]) -> list[dict]:
        """
        Deduplicate books by book_id, keeping first occurrence.

        Args:
            book_list: List of book dicts with book_id

        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []

        for book in book_list:
            book_id = book.get("book_id")
            if book_id and book_id not in seen:
                seen.add(book_id)
                unique.append(book)

        return unique

    @staticmethod
    def process_exchange(original_order_id: str, new_book_id: str, new_book_title: str,
                        customer_id: str, return_reason: str) -> dict:
        """
        Process an automatic book exchange - return original order and create new order in one transaction.

        This simulates a seamless exchange where:
        1. Original order is returned and refund is processed
        2. New order is created for the selected book
        3. Same delivery address is used from original order
        4. Price difference is automatically charged/credited to card on file

        Args:
            original_order_id: Order ID being returned
            new_book_id: Book ID from recommendations
            new_book_title: Title of new book for confirmation
            customer_id: Customer ID
            return_reason: Reason for return

        Returns:
            dict with complete exchange details including both transactions
        """
        original_input = original_order_id

        # Normalize order ID for robust processing
        original_order_id = EnterpriseServices._normalize_order_id(original_order_id)

        logger.info(
            f"EXCHANGE: Processing automatic exchange | "
            f"Original Order: {original_order_id} (original input: {original_input}) | "
            f"New Book: {new_book_id} ({new_book_title})"
        )

        # Get original order details
        original_order = MOCK_ORDERS.get(original_order_id)
        if not original_order:
            logger.error(f"EXCHANGE: Original order not found: {original_order_id}")
            return {"status": "error", "error": "Original order not found"}

        # Get new book details
        new_book = MOCK_BOOKS.get(new_book_id)
        if not new_book:
            logger.error(f"EXCHANGE: New book not found: {new_book_id}")
            return {"status": "error", "error": "Book not found"}

        # Get customer info for VIP discount
        customer_data = MOCK_CUSTOMERS.get(customer_id)
        if not customer_data:
            logger.warning(f"EXCHANGE: Customer not found: {customer_id}")
            customer_data = {}

        is_vip = customer_data.get("is_vip", False)
        tier = customer_data.get("tier", "Regular")

        # Calculate pricing
        discount_map = {"Silver": 10, "Gold": 15, "Platinum": 25, "Regular": 0}
        discount_percentage = discount_map.get(tier, 0)

        original_price = 28.99  # Mock - in production, would fetch from original order
        new_book_price = new_book.get("price", 29.99)
        discounted_price = new_book_price * (1 - discount_percentage / 100)
        price_difference = discounted_price - original_price

        # Generate mock transaction IDs
        return_txn_id = f"txn_{random.randint(10000, 99999)}"
        new_order_id = f"ORD-{random.randint(1000, 9999)}"
        exchange_txn_id = f"txn_{random.randint(10000, 99999)}"

        # Mock delivery address (in production, would fetch from order management system)
        delivery_address = {
            "street": "123 Main Street",
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90001"
        }

        # Mock payment method (in production, would fetch from payment system)
        card_last_four = "4242"

        logger.info(
            f"EXCHANGE: ✅ Exchange processed successfully | "
            f"Return TXN: {return_txn_id} | New Order: {new_order_id} | Exchange TXN: {exchange_txn_id}"
        )

        # Log to audit system
        audit_logger.info(
            f"Exchange processed: {original_order_id} → {new_order_id}",
            extra={
                'session_id': get_session_id(),
                'original_order_id': original_order_id,
                'new_order_id': new_order_id,
                'new_book_id': new_book_id,
                'new_book_title': new_book_title,
                'customer_id': customer_id,
                'customer_tier': tier,
                'return_txn_id': return_txn_id,
                'exchange_txn_id': exchange_txn_id,
                'price_difference': round(price_difference, 2),
                'event_type': 'EXCHANGE_PROCESSED'
            }
        )

        return {
            "status": "success",
            "exchange_type": "automatic",

            # Return transaction details
            "return_transaction": {
                "transaction_id": return_txn_id,
                "original_order_id": original_order_id,
                "return_reason": return_reason,
                "status": "processed"
            },

            # New order details
            "new_order": {
                "order_id": new_order_id,
                "book_id": new_book_id,
                "book_title": new_book_title,
                "book_author": new_book.get("author", "Unknown"),
                "format": new_book.get("formats", ["Hardcover"])[0],
                "original_price": new_book_price,
                "discounted_price": round(discounted_price, 2),
                "discount_applied": discount_percentage,
                "status": "confirmed"
            },

            # Delivery details
            "delivery": {
                "address": f"{delivery_address['street']}, {delivery_address['city']}, {delivery_address['state']} {delivery_address['zip']}",
                "estimated_delivery": "3-5 business days",
                "shipping_method": "Standard Shipping",
                "tracking_available": "You'll receive tracking info via email within 24 hours"
            },

            # Payment details
            "payment": {
                "transaction_id": exchange_txn_id,
                "price_difference": round(price_difference, 2),
                "payment_action": "credit" if price_difference < 0 else "charge",
                "card_last_four": card_last_four,
                "processing_message": f"${abs(price_difference):.2f} will be {'credited to' if price_difference < 0 else 'charged to'} your card ending in {card_last_four} within 3-5 business days"
            },

            # VIP benefits
            "vip_benefits": {
                "tier": tier,
                "free_return_shipping": is_vip,
                "discount_percentage": discount_percentage
            }
        }