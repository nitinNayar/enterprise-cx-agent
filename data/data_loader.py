"""
Data loader utilities for mock data.
Loads JSON data files from the data directory.
"""

import json
from pathlib import Path
from typing import Any

# Get path to data directory
DATA_DIR = Path(__file__).parent


def load_mock_orders() -> dict[str, Any]:
    """
    Load mock order database from JSON file.
    
    Returns:
        dict mapping order_id to order data
        
    Example:
        >>> orders = load_mock_orders()
        >>> order = orders.get("ORD-123")
        >>> print(order["customer_name"])
        John McClane
    """
    orders_file = DATA_DIR / "mock_orders.json"
    
    try:
        with open(orders_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        orders = data.get("orders", {})
        print(f"✅ Loaded {len(orders)} mock orders from {orders_file.name}")
        return orders
        
    except FileNotFoundError:
        print(f"⚠️  WARNING: {orders_file} not found. Using empty order database.")
        return {}
        
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in {orders_file}: {e}")
        return {}
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load orders: {e}")
        return {}


def load_mock_customers() -> dict[str, Any]:
    """
    Load mock customer database from JSON file.

    Returns:
        dict mapping customer_id to customer data

    Example:
        >>> customers = load_mock_customers()
        >>> customer = customers.get("CUST-VIP-0001")
        >>> print(customer["customer_name"])
        John McClane
    """
    customers_file = DATA_DIR / "mock_customers_enhanced.json"

    try:
        with open(customers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        customers = data.get("customers", {})
        print(f"✅ Loaded {len(customers)} mock customers from {customers_file.name}")
        return customers

    except FileNotFoundError:
        print(f"⚠️  WARNING: {customers_file} not found. Using empty customer database.")
        return {}

    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in {customers_file}: {e}")
        return {}

    except Exception as e:
        print(f"❌ ERROR: Failed to load customers: {e}")
        return {}


def load_mock_books() -> dict[str, Any]:
    """
    Load mock book catalog from JSON file.

    Returns:
        dict mapping book_id to book data

    Example:
        >>> books = load_mock_books()
        >>> book = books.get("BOOK-001")
        >>> print(book["title"])
        Killing Floor
    """
    books_file = DATA_DIR / "mock_books_catalog.json"

    try:
        with open(books_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        books = data.get("books", {})
        print(f"✅ Loaded {len(books)} mock books from {books_file.name}")
        return books

    except FileNotFoundError:
        print(f"⚠️  WARNING: {books_file} not found. Using empty book catalog.")
        return {}

    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in {books_file}: {e}")
        return {}

    except Exception as e:
        print(f"❌ ERROR: Failed to load books: {e}")
        return {}


# Load data once at module level (cached for performance)
MOCK_ORDERS: dict[str, Any] = load_mock_orders()
MOCK_CUSTOMERS: dict[str, Any] = load_mock_customers()
MOCK_BOOKS: dict[str, Any] = load_mock_books()
