"""
Test configuration and fixtures for FastAPI tests
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Test client fixture for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """Sample activities data for testing"""
    return {
        "Test Club": {
            "description": "A test activity for testing purposes",
            "schedule": "Test days, 12:00 PM - 1:00 PM",
            "max_participants": 5,
            "participants": ["test1@mergington.edu", "test2@mergington.edu"]
        },
        "Empty Club": {
            "description": "An empty test activity",
            "schedule": "Never, 0:00 AM - 0:00 AM",
            "max_participants": 3,
            "participants": []
        }
    }


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    from src.app import activities
    original_activities = activities.copy()
    yield
    # Restore original activities after test
    activities.clear()
    activities.update(original_activities)