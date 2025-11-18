import pytest
from datetime import date
from app.parsers.base_parser import BaseParser, ParsedTransaction
from app.parsers.generic_parser import GenericParser


class TestBaseParser:
    """Tests for BaseParser utility methods"""

    def test_parse_date_various_formats(self):
        """Test date parsing with different formats"""
        parser = GenericParser("dummy.pdf")

        # Test MM/DD/YYYY format
        result = parser.parse_date("12/25/2023")
        assert result == date(2023, 12, 25)

        # Test MM/DD/YY format
        result = parser.parse_date("01/15/23")
        assert result == date(2023, 1, 15)

        # Test text format
        result = parser.parse_date("Dec 25, 2023")
        assert result == date(2023, 12, 25)

        # Test invalid date
        result = parser.parse_date("invalid")
        assert result is None

    def test_parse_amount_various_formats(self):
        """Test amount parsing with different formats"""
        parser = GenericParser("dummy.pdf")

        # Test simple amount
        result = parser.parse_amount("123.45")
        assert result == 123.45

        # Test with dollar sign
        result = parser.parse_amount("$1,234.56")
        assert result == 1234.56

        # Test with commas
        result = parser.parse_amount("10,000.00")
        assert result == 10000.00

        # Test negative (parentheses)
        result = parser.parse_amount("(500.00)")
        assert result == -500.00

        # Test invalid amount
        result = parser.parse_amount("invalid")
        assert result is None

    def test_determine_transaction_type(self):
        """Test transaction type determination"""
        parser = GenericParser("dummy.pdf")

        # Test charge
        result = parser.determine_transaction_type(100.00, "STORE PURCHASE")
        assert result == "charge"

        # Test payment
        result = parser.determine_transaction_type(-100.00, "PAYMENT - THANK YOU")
        assert result == "payment"

        # Test refund
        result = parser.determine_transaction_type(-50.00, "REFUND")
        assert result == "refund"

        # Test fee
        result = parser.determine_transaction_type(35.00, "LATE FEE")
        assert result == "fee"

    def test_extract_merchant_name(self):
        """Test merchant name extraction"""
        parser = GenericParser("dummy.pdf")

        # Test simple merchant
        result = parser._extract_merchant_name("WALMART SUPERCENTER")
        assert "WALMART" in result.upper()

        # Test with prefix removal
        result = parser._extract_merchant_name("DEBIT CARD PURCHASE - AMAZON.COM")
        assert "AMAZON" in result.upper()

        # Test empty description
        result = parser._extract_merchant_name("")
        assert result == "Unknown"


class TestParsedTransaction:
    """Tests for ParsedTransaction data class"""

    def test_parsed_transaction_creation(self):
        """Test creating a ParsedTransaction"""
        txn = ParsedTransaction(
            transaction_date=date(2023, 12, 25),
            merchant_name="TEST STORE",
            amount=100.50,
            description="Test purchase",
            transaction_type="charge",
        )

        assert txn.transaction_date == date(2023, 12, 25)
        assert txn.merchant_name == "TEST STORE"
        assert txn.amount == 100.50
        assert txn.transaction_type == "charge"

    def test_parsed_transaction_amount_absolute(self):
        """Test that amount is stored as absolute value"""
        txn = ParsedTransaction(
            transaction_date=date(2023, 12, 25),
            merchant_name="TEST",
            amount=-50.00,  # Negative amount
            transaction_type="payment",
        )

        # Amount should be stored as positive
        assert txn.amount == 50.00


def test_parser_factory():
    """Test ParserFactory registration and retrieval"""
    from app.parsers import ParserFactory

    # Test getting generic parser
    parser = ParserFactory.get_parser("generic", "test.pdf")
    assert isinstance(parser, GenericParser)

    # Test fallback to generic for unknown bank
    parser = ParserFactory.get_parser("unknown_bank", "test.pdf")
    assert isinstance(parser, GenericParser)

    # Test listing supported banks
    banks = ParserFactory.list_supported_banks()
    assert "generic" in banks


# Note: Full PDF parsing tests would require sample PDF files
# For integration testing, you would:
# 1. Create sample PDF files with known transaction data
# 2. Parse them and verify extracted transactions
# 3. Test different statement formats and edge cases

"""
Example integration test (requires sample PDF):

def test_full_pdf_parsing(tmp_path):
    # Create or use a sample PDF
    pdf_path = tmp_path / "sample_statement.pdf"

    # Copy sample PDF to tmp_path
    # shutil.copy("tests/fixtures/sample.pdf", pdf_path)

    parser = GenericParser(str(pdf_path))
    transactions = parser.parse()

    assert len(transactions) > 0
    assert all(isinstance(t, ParsedTransaction) for t in transactions)
    assert all(t.amount > 0 for t in transactions)
"""
