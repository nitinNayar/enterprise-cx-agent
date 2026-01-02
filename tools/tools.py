tools_schema = [
    {
        "name": "look_up_order",
        "description": "Fetch order details. This is the MANDATORY first step for any order query. You can NOT skip this",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        } 
    },

    {
        "name": "get_policy_info",
        "description": "Retrieve the official policy text for a specific topic. MANDATORY step before processing any refund.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_type": {
                    "type": "string", 
                    "enum": ["returns", "shipping", "privacy"],
                    "description": "The specific policy document to read."
                }
            },
            "required": ["policy_type"]
        }
    },    

    {
        "name": "execute_order_return",
        "description": "process the refund. RESTRICTED: only use if eligible_for_return is true AND if Policy allows it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {"type": "string"}
            },
            "required": ["order_id", "reason"]
        }
    },
    
    {
        "name": "escalate_to_human",
        "description": "Escalate to human. Use this if a customer is angry or request if out of policy",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "OPTIONAL order_id"} ,
                "reason": {"type": "string"},
                "policy_check_confirmation": {
                    "type": "string",
                    "description": "You must explicitly state: 'I have checked the policy and this item is NOT in the exclusion list.'",
                    "enum": ["verified_compliant"]
                }
            },
            "required": ["order_id", "reason", "policy_check_confirmation"]
        }
    },

    {
        "name": "check_precedents",
        "description": "Query the Kùzu Context Graph for past human decisions. Use this when a user asks for an exception (e.g., VIP).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_tags_str": {
                    "type": "string",
                    "description": "Space-separated keywords describing the context (e.g., 'socks vip return')"
                }
            },
            "required": ["query_tags_str"]
        }
    }
]