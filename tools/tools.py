from typing import Any

tools_schema: list[dict[str, Any]] = [
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
        "description": "DEPRECATED: Use escalate_order_issue or escalate_general_question instead. Escalate to human. Use this if a customer is angry or request if out of policy",
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
        "name": "escalate_order_issue",
        "description": "Escalate an order-related issue to the Order Support team. Use this when customer has an order ID and needs human assistance (angry customer, complex return dispute, delivery problem, VIP exception request, policy denial requiring manager review). This routes to specialized order support with full order context and higher SLA (2-4 hours).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The customer's order ID (e.g., 'ORD-123'). Required so support team can look up full order history, customer profile, and order context."
                },
                "reason": {
                    "type": "string",
                    "description": "Clear, detailed explanation of why escalating. Include key context. Examples: 'Customer is angry - delivery delayed 7+ days past estimate', 'VIP Gold customer requesting return exception for read book - precedent DEC-001 found', 'Customer disputing charge - claims book arrived damaged but no photo provided'"
                },
                "policy_check_confirmation": {
                    "type": "string",
                    "description": "Confirms you've verified this legitimately requires escalation. Always use 'verified_compliant'.",
                    "enum": ["verified_compliant"]
                }
            },
            "required": ["order_id", "reason", "policy_check_confirmation"]
        }
    },

    {
        "name": "escalate_general_question",
        "description": "Escalate a general question or account issue to the General Support team. Use this for non-order-related questions that you cannot answer (complex policy questions not in FAQs, account access problems, technical website issues, specific shipping questions like 'shipping to India'). This routes to general support queue with standard SLA (24 hours).",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Clear explanation of what customer needs help with and why you cannot answer. Examples: 'Customer asking about shipping policy to India - not covered in policy document', 'Account password reset failing - customer tried 3 times', 'Technical issue - payment page not loading in Safari browser', 'Customer wants to know if we ship perishable items - not in FAQ'"
                },
                "question_category": {
                    "type": "string",
                    "enum": ["policy_question", "account_issue", "technical_problem", "shipping_inquiry", "other"],
                    "description": "Category of the general question for proper routing to specialized support agent"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer's email address if they provided it (for follow-up). Optional but helpful for support team to contact customer."
                }
            },
            "required": ["reason", "question_category"]
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
    },

    {
        "name": "get_book_recommendations",
        "description": "Get personalized book recommendations for a customer. Use this when a customer requests a return and you want to offer alternative books they might enjoy instead. IMPORTANT: Call this AFTER gathering return information (order details, customer info) but BEFORE processing the return. This gives customers an attractive alternative that might prevent the return. Only offer recommendations if: 1) Customer is returning a book, 2) Customer tone is neutral or positive (not angry/frustrated), 3) You have gathered necessary return information. Do NOT offer if customer is angry/escalated or explicitly requests speed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID from the order lookup result"
                },
                "num_recommendations": {
                    "type": "integer",
                    "description": "Number of recommendations to return (default: 3)"
                },
                "context": {
                    "type": "string",
                    "description": "Optional context about what they're returning (e.g., 'thriller', 'sci-fi') to improve recommendations"
                }
            },
            "required": ["customer_id"]
        }
    },

    {
        "name": "process_exchange",
        "description": "Process an automatic book exchange (return + new order in one transaction). Use this when a customer selects a recommended book for exchange. This tool will: 1) Process the return of the original order, 2) Create a new order for the selected book using the same delivery address, 3) Automatically charge/credit the price difference to the card on file, 4) Return complete transaction details. ONLY use this when customer explicitly confirms they want to exchange for a specific recommended book.",
        "input_schema": {
            "type": "object",
            "properties": {
                "original_order_id": {
                    "type": "string",
                    "description": "The order ID being returned"
                },
                "new_book_id": {
                    "type": "string",
                    "description": "The book ID from recommendations that customer wants to exchange for"
                },
                "new_book_title": {
                    "type": "string",
                    "description": "The title of the new book for confirmation"
                },
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID from the order lookup"
                },
                "return_reason": {
                    "type": "string",
                    "description": "Reason for the return (e.g., 'not as expected', 'exchanging for different title')"
                }
            },
            "required": ["original_order_id", "new_book_id", "new_book_title", "customer_id", "return_reason"]
        }
    }
]