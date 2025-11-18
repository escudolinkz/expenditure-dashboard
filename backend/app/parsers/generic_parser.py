from typing import List
import re
from .base_parser import BaseParser, ParsedTransaction


class GenericParser(BaseParser):
    """
    Generic parser for credit card statements with table-based transaction lists.

    This parser attempts to extract transactions from common table formats.
    It looks for patterns like:
    Date | Description | Amount
    or
    Date | Merchant | Debit | Credit

    For bank-specific formats, create a new parser class that inherits from BaseParser.
    """

    def parse(self) -> List[ParsedTransaction]:
        """Parse the PDF and extract transactions"""
        # Extract text and tables
        text = self.extract_text_from_pdf()
        tables = self.extract_tables_from_pdf()

        # Store metadata
        self.metadata.update(self.extract_card_info(text))
        self.metadata.update(self.extract_statement_period(text))

        # Try table-based parsing first
        if tables:
            self.transactions = self._parse_from_tables(tables)

        # If no transactions found, try text-based parsing
        if not self.transactions:
            self.transactions = self._parse_from_text(text)

        return self.transactions

    def _parse_from_tables(self, tables: List[List[List[str]]]) -> List[ParsedTransaction]:
        """Parse transactions from extracted tables"""
        transactions = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Analyze header to determine column positions
            header = table[0] if table else []
            date_col, desc_col, amount_col = self._identify_columns(header)

            if date_col is None:
                continue

            # Parse each row
            for row in table[1:]:
                if not row or len(row) < 2:
                    continue

                transaction = self._parse_table_row(row, date_col, desc_col, amount_col)
                if transaction:
                    transactions.append(transaction)

        return transactions

    def _identify_columns(self, header: List[str]) -> tuple:
        """
        Identify column positions from table header

        Returns:
            Tuple of (date_col_index, description_col_index, amount_col_index)
        """
        header_lower = [h.lower() if h else "" for h in header]

        date_col = None
        desc_col = None
        amount_col = None

        for i, col in enumerate(header_lower):
            if not date_col and any(
                keyword in col for keyword in ["date", "trans date", "post date"]
            ):
                date_col = i
            elif not desc_col and any(
                keyword in col
                for keyword in ["description", "merchant", "transaction", "details"]
            ):
                desc_col = i
            elif not amount_col and any(
                keyword in col for keyword in ["amount", "debit", "charge", "total"]
            ):
                amount_col = i

        # If we couldn't identify columns from header, use positional defaults
        if date_col is None and len(header) >= 3:
            date_col = 0
            desc_col = 1
            amount_col = -1  # Last column

        return date_col, desc_col, amount_col

    def _parse_table_row(
        self, row: List[str], date_col: int, desc_col: int, amount_col: int
    ) -> ParsedTransaction:
        """Parse a single table row into a transaction"""
        try:
            # Extract date
            date_str = row[date_col] if date_col is not None and date_col < len(row) else ""
            transaction_date = self.parse_date(date_str)
            if not transaction_date:
                return None

            # Extract description/merchant
            description = ""
            if desc_col is not None and desc_col < len(row):
                description = row[desc_col].strip()
            if not description:
                # Use all text columns except date and amount
                text_parts = [
                    cell.strip()
                    for i, cell in enumerate(row)
                    if i not in [date_col, amount_col] and cell and cell.strip()
                ]
                description = " ".join(text_parts)

            # Extract amount
            amount_str = row[amount_col] if amount_col is not None and abs(amount_col) <= len(row) else ""
            amount = self.parse_amount(amount_str)
            if amount is None:
                # Try to find amount in other columns
                for cell in row:
                    amount = self.parse_amount(cell)
                    if amount is not None:
                        break

            if amount is None:
                return None

            # Determine merchant name (extract first part of description)
            merchant_name = self._extract_merchant_name(description)

            # Determine transaction type
            transaction_type = self.determine_transaction_type(amount, description)

            return ParsedTransaction(
                transaction_date=transaction_date,
                merchant_name=merchant_name,
                description=description,
                amount=abs(amount),
                transaction_type=transaction_type,
                raw_text=" | ".join(row),
            )

        except Exception as e:
            # Log error but continue parsing
            print(f"Error parsing row: {e}")
            return None

    def _parse_from_text(self, text: str) -> List[ParsedTransaction]:
        """
        Parse transactions from plain text when table extraction fails

        This is a fallback method that looks for transaction patterns in text.
        """
        transactions = []
        lines = text.split('\n')

        for line in lines:
            # Skip empty lines and headers
            if not line.strip() or len(line.strip()) < 10:
                continue

            # Look for lines that start with a date pattern
            date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})', line.strip())
            if not date_match:
                continue

            # Try to parse this line as a transaction
            transaction = self._parse_text_line(line)
            if transaction:
                transactions.append(transaction)

        return transactions

    def _parse_text_line(self, line: str) -> ParsedTransaction:
        """Parse a single text line into a transaction"""
        try:
            # Common pattern: DATE DESCRIPTION AMOUNT
            # Extract date (at the start)
            date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})', line.strip())
            if not date_match:
                return None

            date_str = date_match.group(1)
            transaction_date = self.parse_date(date_str)
            if not transaction_date:
                return None

            # Remove date from line
            remaining = line[date_match.end():].strip()

            # Extract amount (at the end, often preceded by $ or formatted with commas)
            amount_match = re.search(r'([\$\(]?[\d,]+\.\d{2}\)?)\s*$', remaining)
            if not amount_match:
                return None

            amount_str = amount_match.group(1)
            amount = self.parse_amount(amount_str)
            if amount is None:
                return None

            # What remains is the description
            description = remaining[:amount_match.start()].strip()
            merchant_name = self._extract_merchant_name(description)

            transaction_type = self.determine_transaction_type(amount, description)

            return ParsedTransaction(
                transaction_date=transaction_date,
                merchant_name=merchant_name,
                description=description,
                amount=abs(amount),
                transaction_type=transaction_type,
                raw_text=line,
            )

        except Exception as e:
            print(f"Error parsing line: {e}")
            return None

    def _extract_merchant_name(self, description: str) -> str:
        """
        Extract merchant name from transaction description

        This is a simple implementation that takes the first part of the description.
        Can be enhanced with more sophisticated NLP or pattern matching.
        """
        if not description:
            return "Unknown"

        # Remove common prefixes
        cleaned = re.sub(r'^(DEBIT CARD PURCHASE|PURCHASE|POS|ATM)\s*-?\s*', '', description, flags=re.IGNORECASE)

        # Take first meaningful part (up to first special character or number pattern)
        parts = re.split(r'[\d#\*]{4,}|\s{2,}|[\/\\]', cleaned)
        merchant = parts[0].strip() if parts else cleaned

        # Clean up
        merchant = re.sub(r'\s+', ' ', merchant).strip()

        return merchant[:100] if merchant else "Unknown"  # Limit length
