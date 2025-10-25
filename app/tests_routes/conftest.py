# tests/conftest.py
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_db_conn():
    """Mock database connection with proper transaction methods"""
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_conn.execute.return_value = mock_result
    
    # Mock transaction methods
    mock_tx = MagicMock()
    mock_tx.is_active = True
    mock_tx.rollback = MagicMock()
    mock_tx.commit = MagicMock()
    
    mock_conn.begin.return_value = mock_tx
    mock_conn.begin_nested.return_value = mock_tx
    mock_conn.in_transaction = False
    
    return mock_conn

@pytest.fixture
def admin_jwt_payload():
    """Admin user JWT payload"""
    return {
        "sub": "1",
        "role": "Admin",
        "email": "admin@example.com"
    }

@pytest.fixture
def user_jwt_payload():
    """Regular user JWT payload"""
    return {
        "sub": "2", 
        "role": "Client",
        "email": "user@example.com"
    }