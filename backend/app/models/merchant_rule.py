from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class MerchantRule(Base):
    __tablename__ = "merchant_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Pattern matching
    pattern = Column(String, nullable=False, index=True)  # Merchant name pattern
    pattern_type = Column(String, default="exact")  # exact, contains, regex
    is_case_sensitive = Column(Boolean, default=False)

    # Priority and metadata
    priority = Column(Integer, default=0)  # Higher priority rules are checked first
    confidence = Column(Numeric(3, 2), default=1.0)  # Confidence score for this rule
    is_global = Column(Boolean, default=False)  # If True, apply to all users (admin-created)

    # Relationships
    user = relationship("User", back_populates="merchant_rules")
    category = relationship("Category", back_populates="merchant_rules")
