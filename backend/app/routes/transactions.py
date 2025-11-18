from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models import User, Transaction, Statement, Category
from app.utils.auth import get_current_user
from app.utils.schemas import TransactionResponse, TransactionUpdate
from app.services.categorizer import TransactionCategorizer

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    statement_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get transactions with filtering and pagination.

    Filters:
    - start_date/end_date: Date range
    - category_id: Filter by category
    - statement_id: Filter by statement/card
    - transaction_type: Filter by type (charge, payment, refund, fee)
    - min_amount/max_amount: Amount range
    - search: Search merchant name or description
    """
    # Base query
    query = (
        db.query(Transaction)
        .join(Statement)
        .filter(Statement.user_id == current_user.id)
    )

    # Apply filters
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if statement_id:
        query = query.filter(Transaction.statement_id == statement_id)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.merchant_name.ilike(search_pattern),
                Transaction.description.ilike(search_pattern),
            )
        )

    # Count total
    total = query.count()

    # Paginate
    offset = (page - 1) * limit
    transactions = (
        query.order_by(Transaction.transaction_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Build response with additional data
    result = []
    for txn in transactions:
        txn_dict = txn.__dict__.copy()
        # Add category name
        if txn.category_id:
            category = db.query(Category).filter(Category.id == txn.category_id).first()
            txn_dict["category_name"] = category.name if category else None
        else:
            txn_dict["category_name"] = "Uncategorized"

        # Add card info
        statement = db.query(Statement).filter(Statement.id == txn.statement_id).first()
        if statement:
            txn_dict["card_name"] = statement.card_name
            txn_dict["card_last4"] = statement.card_last4

        result.append(txn_dict)

    return result


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific transaction"""
    transaction = (
        db.query(Transaction)
        .join(Statement)
        .filter(
            Transaction.id == transaction_id,
            Statement.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Build response
    txn_dict = transaction.__dict__.copy()
    if transaction.category_id:
        category = db.query(Category).filter(Category.id == transaction.category_id).first()
        txn_dict["category_name"] = category.name if category else None
    else:
        txn_dict["category_name"] = "Uncategorized"

    statement = db.query(Statement).filter(Statement.id == transaction.statement_id).first()
    if statement:
        txn_dict["card_name"] = statement.card_name
        txn_dict["card_last4"] = statement.card_last4

    return txn_dict


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    update_data: TransactionUpdate,
    create_rule: bool = Query(False, description="Create merchant rule for this category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a transaction (typically to change category).

    If create_rule=true, a merchant rule will be created to automatically
    categorize future transactions from this merchant.
    """
    transaction = (
        db.query(Transaction)
        .join(Statement)
        .filter(
            Transaction.id == transaction_id,
            Statement.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update fields
    if update_data.category_id is not None:
        transaction.category_id = update_data.category_id
        transaction.manually_categorized = True
        transaction.category_confidence = 1.0

        # Create merchant rule if requested
        if create_rule:
            categorizer = TransactionCategorizer(db, current_user.id)
            categorizer.create_rule_from_transaction(
                transaction, update_data.category_id
            )

    if update_data.merchant_name is not None:
        transaction.merchant_name = update_data.merchant_name

    if update_data.description is not None:
        transaction.description = update_data.description

    db.commit()
    db.refresh(transaction)

    # Build response
    txn_dict = transaction.__dict__.copy()
    if transaction.category_id:
        category = db.query(Category).filter(Category.id == transaction.category_id).first()
        txn_dict["category_name"] = category.name if category else None
    else:
        txn_dict["category_name"] = "Uncategorized"

    statement = db.query(Statement).filter(Statement.id == transaction.statement_id).first()
    if statement:
        txn_dict["card_name"] = statement.card_name
        txn_dict["card_last4"] = statement.card_last4

    return txn_dict


@router.post("/bulk-update")
def bulk_update_category(
    transaction_ids: List[int],
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update category for multiple transactions"""
    # Verify all transactions belong to user
    transactions = (
        db.query(Transaction)
        .join(Statement)
        .filter(
            Transaction.id.in_(transaction_ids),
            Statement.user_id == current_user.id,
        )
        .all()
    )

    if len(transactions) != len(transaction_ids):
        raise HTTPException(
            status_code=400,
            detail="Some transactions not found or don't belong to user",
        )

    # Update all transactions
    for txn in transactions:
        txn.category_id = category_id
        txn.manually_categorized = True
        txn.category_confidence = 1.0

    db.commit()

    return {
        "message": f"Updated {len(transactions)} transactions",
        "updated_count": len(transactions),
    }
