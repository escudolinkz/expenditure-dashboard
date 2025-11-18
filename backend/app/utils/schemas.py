from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Category Schemas
class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# Statement Schemas
class StatementCreate(BaseModel):
    card_name: Optional[str] = None
    card_last4: Optional[str] = None
    bank_type: str = "generic"


class StatementResponse(BaseModel):
    id: int
    filename: str
    card_name: Optional[str]
    card_last4: Optional[str]
    period_start: Optional[date]
    period_end: Optional[date]
    bank_type: str
    uploaded_at: datetime
    parsed_at: Optional[datetime]
    parse_status: str
    parse_error: Optional[str]
    transaction_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    transaction_date: date
    posting_date: Optional[date] = None
    merchant_name: Optional[str]
    description: Optional[str]
    amount: Decimal
    currency: str = "USD"
    transaction_type: str


class TransactionCreate(TransactionBase):
    statement_id: int
    category_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    merchant_name: Optional[str] = None
    description: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    statement_id: int
    category_id: Optional[int]
    category_name: Optional[str] = None
    category_confidence: Optional[Decimal]
    manually_categorized: bool
    card_name: Optional[str] = None
    card_last4: Optional[str] = None

    class Config:
        from_attributes = True


# Merchant Rule Schemas
class MerchantRuleCreate(BaseModel):
    pattern: str
    category_id: int
    pattern_type: str = "contains"  # exact, contains, regex
    is_case_sensitive: bool = False
    priority: int = 0


class MerchantRuleResponse(BaseModel):
    id: int
    pattern: str
    category_id: int
    category_name: Optional[str]
    pattern_type: str
    is_case_sensitive: bool
    priority: int
    confidence: Decimal

    class Config:
        from_attributes = True


# Analytics Schemas
class SpendingByCategory(BaseModel):
    category_id: Optional[int]
    category_name: str
    total_amount: Decimal
    transaction_count: int
    percentage: Optional[float] = None


class SpendingByTime(BaseModel):
    period: str  # Date, week, or month label
    total_amount: Decimal
    transaction_count: int
    categories: Optional[List[SpendingByCategory]] = None


class AnalyticsSummary(BaseModel):
    total_spending: Decimal
    transaction_count: int
    period_start: date
    period_end: date
    top_categories: List[SpendingByCategory]
    spending_by_category: List[SpendingByCategory]
    spending_by_time: List[SpendingByTime]


# Filter and Query Schemas
class TransactionFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category_id: Optional[int] = None
    card_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    search: Optional[str] = None
    transaction_type: Optional[str] = None
    page: int = 1
    limit: int = 50
