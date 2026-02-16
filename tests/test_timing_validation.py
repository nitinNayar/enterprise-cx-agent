"""
Test timing validation for late returns

Verifies that:
1. Mock orders have structured date fields
2. ORD-888 has days_since_purchase = 39
3. Data is correctly formatted
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.data_loader import MOCK_ORDERS


def test_date_fields_exist():
    """Verify all delivered orders have date fields"""
    print("\n📋 TEST 1: Verify Date Fields Exist")
    print("=" * 60)

    errors = []

    for order_id, order_data in MOCK_ORDERS.items():
        # Skip processing orders
        if order_data.get('status') == 'processing':
            print(f"  ⚪ {order_id}: Processing (no delivery date required)")
            continue

        # Check for required fields
        if 'purchase_date' not in order_data:
            errors.append(f"{order_id}: Missing 'purchase_date'")

        if 'days_since_purchase' not in order_data:
            errors.append(f"{order_id}: Missing 'days_since_purchase'")

        if order_data.get('status') == 'delivered' and 'delivered_date' not in order_data:
            errors.append(f"{order_id}: Status is 'delivered' but missing 'delivered_date'")

        if order_data.get('status') == 'shipped' and 'shipped_date' not in order_data:
            errors.append(f"{order_id}: Status is 'shipped' but missing 'shipped_date'")

        if not errors:
            days = order_data.get('days_since_purchase', 0)
            status_icon = "✅" if days <= 30 else "⏰"
            print(f"  {status_icon} {order_id}: {days} days since purchase")

    if errors:
        print("\n❌ ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All orders have required date fields!")
        return True


def test_ord_888_timing():
    """Verify ORD-888 has correct timing data"""
    print("\n📋 TEST 2: Verify ORD-888 Timing Data")
    print("=" * 60)

    ord_888 = MOCK_ORDERS.get('ORD-888')

    if not ord_888:
        print("❌ ERROR: ORD-888 not found in mock data")
        return False

    print(f"  Order ID: ORD-888")
    print(f"  Customer: {ord_888.get('customer_name')}")
    print(f"  Purchase Date: {ord_888.get('purchase_date')}")
    print(f"  Delivered Date: {ord_888.get('delivered_date')}")
    print(f"  Days Since Purchase: {ord_888.get('days_since_purchase')}")
    print(f"  Notes: {ord_888.get('notes')}")

    days = ord_888.get('days_since_purchase')

    if days != 55:
        print(f"\n❌ ERROR: Expected days_since_purchase = 55, got {days}")
        return False

    if days > 30:
        print(f"\n✅ Correctly identifies as LATE RETURN (55 > 30 days)")

    if days <= 60:
        print(f"✅ Within 60-day holiday window (55 < 60 days)")

    purchase_date = ord_888.get('purchase_date', '')
    if purchase_date.startswith('2025-12'):
        print(f"✅ Purchased in December 2025 (meets precedent condition)")

    if 'December' in ord_888.get('notes', '') or 'holiday' in ord_888.get('notes', '').lower():
        print(f"✅ Contains holiday gift context in notes")

    print("\n✅ ORD-888 timing data is correct!")
    return True


def test_timing_categories():
    """Categorize orders by return window status"""
    print("\n📋 TEST 3: Categorize Orders by Timing")
    print("=" * 60)

    within_window = []
    late_returns = []

    for order_id, order_data in MOCK_ORDERS.items():
        days = order_data.get('days_since_purchase', 0)

        if days <= 30:
            within_window.append((order_id, days))
        else:
            late_returns.append((order_id, days))

    print(f"\n  ✅ Within 30-Day Window ({len(within_window)} orders):")
    for order_id, days in sorted(within_window, key=lambda x: x[1]):
        print(f"     {order_id}: {days} days")

    print(f"\n  ⏰ Late Returns - Require Exception Check ({len(late_returns)} orders):")
    for order_id, days in sorted(late_returns, key=lambda x: x[1]):
        customer = MOCK_ORDERS[order_id].get('customer_name')
        print(f"     {order_id} ({customer}): {days} days")

    print(f"\n✅ Found {len(late_returns)} late returns that will trigger exception protocol")
    return True


def test_date_format():
    """Verify date fields are in correct format"""
    print("\n📋 TEST 4: Verify Date Format")
    print("=" * 60)

    from datetime import datetime

    errors = []

    for order_id, order_data in MOCK_ORDERS.items():
        purchase_date = order_data.get('purchase_date')

        if purchase_date:
            try:
                # Verify ISO format
                datetime.fromisoformat(purchase_date)
                print(f"  ✅ {order_id}: Valid date format ({purchase_date})")
            except ValueError:
                errors.append(f"{order_id}: Invalid purchase_date format: {purchase_date}")

        delivered_date = order_data.get('delivered_date')
        if delivered_date:
            try:
                datetime.fromisoformat(delivered_date)
            except ValueError:
                errors.append(f"{order_id}: Invalid delivered_date format: {delivered_date}")

    if errors:
        print("\n❌ ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All dates in correct ISO format!")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TIMING VALIDATION TEST SUITE")
    print("=" * 60)

    results = []

    results.append(("Date Fields Exist", test_date_fields_exist()))
    results.append(("ORD-888 Timing Data", test_ord_888_timing()))
    results.append(("Timing Categories", test_timing_categories()))
    results.append(("Date Format Validation", test_date_format()))

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Data layer is ready!")
        print("\nNext step: Test agent behavior with ORD-888")
        print("Expected: Agent should detect late return and apply holiday exception")
    else:
        print("❌ SOME TESTS FAILED - Please review errors above")
        sys.exit(1)
    print("=" * 60 + "\n")
