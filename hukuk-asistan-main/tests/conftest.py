import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app
from app.security import create_access_token
from datetime import datetime

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_firestore_globally(monkeypatch):
    """
    Mock FirestoreManager for all tests to avoid real DB calls.
    This is more sophisticated to handle auth tests.
    """
    mock_manager = AsyncMock()

    # Mock methods for usage middleware
    mock_manager.check_user_search_limit.return_value = {"can_search": True}
    mock_manager.increment_user_search_usage.return_value = True

    # Mock methods for auth
    mock_manager.create_user_with_trial.return_value = "new-user-id"

    async def get_user_by_email(email):
        if email == "demo@yargisalzeka.com":
            return {
                "id": "demo-user-id",
                "email": "demo@yargisalzeka.com",
                "hashed_password": "$2b$12$EixZaYVK1e.JSguKgmB2v.4e.F3G4i.S3s4v5.6w7.8x9.0y1.2z3", # Dummy hash
                "full_name": "Demo User",
                "subscription_plan": "premium"
            }
        return None

    async def get_user_by_id(user_id):
        if user_id == "test-user-123":
             return {
                "id": "test-user-123",
                "email": "test@example.com",
                "hashed_password": "hashed_password",
                "full_name": "Test User",
                "is_active": True,
                "subscription_plan": "premium",
                "created_at": datetime(2023, 1, 1, 0, 0, 0)
            }
        return None

    mock_manager.get_user_by_email.side_effect = get_user_by_email
    mock_manager.get_user_by_id.side_effect = get_user_by_id

    monkeypatch.setattr("app.main.firestore_manager", mock_manager)
    monkeypatch.setattr("app.auth.firestore_manager", mock_manager)
    monkeypatch.setattr("app.usage_middleware.firestore_manager", mock_manager)


@pytest.fixture
async def async_client():
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def test_token():
    """Create a test JWT token"""
    token_data = {
        "sub": "test@example.com",
        "user_id": "test-user-123",
        "subscription_plan": "premium"
    }
    return create_access_token(data=token_data)

@pytest.fixture
def auth_headers(test_token):
    """Create authorization headers for tests"""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def sample_case_text():
    """Sample case text for testing"""
    return """
    Müvekkilim A şirketi ile B şirketi arasında imzalanan satış sözleşmesinde,
    B şirketi teslim tarihini geçirmesi nedeniyle tazminat talep etmekteyiz.
    Sözleşmede belirlenen 30 günlük teslim süresi aşılmış ve bu durum
    müvekkilime maddi zarar vermiştir.
    """