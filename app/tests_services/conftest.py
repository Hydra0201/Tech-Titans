# tests/conftest.py
import os
import sys
from unittest.mock import MagicMock

# Set required environment variables for testing
os.environ['JWT_SECRET'] = 'test-secret-key-for-testing-only'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Mock the problematic imports
sys.modules['app.db.engine'] = MagicMock()
sys.modules['app.models.user'] = MagicMock()

# Import after setting up mocks
from app.services.auth import AuthService