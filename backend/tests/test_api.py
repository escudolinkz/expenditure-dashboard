import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, Category
from app.utils.auth import get_password_hash


# Test database setup
@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()

    # Seed default categories
    categories = [
        Category(id=1, name="Groceries"),
        Category(id=2, name="Dining"),
        Category(id=3, name="Transport"),
    ]
    for cat in categories:
        db.add(cat)
    db.commit()

    yield db

    db.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers"""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",  # Already exists
                "password": "password123",
                "full_name": "Duplicate User",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401


class TestCategoryEndpoints:
    """Tests for category endpoints"""

    def test_list_categories(self, client, auth_headers):
        """Test listing categories"""
        response = client.get("/api/categories", headers=auth_headers)

        assert response.status_code == 200
        categories = response.json()
        assert len(categories) >= 3
        assert any(cat["name"] == "Groceries" for cat in categories)

    def test_create_category(self, client, auth_headers):
        """Test creating a category"""
        response = client.post(
            "/api/categories",
            headers=auth_headers,
            json={"name": "New Category", "color": "#FF0000"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Category"
        assert data["color"] == "#FF0000"


class TestTransactionEndpoints:
    """Tests for transaction endpoints"""

    def test_list_transactions_unauthorized(self, client):
        """Test listing transactions without auth"""
        response = client.get("/api/transactions")
        assert response.status_code == 401

    def test_list_transactions_with_auth(self, client, auth_headers):
        """Test listing transactions with auth"""
        response = client.get("/api/transactions", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_transactions_with_filters(self, client, auth_headers):
        """Test listing transactions with filters"""
        response = client.get(
            "/api/transactions",
            headers=auth_headers,
            params={
                "category_id": 1,
                "transaction_type": "charge",
                "limit": 10,
            },
        )

        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints"""

    def test_get_summary(self, client, auth_headers):
        """Test getting analytics summary"""
        response = client.get("/api/analytics/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_spending" in data
        assert "transaction_count" in data

    def test_get_spending_by_category(self, client, auth_headers):
        """Test getting spending by category"""
        response = client.get(
            "/api/analytics/spending/by-category", headers=auth_headers
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_time_series(self, client, auth_headers):
        """Test getting time series data"""
        response = client.get(
            "/api/analytics/spending/time-series",
            headers=auth_headers,
            params={"group_by": "monthly"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
