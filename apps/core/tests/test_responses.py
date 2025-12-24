"""
Tests for core response utilities.
"""
import pytest
from django.utils import timezone
from apps.core.responses import ok, bad_request, not_found, unauthorized, envelope


class TestResponseEnvelope:
    """Test response envelope functions."""
    
    def test_ok_response(self):
        """Test successful response."""
        response = ok({'message': 'Success'})
        assert response.status_code == 200
        assert response.data['success'] is True
        assert 'data' in response.data
        assert response.data['data']['message'] == 'Success'
        assert 'timestamp' in response.data
    
    def test_ok_response_no_data(self):
        """Test OK response without data."""
        response = ok()
        assert response.status_code == 200
        assert response.data['success'] is True
    
    def test_bad_request(self):
        """Test bad request response."""
        response = bad_request('Invalid input')
        assert response.status_code == 400
        assert response.data['success'] is False
        assert response.data['error'] == 'Invalid input'
    
    def test_not_found(self):
        """Test not found response."""
        response = not_found('Resource not found')
        assert response.status_code == 404
        assert response.data['success'] is False
        assert response.data['error'] == 'Resource not found'
    
    def test_unauthorized(self):
        """Test unauthorized response."""
        response = unauthorized('Authentication required')
        assert response.status_code == 401
        assert response.data['success'] is False
        assert response.data['error'] == 'Authentication required'
    
    def test_envelope_custom_status(self):
        """Test envelope with custom status code."""
        response = envelope(True, data={'id': 1}, status=201)
        assert response.status_code == 201
        assert response.data['success'] is True
    
    def test_timestamp_format(self):
        """Test timestamp is in ISO format."""
        response = ok({'test': 'data'})
        timestamp = response.data['timestamp']
        assert timestamp.endswith('Z')
        # Should be parseable as ISO format
        timezone.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

