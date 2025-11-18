from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.models import User
from app.utils.auth import get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    card_id: Optional[int] = None,
    include_credits: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get summary statistics for a date range.

    Returns total spending, transaction count, and top categories.
    """
    analytics = AnalyticsService(db, current_user.id)

    summary = analytics.get_summary(
        start_date=start_date,
        end_date=end_date,
        card_id=card_id,
        include_credits=include_credits,
    )

    # Add top categories
    top_categories = analytics.get_spending_by_category(
        start_date=start_date,
        end_date=end_date,
        card_id=card_id,
        include_credits=include_credits,
        limit=3,
    )

    summary["top_categories"] = top_categories

    return summary


@router.get("/spending/by-category")
def get_spending_by_category(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    card_id: Optional[int] = None,
    include_credits: bool = Query(False),
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get spending grouped by category.

    Returns list of categories with total spending and transaction counts.
    """
    analytics = AnalyticsService(db, current_user.id)

    return analytics.get_spending_by_category(
        start_date=start_date,
        end_date=end_date,
        card_id=card_id,
        include_credits=include_credits,
        limit=limit,
    )


@router.get("/spending/time-series")
def get_spending_time_series(
    group_by: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    card_id: Optional[int] = None,
    include_credits: bool = Query(False),
    include_categories: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get spending grouped by time period (daily/weekly/monthly).

    Parameters:
    - group_by: Grouping granularity (daily, weekly, monthly)
    - include_categories: Include category breakdown for each period

    Returns time series data with spending per period.
    """
    analytics = AnalyticsService(db, current_user.id)

    return analytics.get_spending_by_time(
        group_by=group_by,
        start_date=start_date,
        end_date=end_date,
        card_id=card_id,
        include_credits=include_credits,
        include_category_breakdown=include_categories,
    )


@router.get("/top-merchants")
def get_top_merchants(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    card_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get top merchants by spending.

    Returns list of merchants with total spending and transaction counts.
    """
    analytics = AnalyticsService(db, current_user.id)

    return analytics.get_top_merchants(
        start_date=start_date,
        end_date=end_date,
        card_id=card_id,
        limit=limit,
    )


@router.get("/export/csv", response_class=PlainTextResponse)
def export_transactions_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export transactions to CSV format.

    Returns CSV file with transactions matching the filters.
    """
    analytics = AnalyticsService(db, current_user.id)

    csv_content = analytics.export_transactions_csv(
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
    )

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )
