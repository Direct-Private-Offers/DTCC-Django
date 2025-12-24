"""
Pytest configuration and fixtures for DTCC Django project.
"""
import os
import django
from django.conf import settings
from django.test.utils import get_runner

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pytest
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    """API client for testing."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Authenticated API client."""
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def issuer_user(db):
    """Create a user with issuer group."""
    user = User.objects.create_user(
        username='issuer',
        email='issuer@example.com',
        password='testpass123'
    )
    group, _ = Group.objects.get_or_create(name='issuer')
    user.groups.add(group)
    return user


@pytest.fixture
def reporter_user(db):
    """Create a user with reporter group."""
    user = User.objects.create_user(
        username='reporter',
        email='reporter@example.com',
        password='testpass123'
    )
    group, _ = Group.objects.get_or_create(name='reporter')
    user.groups.add(group)
    return user


@pytest.fixture
def ops_user(db):
    """Create a user with ops group."""
    user = User.objects.create_user(
        username='ops',
        email='ops@example.com',
        password='testpass123'
    )
    group, _ = Group.objects.get_or_create(name='ops')
    user.groups.add(group)
    return user


@pytest.fixture
def mock_web3(monkeypatch):
    """Mock Web3 provider for blockchain tests."""
    from unittest.mock import MagicMock
    
    mock_w3 = MagicMock()
    mock_w3.eth.block_number = 12345678
    mock_w3.eth.get_transaction_receipt.return_value = {
        'status': 1,
        'transactionHash': b'\x12\x34\x56\x78',
    }
    
    def mock_get_web3_provider(*args, **kwargs):
        return mock_w3
    
    monkeypatch.setattr('apps.core.blockchain.get_web3_provider', mock_get_web3_provider)
    return mock_w3

