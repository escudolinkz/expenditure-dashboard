from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("statements.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))

    # Transaction details
    transaction_date = Column(Date, nullable=False, index=True)
    posting_date = Column(Date)
    merchant_name = Column(String, index=True)
    description = Column(String)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    transaction_type = Column(String, nullable=False)  # charge, payment, refund, fee

    # Metadata
    raw_text = Column(String)  # Original line from PDF for reference
    category_confidence = Column(Numeric(3, 2))  # 0.00 to 1.00
    manually_categorized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    statement = relationship("Statement", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
