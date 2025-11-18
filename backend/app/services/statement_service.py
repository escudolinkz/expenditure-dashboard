from typing import List
import os
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models import Statement, Transaction, User
from app.parsers import ParserFactory
from app.services.categorizer import TransactionCategorizer


class StatementService:
    """Service for handling PDF statement upload and processing"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.upload_dir = os.getenv("UPLOAD_DIR", "/app/uploads")

    async def upload_statement(
        self,
        file: UploadFile,
        card_name: str = None,
        card_last4: str = None,
        bank_type: str = "generic",
    ) -> Statement:
        """
        Upload and save a PDF statement file.

        Args:
            file: The uploaded PDF file
            card_name: Optional card name
            card_last4: Optional last 4 digits of card
            bank_type: Bank type for selecting appropriate parser

        Returns:
            Created Statement object
        """
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise ValueError("Only PDF files are allowed")

        # Create user-specific upload directory
        user_upload_dir = os.path.join(self.upload_dir, str(self.user.id))
        os.makedirs(user_upload_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(user_upload_dir, safe_filename)

        # Save file
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)

        # Create statement record
        statement = Statement(
            user_id=self.user.id,
            filename=file.filename,
            file_path=file_path,
            card_name=card_name,
            card_last4=card_last4,
            bank_type=bank_type,
            parse_status="pending",
        )

        self.db.add(statement)
        self.db.commit()
        self.db.refresh(statement)

        return statement

    def parse_statement(self, statement_id: int) -> Statement:
        """
        Parse a PDF statement and extract transactions.

        Args:
            statement_id: ID of the statement to parse

        Returns:
            Updated Statement object
        """
        statement = (
            self.db.query(Statement)
            .filter(
                Statement.id == statement_id,
                Statement.user_id == self.user.id,
            )
            .first()
        )

        if not statement:
            raise ValueError("Statement not found")

        try:
            # Update status
            statement.parse_status = "processing"
            self.db.commit()

            # Get appropriate parser
            parser = ParserFactory.get_parser(statement.bank_type, statement.file_path)

            # Parse PDF
            parsed_transactions = parser.parse()

            # Update statement metadata from parser
            if parser.metadata.get("card_last4") and not statement.card_last4:
                statement.card_last4 = parser.metadata["card_last4"]
            if parser.metadata.get("period_start"):
                statement.period_start = parser.metadata["period_start"]
            if parser.metadata.get("period_end"):
                statement.period_end = parser.metadata["period_end"]

            # Create transaction records
            categorizer = TransactionCategorizer(self.db, self.user.id)

            for parsed_txn in parsed_transactions:
                transaction = Transaction(
                    statement_id=statement.id,
                    transaction_date=parsed_txn.transaction_date,
                    posting_date=parsed_txn.posting_date,
                    merchant_name=parsed_txn.merchant_name,
                    description=parsed_txn.description,
                    amount=parsed_txn.amount,
                    currency=parsed_txn.currency,
                    transaction_type=parsed_txn.transaction_type,
                    raw_text=parsed_txn.raw_text,
                )

                self.db.add(transaction)
                self.db.flush()  # Get transaction ID

                # Auto-categorize
                categorizer.categorize_transaction(transaction, save=False)

            # Update statement status
            statement.parse_status = "completed"
            statement.parsed_at = datetime.utcnow()
            statement.parse_error = None

            self.db.commit()
            self.db.refresh(statement)

            return statement

        except Exception as e:
            # Update statement with error
            statement.parse_status = "failed"
            statement.parse_error = str(e)
            self.db.commit()
            raise

    def reparse_statement(self, statement_id: int) -> Statement:
        """
        Re-parse a statement and update transactions.

        This is useful after adding new categorization rules.

        Args:
            statement_id: ID of the statement to re-parse

        Returns:
            Updated Statement object
        """
        statement = (
            self.db.query(Statement)
            .filter(
                Statement.id == statement_id,
                Statement.user_id == self.user.id,
            )
            .first()
        )

        if not statement:
            raise ValueError("Statement not found")

        # Delete existing transactions
        self.db.query(Transaction).filter(
            Transaction.statement_id == statement_id
        ).delete()

        self.db.commit()

        # Re-parse
        return self.parse_statement(statement_id)

    def recategorize_transactions(self, statement_id: int = None):
        """
        Re-run categorization on existing transactions.

        Args:
            statement_id: Optional statement ID to limit re-categorization.
                         If None, re-categorize all user's transactions.
        """
        query = self.db.query(Transaction).join(Statement).filter(
            Statement.user_id == self.user.id,
            Transaction.manually_categorized == False,  # Don't override manual categorizations
        )

        if statement_id:
            query = query.filter(Transaction.statement_id == statement_id)

        transactions = query.all()

        categorizer = TransactionCategorizer(self.db, self.user.id)
        categorizer.categorize_bulk(transactions, save=True)

    def list_statements(self) -> List[Statement]:
        """Get all statements for the current user"""
        return (
            self.db.query(Statement)
            .filter(Statement.user_id == self.user.id)
            .order_by(Statement.uploaded_at.desc())
            .all()
        )

    def delete_statement(self, statement_id: int) -> bool:
        """
        Delete a statement and its transactions.

        Args:
            statement_id: ID of the statement to delete

        Returns:
            True if deleted successfully
        """
        statement = (
            self.db.query(Statement)
            .filter(
                Statement.id == statement_id,
                Statement.user_id == self.user.id,
            )
            .first()
        )

        if not statement:
            raise ValueError("Statement not found")

        # Delete file
        if os.path.exists(statement.file_path):
            os.remove(statement.file_path)

        # Delete statement (cascades to transactions)
        self.db.delete(statement)
        self.db.commit()

        return True
