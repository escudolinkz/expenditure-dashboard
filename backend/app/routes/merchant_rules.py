from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, MerchantRule, Category
from app.utils.auth import get_current_user
from app.utils.schemas import MerchantRuleCreate, MerchantRuleResponse

router = APIRouter(prefix="/merchant-rules", tags=["Merchant Rules"])


@router.get("", response_model=List[MerchantRuleResponse])
def list_merchant_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all merchant rules for the current user"""
    rules = (
        db.query(MerchantRule)
        .filter(
            (MerchantRule.user_id == current_user.id) | (MerchantRule.is_global == True)
        )
        .order_by(MerchantRule.priority.desc())
        .all()
    )

    # Add category names
    result = []
    for rule in rules:
        rule_dict = rule.__dict__.copy()
        category = db.query(Category).filter(Category.id == rule.category_id).first()
        rule_dict["category_name"] = category.name if category else None
        result.append(rule_dict)

    return result


@router.post("", response_model=MerchantRuleResponse)
def create_merchant_rule(
    rule_data: MerchantRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new merchant rule"""
    # Verify category exists
    category = db.query(Category).filter(Category.id == rule_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    rule = MerchantRule(
        user_id=current_user.id,
        **rule_data.dict(),
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Add category name to response
    rule_dict = rule.__dict__.copy()
    rule_dict["category_name"] = category.name

    return rule_dict


@router.delete("/{rule_id}")
def delete_merchant_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a merchant rule"""
    rule = (
        db.query(MerchantRule)
        .filter(
            MerchantRule.id == rule_id,
            MerchantRule.user_id == current_user.id,
        )
        .first()
    )

    if not rule:
        raise HTTPException(status_code=404, detail="Merchant rule not found")

    db.delete(rule)
    db.commit()

    return {"message": "Merchant rule deleted successfully"}
