import logging
import random
import os

# Configure Logging to STDOUT (Terminal)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("BackendServices")

class EnterpriseServices:
    """
    Simulates Core Enterprise Integrations / API with 
    structured logging
    """

    @staticmethod
    def look_up_order(order_id):
        logger.info(f"API CALL: Querying OMS for Order ID: {order_id}")
        
        # Mock Database

        mock_db = {
            "ORD-123": {"status": "shipped", "items": ["Wireless Headphones"], "eligible_for_return": True, "customer_sentiment": "neutral"},
            "ORD-456": {"status": "delivered", "items": ["Gaming Mouse"], "eligible_for_return": False, "return_reason": "window_expired", "customer_sentiment": "neutral"},
            "ORD-999": {"status": "processing", "items": ["4K Monitor"], "eligible_for_return": True, "customer_sentiment": "angry"},
            "ORD-777": {"status": "delivered", "items": ["Premium Wool Socks"], "eligible_for_return": True, "customer_sentiment": "neutral"},
            "ORD-888": {"status": "delivered", "items": ["$50 PlayStation Store Card"], "eligible_for_return": True, "customer_sentiment": "neutral"},
            "ORD-555": {"status": "delivered", "items": ["Luxury Night Cream"], "eligible_for_return": True, "customer_sentiment": "positive"}
        }

        result = mock_db.get(order_id)
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