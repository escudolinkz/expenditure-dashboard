from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Statement(Base):
    __tablename__ = "statements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    card_name = Column(String)
    card_last4 = Column(String(4))
    period_start = Column(Date)
    period_end = Column(Date)
    bank_type = Column(String, default="generic")  # For selecting appropriate parser
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    parsed_at = Column(DateTime)
    parse_status = Column(String, default="pending")  # pending, processing, completed, failed
    parse_error = Column(String)

    # Relationships
    user = relationship("User", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")
