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
        "name": "get_customer_info",
        "description": "Retrieve customer information for personalized greeting. MANDATORY: Call this immediately after look_up_order to greet the customer by name and acknowledge their VIP status/loyalty. Use the customer_id from the order lookup result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID from the order lookup result"
                }
            },
            "required": ["customer_id"]
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
        "name": "check_vip_status",
        "description": "Check if a customer has VIP or high-value status. MANDATORY: Call this automatically whenever a return is denied by policy to determine if the customer qualifies for exception consideration. Do NOT wait for customer to ask - this should be automatic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID from the order lookup result"
                }
            },
            "required": ["customer_id"]
        }
    },

    {
        "name": "check_precedents",
        "description": "Query the Kùzu Context Graph for past human decisions. Use this when a customer is VIP AND their return was denied by standard policy. This checks if there are precedents for making exceptions for VIP customers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_tags_str": {
                    "type": "string",
                    "description": "Space-separated lowercase keywords describing the context. Extract relevant keywords from the situation (e.g., 'vip socks return exception', 'holiday gift late', 'electronics opened high_value'). Use lowercase for all keywords."
                }
            },
            "required": ["query_tags_str"]
        }
    }
]