"""
Shared pytest fixtures and configuration for all tests.
"""

import os
import sys
from pathlib import Path
from typing import Generator, Any
import pytest
from unittest.mock import Mock, patch
import tempfile
import shutil

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Test environment setup
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "api_base_url": "http://localhost:8000",
        "test_user": {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "username": "testuser"
        },
        "admin_user": {
            "email": "admin@example.com",
            "password": "AdminPassword123!",
            "username": "admin"
        },
        "database": {
            "url": "sqlite:///./test.db",
            "echo": False
        }
    }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_database():
    """Mock database connection."""
    with patch('backend.app.core.database.get_db') as mock_db:
        mock_session = Mock()
        mock_db.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_auth():
    """Mock authentication."""
    with patch('backend.app.core.security.verify_token') as mock_verify:
        mock_verify.return_value = {
            "sub": "test@example.com",
            "user_id": 1,
            "role": "user"
        }
        yield mock_verify


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    with patch('boto3.client') as mock_client:
        s3_mock = Mock()
        mock_client.return_value = s3_mock
        yield s3_mock


@pytest.fixture
def sample_dataset():
    """Provide sample dataset for testing."""
    return {
        "id": 1,
        "name": "Test Dataset",
        "description": "A test dataset",
        "file_path": "/test/path/dataset.csv",
        "file_type": "csv",
        "size": 1024,
        "owner_id": 1,
        "sharing_level": "private",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_connector():
    """Provide sample connector for testing."""
    return {
        "id": 1,
        "name": "Test Database",
        "type": "postgresql",
        "connection_details": {
            "host": "localhost",
            "port": 5432,
            "database": "testdb"
        },
        "owner_id": 1,
        "is_active": True
    }


@pytest.fixture
def api_client():
    """Create test API client."""
    from fastapi.testclient import TestClient
    try:
        from backend.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("Backend not available")


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    # Cleanup logic
    test_files = [
        "test.db",
        "test_upload.csv",
        "test_document.pdf"
    ]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


@pytest.fixture
def mock_mindsdb():
    """Mock MindsDB connection."""
    with patch('mindsdb_sdk.connect') as mock_connect:
        mock_server = Mock()
        mock_connect.return_value = mock_server
        yield mock_server


@pytest.fixture
def mock_gemini():
    """Mock Google Gemini AI."""
    with patch('google.generativeai.GenerativeModel') as mock_model:
        mock_instance = Mock()
        mock_model.return_value = mock_instance
        mock_instance.generate_content.return_value.text = "AI response"
        yield mock_instance


# Markers for slow tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_db: marks tests that require database"
    )
    config.addinivalue_line(
        "markers", "requires_mindsdb: marks tests that require MindsDB"
    )


# Skip slow tests by default
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers."""
    if not config.getoption("-m"):
        skip_slow = pytest.mark.skip(reason="Slow test - run with '-m slow'")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)