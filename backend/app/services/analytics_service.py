from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy import func, extract, case
from sqlalchemy.orm import Session

from app.models import Transaction, Statement, Category


class AnalyticsService:
    """Service for generating analytics and reports"""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        card_id: Optional[int] = None,
        include_credits: bool = False,
    ) -> dict:
        """
        Get summary statistics for a date range.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            card_id: Optional statement/card ID to filter by
            include_credits: Whether to include credit transactions

        Returns:
            Dictionary with summary statistics
        """
        query = self._base_query(include_credits)
        query = self._apply_filters(query, start_date, end_date, card_id)

        # Calculate totals
        result = query.with_entities(
            func.count(Transaction.id).label("transaction_count"),
            func.sum(Transaction.amount).label("total_spending"),
        ).first()

        return {
            "total_spending": float(result.total_spending or 0),
            "transaction_count": result.transaction_count or 0,
            "period_start": start_date,
            "period_end": end_date,
        }

    def get_spending_by_category(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        card_id: Optional[int] = None,
        include_credits: bool = False,
        limit: int = None,
    ) -> List[dict]:
        """
        Get spending grouped by category.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            card_id: Optional statement/card ID to filter by
            include_credits: Whether to include credit transactions
            limit: Optional limit for number of categories

        Returns:
            List of dictionaries with category spending data
        """
        query = self._base_query(include_credits)
        query = self._apply_filters(query, start_date, end_date, card_id)

        # Group by category
        results = (
            query.outerjoin(Category, Transaction.category_id == Category.id)
            .with_entities(
                Transaction.category_id,
                func.coalesce(Category.name, "Uncategorized").label("category_name"),
                func.sum(Transaction.amount).label("total_amount"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .group_by(Transaction.category_id, Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )

        if limit:
            results = results.limit(limit)

        results = results.all()

        # Calculate total for percentages
        total_spending = sum(r.total_amount for r in results)

        return [
            {
                "category_id": r.category_id,
                "category_name": r.category_name,
                "total_amount": float(r.total_amount),
                "transaction_count": r.transaction_count,
                "percentage": (
                    float(r.total_amount / total_spending * 100) if total_spending > 0 else 0
                ),
            }
            for r in results
        ]

    def get_spending_by_time(
        self,
        group_by: str = "monthly",  # daily, weekly, monthly
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        card_id: Optional[int] = None,
        include_credits: bool = False,
        include_category_breakdown: bool = False,
    ) -> List[dict]:
        """
        Get spending grouped by time period.

        Args:
            group_by: Grouping granularity (daily, weekly, monthly)
            start_date: Start date for filtering
            end_date: End date for filtering
            card_id: Optional statement/card ID to filter by
            include_credits: Whether to include credit transactions
            include_category_breakdown: Whether to include category breakdown per period

        Returns:
            List of dictionaries with time-based spending data
        """
        query = self._base_query(include_credits)
        query = self._apply_filters(query, start_date, end_date, card_id)

        if group_by == "daily":
            period_label = func.to_char(Transaction.transaction_date, 'YYYY-MM-DD')
            group_field = Transaction.transaction_date
        elif group_by == "weekly":
            # ISO week format: YYYY-Www
            period_label = func.concat(
                func.to_char(Transaction.transaction_date, 'IYYY'),
                '-W',
                func.to_char(Transaction.transaction_date, 'IW')
            )
            group_field = func.concat(
                func.to_char(Transaction.transaction_date, 'IYYY'),
                func.to_char(Transaction.transaction_date, 'IW')
            )
        else:  # monthly
            period_label = func.to_char(Transaction.transaction_date, 'YYYY-MM')
            group_field = func.to_char(Transaction.transaction_date, 'YYYY-MM')

        # Group by time period
        results = (
            query.with_entities(
                period_label.label("period"),
                func.sum(Transaction.amount).label("total_amount"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .group_by(group_field, period_label)
            .order_by(period_label)
            .all()
        )

        time_series = [
            {
                "period": r.period,
                "total_amount": float(r.total_amount),
                "transaction_count": r.transaction_count,
                "categories": None,
            }
            for r in results
        ]

        # Add category breakdown if requested
        if include_category_breakdown:
            for item in time_series:
                item["categories"] = self._get_categories_for_period(
                    item["period"], group_by, card_id, include_credits
                )

        return time_series

    def _get_categories_for_period(
        self, period: str, group_by: str, card_id: Optional[int], include_credits: bool
    ) -> List[dict]:
        """Get category breakdown for a specific time period"""
        # Parse period and determine date range
        if group_by == "daily":
            period_date = datetime.strptime(period, '%Y-%m-%d').date()
            start = period_date
            end = period_date
        elif group_by == "weekly":
            # Parse YYYY-Www format
            year, week = period.split('-W')
            # Get first day of week
            start = datetime.strptime(f'{year}-W{week}-1', '%Y-W%W-%w').date()
            end = start + timedelta(days=6)
        else:  # monthly
            year, month = period.split('-')
            start = date(int(year), int(month), 1)
            # Last day of month
            if int(month) == 12:
                end = date(int(year) + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(int(year), int(month) + 1, 1) - timedelta(days=1)

        return self.get_spending_by_category(
            start_date=start, end_date=end, card_id=card_id, include_credits=include_credits
        )

    def get_top_merchants(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        card_id: Optional[int] = None,
        limit: int = 10,
    ) -> List[dict]:
        """
        Get top merchants by spending.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            card_id: Optional statement/card ID to filter by
            limit: Number of top merchants to return

        Returns:
            List of dictionaries with merchant spending data
        """
        query = self._base_query(include_credits=False)
        query = self._apply_filters(query, start_date, end_date, card_id)

        results = (
            query.with_entities(
                Transaction.merchant_name,
                func.sum(Transaction.amount).label("total_amount"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .group_by(Transaction.merchant_name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "merchant_name": r.merchant_name,
                "total_amount": float(r.total_amount),
                "transaction_count": r.transaction_count,
            }
            for r in results
        ]

    def _base_query(self, include_credits: bool = False):
        """Create base query with user filtering"""
        query = (
            self.db.query(Transaction)
            .join(Statement)
            .filter(Statement.user_id == self.user_id)
        )

        if not include_credits:
            # Exclude payments and refunds
            query = query.filter(
                Transaction.transaction_type.in_(["charge", "fee"])
            )

        return query

    def _apply_filters(
        self,
        query,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        card_id: Optional[int] = None,
    ):
        """Apply common filters to query"""
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if card_id:
            query = query.filter(Transaction.statement_id == card_id)

        return query

    def export_transactions_csv(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
    ) -> str:
        """
        Export transactions to CSV format.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            category_id: Optional category ID to filter by

        Returns:
            CSV string
        """
        query = self._base_query(include_credits=True)
        query = self._apply_filters(query, start_date, end_date)

        if category_id:
            query = query.filter(Transaction.category_id == category_id)

        transactions = (
            query.outerjoin(Category, Transaction.category_id == Category.id)
            .with_entities(
                Transaction.transaction_date,
                Transaction.merchant_name,
                Transaction.description,
                func.coalesce(Category.name, "Uncategorized").label("category_name"),
                Transaction.amount,
                Transaction.transaction_type,
            )
            .order_by(Transaction.transaction_date.desc())
            .all()
        )

        # Build CSV
        csv_lines = ["Date,Merchant,Description,Category,Amount,Type"]
        for t in transactions:
            csv_lines.append(
                f"{t.transaction_date},{t.merchant_name or ''},"
                f'"{t.description or ""}",{t.category_name},'
                f"{t.amount},{t.transaction_type}"
            )

        return "\n".join(csv_lines)
