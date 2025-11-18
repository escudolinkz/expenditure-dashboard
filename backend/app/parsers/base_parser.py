from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date
import pdfplumber
import re


class ParsedTransaction:
    """Data class for a parsed transaction"""

    def __init__(
        self,
        transaction_date: date,
        merchant_name: str,
        amount: float,
        description: str = "",
        posting_date: Optional[date] = None,
        transaction_type: str = "charge",
        currency: str = "USD",
        raw_text: str = "",
    ):
        self.transaction_date = transaction_date
        self.posting_date = posting_date or transaction_date
        self.merchant_name = merchant_name
        self.description = description
        self.amount = abs(amount)  # Store as positive, type determines debit/credit
        self.transaction_type = transaction_type
        self.currency = currency
        self.raw_text = raw_text


class BaseParser(ABC):
    """
    Base class for PDF statement parsers.

    To add support for a new bank:
    1. Create a new class that inherits from BaseParser
    2. Implement the parse() method with bank-specific parsing logic
    3. Register the parser in ParserFactory
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.transactions: List[ParsedTransaction] = []
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def parse(self) -> List[ParsedTransaction]:
        """
        Parse the PDF and extract transactions.
        Must be implemented by subclasses.

        Returns:
            List of ParsedTransaction objects
        """
        pass

    def extract_text_from_pdf(self) -> str:
        """Extract all text from the PDF file"""
        text = ""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {str(e)}")
        return text

    def extract_tables_from_pdf(self) -> List[List[List[str]]]:
        """Extract tables from all pages of the PDF"""
        all_tables = []
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
        except Exception as e:
            raise ValueError(f"Failed to extract tables from PDF: {str(e)}")
        return all_tables

    def parse_date(self, date_str: str, formats: List[str] = None) -> Optional[date]:
        """
        Parse a date string with multiple format attempts

        Args:
            date_str: The date string to parse
            formats: List of strptime format strings to try

        Returns:
            Parsed date or None
        """
        if not date_str:
            return None

        if formats is None:
            formats = [
                "%m/%d/%Y",
                "%m/%d/%y",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d/%m/%y",
                "%b %d, %Y",
                "%B %d, %Y",
                "%d %b %Y",
                "%d %B %Y",
            ]

        from datetime import datetime

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def parse_amount(self, amount_str: str) -> Optional[float]:
        """
        Parse an amount string to float

        Args:
            amount_str: String representation of amount (e.g., "$1,234.56", "(500.00)")

        Returns:
            Parsed amount as float, or None if parsing fails
        """
        if not amount_str:
            return None

        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[$,\s]', '', amount_str.strip())

        # Handle parentheses as negative (common in accounting)
        is_negative = cleaned.startswith('(') and cleaned.endswith(')')
        if is_negative:
            cleaned = cleaned[1:-1]

        try:
            amount = float(cleaned)
            return -amount if is_negative else amount
        except ValueError:
            return None

    def determine_transaction_type(self, amount: float, description: str) -> str:
        """
        Determine transaction type based on amount and description

        Args:
            amount: Transaction amount (negative for credits)
            description: Transaction description

        Returns:
            Transaction type: charge, payment, refund, fee
        """
        description_lower = description.lower()

        if amount < 0:
            if "payment" in description_lower or "autopay" in description_lower:
                return "payment"
            elif "refund" in description_lower or "return" in description_lower:
                return "refund"
            else:
                return "payment"
        else:
            if "fee" in description_lower or "charge" in description_lower:
                return "fee"
            else:
                return "charge"

    def extract_card_info(self, text: str) -> Dict[str, str]:
        """
        Extract card information from PDF text

        Args:
            text: Full text of the PDF

        Returns:
            Dictionary with card_name and card_last4
        """
        card_info = {"card_name": None, "card_last4": None}

        # Try to find card last 4 digits
        last4_patterns = [
            r'ending in (\d{4})',
            r'card ending (\d{4})',
            r'account #?\*+(\d{4})',
            r'\*{4,}(\d{4})',
        ]

        for pattern in last4_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                card_info["card_last4"] = match.group(1)
                break

        return card_info

    def extract_statement_period(self, text: str) -> Dict[str, Optional[date]]:
        """
        Extract statement period from PDF text

        Args:
            text: Full text of the PDF

        Returns:
            Dictionary with period_start and period_end dates
        """
        period = {"period_start": None, "period_end": None}

        # Common patterns for statement periods
        patterns = [
            r'statement period:?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'billing period:?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*to\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'from\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*to\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                period["period_start"] = self.parse_date(match.group(1))
                period["period_end"] = self.parse_date(match.group(2))
                if period["period_start"] and period["period_end"]:
                    break

        return period
