import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User, Category, MerchantRule, Transaction, Statement
from app.services.categorizer import TransactionCategorizer


# Test database setup
@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test user
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )
    session.add(user)

    # Create test categories
    categories = [
        Category(id=1, name="Groceries"),
        Category(id=2, name="Dining"),
        Category(id=3, name="Transport"),
    ]
    for cat in categories:
        session.add(cat)

    session.commit()

    yield session

    session.close()


def test_categorizer_with_merchant_rule(db_session):
    """Test categorization using merchant rules"""
    # Create a merchant rule
    rule = MerchantRule(
        user_id=1,
        category_id=1,  # Groceries
        pattern="WALMART",
        pattern_type="contains",
        is_case_sensitive=False,
        priority=10,
        confidence=1.0,
    )
    db_session.add(rule)

    # Create a test statement
    statement = Statement(
        id=1,
        user_id=1,
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        bank_type="generic",
    )
    db_session.add(statement)

    # Create a test transaction
    transaction = Transaction(
        statement_id=1,
        transaction_date=date.today(),
        merchant_name="WALMART SUPERCENTER",
        description="WALMART SUPERCENTER #1234",
        amount=Decimal("45.67"),
        transaction_type="charge",
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    # Categorize the transaction
    categorizer = TransactionCategorizer(db_session, user_id=1)
    category_id, confidence = categorizer.categorize_transaction(transaction, save=True)

    # Assert
    assert category_id == 1  # Groceries
    assert confidence == 1.0
    assert transaction.category_id == 1


def test_categorizer_with_default_keywords(db_session):
    """Test categorization using default keywords"""
    # Create a test statement
    statement = Statement(
        id=1,
        user_id=1,
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        bank_type="generic",
    )
    db_session.add(statement)

    # Create a test transaction with a known keyword
    transaction = Transaction(
        statement_id=1,
        transaction_date=date.today(),
        merchant_name="MCDONALD'S",
        description="MCDONALD'S #12345",
        amount=Decimal("12.50"),
        transaction_type="charge",
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    # Categorize the transaction
    categorizer = TransactionCategorizer(db_session, user_id=1)
    category_id, confidence = categorizer.categorize_transaction(transaction, save=True)

    # Assert - should be categorized as Dining
    assert category_id == 2  # Dining
    assert confidence == 0.7  # Default keyword confidence


def test_categorizer_create_rule(db_session):
    """Test creating a merchant rule from transaction"""
    # Create a test statement
    statement = Statement(
        id=1,
        user_id=1,
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        bank_type="generic",
    )
    db_session.add(statement)

    # Create a test transaction
    transaction = Transaction(
        statement_id=1,
        transaction_date=date.today(),
        merchant_name="TARGET",
        description="TARGET STORE #5678",
        amount=Decimal("89.99"),
        transaction_type="charge",
    )
    db_session.add(transaction)
    db_session.commit()

    # Create a rule from the transaction
    categorizer = TransactionCategorizer(db_session, user_id=1)
    rule = categorizer.create_rule_from_transaction(
        transaction, category_id=1  # Groceries
    )

    # Assert
    assert rule.pattern == "TARGET"
    assert rule.category_id == 1
    assert rule.user_id == 1
    assert rule.confidence == 1.0


def test_categorizer_bulk_categorization(db_session):
    """Test bulk categorization of transactions"""
    # Create test statement
    statement = Statement(
        id=1,
        user_id=1,
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        bank_type="generic",
    )
    db_session.add(statement)

    # Create multiple transactions
    transactions = [
        Transaction(
            statement_id=1,
            transaction_date=date.today(),
            merchant_name="WALMART",
            description="WALMART",
            amount=Decimal("50.00"),
            transaction_type="charge",
        ),
        Transaction(
            statement_id=1,
            transaction_date=date.today(),
            merchant_name="SHELL GAS",
            description="SHELL GAS STATION",
            amount=Decimal("40.00"),
            transaction_type="charge",
        ),
    ]

    for txn in transactions:
        db_session.add(txn)

    db_session.commit()

    # Categorize in bulk
    categorizer = TransactionCategorizer(db_session, user_id=1)
    categorizer.categorize_bulk(transactions, save=True)

    # Assert - at least some should be categorized
    categorized_count = sum(1 for txn in transactions if txn.category_id is not None)
    assert categorized_count > 0
