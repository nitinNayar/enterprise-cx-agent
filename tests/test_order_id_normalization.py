"""
Test suite for order ID normalization feature.

This test suite verifies that order lookups are resilient to:
- Case variations (ORD-123 vs ord-123)
- Delimiter variations (ORD-123 vs ORD_123)
- Whitespace (leading/trailing spaces)
- Combinations of the above

Bug fix for: https://github.com/nitinNayar/enterprise-cx-agent/issues/TBD
"""

import pytest
from services.services import EnterpriseServices


class TestOrderIDNormalization:
    """Test order ID normalization helper function."""

    def test_exact_match(self):
        """Test that exact match passes through unchanged."""
        assert EnterpriseServices._normalize_order_id("ORD-123") == "ORD-123"

    def test_lowercase_conversion(self):
        """Test that lowercase is converted to uppercase."""
        assert EnterpriseServices._normalize_order_id("ord-123") == "ORD-123"

    def test_underscore_to_hyphen(self):
        """Test that underscores are replaced with hyphens."""
        assert EnterpriseServices._normalize_order_id("ORD_123") == "ORD-123"

    def test_lowercase_with_underscore(self):
        """Test combination of lowercase and underscore."""
        assert EnterpriseServices._normalize_order_id("ord_123") == "ORD-123"

    def test_whitespace_stripping(self):
        """Test that leading/trailing whitespace is stripped."""
        assert EnterpriseServices._normalize_order_id(" ORD-123 ") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("  ORD-123  ") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("\tORD-123\n") == "ORD-123"

    def test_space_as_delimiter(self):
        """Test that spaces between prefix and number are handled."""
        assert EnterpriseServices._normalize_order_id("ord 123") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("ORD 123") == "ORD-123"

    def test_multiple_spaces(self):
        """Test that multiple consecutive spaces are handled."""
        assert EnterpriseServices._normalize_order_id("ord  123") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("ORD   123") == "ORD-123"

    def test_colon_as_delimiter(self):
        """Test that colons are handled as delimiters."""
        assert EnterpriseServices._normalize_order_id("ORD:123") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("ord:123") == "ORD-123"

    def test_dot_as_delimiter(self):
        """Test that dots are handled as delimiters."""
        assert EnterpriseServices._normalize_order_id("ORD.123") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("ord.123") == "ORD-123"

    def test_no_delimiter(self):
        """Test that missing delimiter is handled (ORD123 → ORD-123)."""
        assert EnterpriseServices._normalize_order_id("ORD123") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("ord123") == "ORD-123"

    def test_mixed_delimiters(self):
        """Test combination of different delimiters."""
        assert EnterpriseServices._normalize_order_id("ord_ 123") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("ord _123") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("ord:_123") == "ORD-123"

    def test_all_variations_combined(self):
        """Test combination of all variations."""
        assert EnterpriseServices._normalize_order_id("  ord_123  ") == "ORD-123"
        assert EnterpriseServices._normalize_order_id(" Ord_123 ") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("  ord 123  ") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("  ord:123  ") == "ORD-123"
        assert EnterpriseServices._normalize_order_id("  ord123  ") == "ORD-123"

    def test_empty_string(self):
        """Test that empty string is handled gracefully."""
        assert EnterpriseServices._normalize_order_id("") == ""

    def test_none_value(self):
        """Test that None is handled gracefully."""
        assert EnterpriseServices._normalize_order_id(None) is None


class TestOrderLookupWithNormalization:
    """Test that order lookup works with various input formats."""

    def test_lookup_with_exact_format(self):
        """Test lookup with exact format (ORD-123)."""
        result = EnterpriseServices.look_up_order("ORD-123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"
        assert result["status"] == "Delivered"

    def test_lookup_with_lowercase(self):
        """Test lookup with lowercase input (ord-123)."""
        result = EnterpriseServices.look_up_order("ord-123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"
        assert result["status"] == "Delivered"

    def test_lookup_with_underscore(self):
        """Test lookup with underscore delimiter (ORD_123)."""
        result = EnterpriseServices.look_up_order("ORD_123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"
        assert result["status"] == "Delivered"

    def test_lookup_with_lowercase_and_underscore(self):
        """Test lookup with both lowercase and underscore (ord_123)."""
        result = EnterpriseServices.look_up_order("ord_123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"
        assert result["status"] == "Delivered"

    def test_lookup_with_whitespace(self):
        """Test lookup with leading/trailing whitespace."""
        result = EnterpriseServices.look_up_order("  ORD-123  ")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"

    def test_lookup_with_space_delimiter(self):
        """Test lookup with space as delimiter (ord 123)."""
        result = EnterpriseServices.look_up_order("ord 123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"
        assert result["status"] == "Delivered"

    def test_lookup_with_multiple_spaces(self):
        """Test lookup with multiple spaces."""
        result = EnterpriseServices.look_up_order("ORD  123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"

    def test_lookup_with_colon_delimiter(self):
        """Test lookup with colon as delimiter (ORD:123)."""
        result = EnterpriseServices.look_up_order("ORD:123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"

    def test_lookup_with_no_delimiter(self):
        """Test lookup with no delimiter (ORD123)."""
        result = EnterpriseServices.look_up_order("ORD123")
        assert "error" not in result
        assert result["customer_name"] == "John McClane"

    def test_lookup_all_variations_same_result(self):
        """Test that all variations return the same result."""
        variations = [
            "ORD-123",
            "ord-123",
            "ORD_123",
            "ord_123",
            " ORD-123 ",
            "  ord_123  ",
            "ord 123",      # Space delimiter
            "ORD  123",     # Multiple spaces
            "  ord 123  ",  # Space + whitespace
            "ORD:123",      # NEW: Colon delimiter
            "ord:123",      # NEW: Colon (lowercase)
            "ORD123",       # NEW: No delimiter
            "ord123",       # NEW: No delimiter (lowercase)
            "ORD.123",      # NEW: Dot delimiter
        ]

        results = [EnterpriseServices.look_up_order(v) for v in variations]

        # All should succeed (no errors)
        for result in results:
            assert "error" not in result

        # All should return the same customer
        customer_names = [r["customer_name"] for r in results]
        assert all(name == "John McClane" for name in customer_names)

    def test_lookup_nonexistent_order(self):
        """Test that nonexistent order still returns error even with normalization."""
        result = EnterpriseServices.look_up_order("ord-99999")
        assert "error" in result
        assert "not found" in result["error"]


class TestRefundWithNormalization:
    """Test that refund processing works with normalized order IDs."""

    def test_refund_with_lowercase(self):
        """Test refund with lowercase order ID."""
        result = EnterpriseServices.execute_refund("ord-123", "customer request")
        assert result["status"] == "success"
        assert "transaction_id" in result

    def test_refund_with_underscore(self):
        """Test refund with underscore delimiter."""
        result = EnterpriseServices.execute_refund("ORD_123", "defective product")
        assert result["status"] == "success"
        assert "transaction_id" in result


class TestEscalationWithNormalization:
    """Test that escalation works with normalized order IDs."""

    def test_escalation_with_lowercase(self):
        """Test escalation with lowercase order ID."""
        result = EnterpriseServices.escalate_to_human("ord-123", "angry customer")
        assert result["status"] == "escalated"
        assert "ticket_id" in result

    def test_escalation_with_underscore(self):
        """Test escalation with underscore delimiter."""
        result = EnterpriseServices.escalate_to_human("ORD_123", "complex issue")
        assert result["status"] == "escalated"
        assert "ticket_id" in result


class TestExchangeWithNormalization:
    """Test that exchange processing works with normalized order IDs."""

    def test_exchange_with_lowercase(self):
        """Test exchange with lowercase order ID."""
        result = EnterpriseServices.process_exchange(
            original_order_id="ord-123",
            new_book_id="BOOK-002",
            new_book_title="The Killing Floor",
            customer_id="CUST-VIP-0001",
            return_reason="want different book"
        )
        assert result["status"] == "success"
        assert result["return_transaction"]["original_order_id"] == "ORD-123"

    def test_exchange_with_underscore(self):
        """Test exchange with underscore delimiter."""
        result = EnterpriseServices.process_exchange(
            original_order_id="ORD_456",
            new_book_id="BOOK-003",
            new_book_title="Die Trying",
            customer_id="CUST-REG-0001",
            return_reason="exchanging for sequel"
        )
        assert result["status"] == "success"
        assert result["return_transaction"]["original_order_id"] == "ORD-456"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
