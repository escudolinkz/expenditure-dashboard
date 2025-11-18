from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import User, Statement, Transaction
from app.utils.auth import get_current_user
from app.utils.schemas import StatementResponse
from app.services.statement_service import StatementService

router = APIRouter(prefix="/statements", tags=["Statements"])


@router.post("/upload", response_model=StatementResponse)
async def upload_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    card_name: str = Form(None),
    card_last4: str = Form(None),
    bank_type: str = Form("generic"),
    auto_parse: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a credit card PDF statement.

    The file will be saved and optionally parsed in the background.
    """
    service = StatementService(db, current_user)

    # Upload file
    statement = await service.upload_statement(
        file=file,
        card_name=card_name,
        card_last4=card_last4,
        bank_type=bank_type,
    )

    # Parse in background if requested
    if auto_parse:
        background_tasks.add_task(service.parse_statement, statement.id)

    # Get transaction count
    statement_dict = statement.__dict__
    statement_dict["transaction_count"] = 0

    return statement_dict


@router.get("", response_model=List[StatementResponse])
def list_statements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all statements for the current user"""
    statements = (
        db.query(Statement)
        .filter(Statement.user_id == current_user.id)
        .order_by(Statement.uploaded_at.desc())
        .all()
    )

    # Add transaction counts
    result = []
    for statement in statements:
        statement_dict = statement.__dict__.copy()
        statement_dict["transaction_count"] = (
            db.query(func.count(Transaction.id))
            .filter(Transaction.statement_id == statement.id)
            .scalar()
        )
        result.append(statement_dict)

    return result


@router.get("/{statement_id}", response_model=StatementResponse)
def get_statement(
    statement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific statement"""
    statement = (
        db.query(Statement)
        .filter(
            Statement.id == statement_id,
            Statement.user_id == current_user.id,
        )
        .first()
    )

    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    # Add transaction count
    statement_dict = statement.__dict__.copy()
    statement_dict["transaction_count"] = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.statement_id == statement.id)
        .scalar()
    )

    return statement_dict


@router.post("/{statement_id}/parse", response_model=StatementResponse)
def parse_statement(
    statement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Parse or re-parse a statement"""
    service = StatementService(db, current_user)

    try:
        statement = service.parse_statement(statement_id)
        statement_dict = statement.__dict__.copy()
        statement_dict["transaction_count"] = (
            db.query(func.count(Transaction.id))
            .filter(Transaction.statement_id == statement.id)
            .scalar()
        )
        return statement_dict
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


@router.post("/{statement_id}/recategorize")
def recategorize_statement(
    statement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-run categorization on a statement's transactions"""
    service = StatementService(db, current_user)

    try:
        service.recategorize_transactions(statement_id)
        return {"message": "Recategorization completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{statement_id}")
def delete_statement(
    statement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a statement and its transactions"""
    service = StatementService(db, current_user)

    try:
        service.delete_statement(statement_id)
        return {"message": "Statement deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
