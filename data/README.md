# Data Directory

This directory contains mock data and data loaders for the application.

## Files

### `mock_orders.json`
Mock order database for testing and demos. Contains sample customer orders with various statuses.

**Structure:**
```json
{
  "orders": {
    "ORDER_ID": {
      "status": "delivered|shipped|processing",
      "items": ["Product name"],
      "eligible_for_return": true|false,
      "customer_sentiment": "neutral|angry|positive",
      "customer_id": "CUST-XXX-XXXX",
      "customer_name": "Customer Name",
      "notes": "Optional notes"
    }
  }
}
```

### `mock_customers.json`
Customer database for testing and demos. Contains both VIP and regular customers.

**Structure for VIP Customers:**
```json
{
  "customers": {
    "CUST-VIP-XXXX": {
      "customer_name": "Customer Name",
      "is_vip": true,
      "tier": "Gold|Platinum|Silver",
      "lifetime_value": 15000,
      "years_active": 5,
      "member_since": "YYYY-MM-DD"
    }
  }
}
```

**Structure for Regular Customers:**
```json
{
  "customers": {
    "CUST-REG-XXXX": {
      "customer_name": "Customer Name",
      "is_vip": false,
      "years_active": 2,
      "member_since": "YYYY-MM-DD"
    }
  }
}
```

**Note:** `tier` and `lifetime_value` fields are only present for VIP customers.

### `data_loader.py`
Python module that loads JSON data files into Python dictionaries.

**Usage:**
```python
from data.data_loader import MOCK_ORDERS, MOCK_CUSTOMERS

# Get an order
order = MOCK_ORDERS.get("ORD-123")
print(order["customer_name"])

# Get a customer
customer = MOCK_CUSTOMERS.get("CUST-VIP-0001")
print(customer["customer_name"])

# Check if VIP
if customer.get("is_vip"):
    print(f"VIP Tier: {customer['tier']}")
```

## Adding New Mock Data

### Adding Orders

1. Edit `mock_orders.json`
2. Add new order under the `"orders"` key
3. Follow the structure shown above
4. Ensure valid JSON syntax (use `python -m json.tool mock_orders.json` to validate)
5. Restart your application to load the new data

### Adding Customers

1. Edit `mock_customers.json`
2. Add new customer under the `"customers"` key
3. For VIP customers, include: `tier` and `lifetime_value`
4. For regular customers, omit VIP-specific fields
5. Ensure valid JSON syntax (use `python -m json.tool mock_customers.json` to validate)
6. Restart your application to load the new data

## Order ID Conventions

- VIP customers: `CUST-VIP-XXXX`
- Regular customers: `CUST-REG-XXXX`
- Order IDs: `ORD-XXX`

## Data Relationships

- Orders reference customers via `customer_id`
- Customer names appear in both files for convenience (orders show name without lookup)
- `mock_customers.json` is the **source of truth** for customer data
- Both `check_vip_status()` and `get_customer_info()` use the same customer database

## Notes

- The data loader caches data at module import time for performance
- To reload data, restart the Python process
- All mock data is loaded into memory (suitable for testing/demos)
- The `_comment` and `_last_updated` fields in JSON are metadata (not used by code)
- Customer data is no longer duplicated in `services.py` - all in JSON files
