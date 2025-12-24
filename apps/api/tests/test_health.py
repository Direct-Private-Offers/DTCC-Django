"""
Tests for health check endpoints.
"""
import pytest
from rest_framework.test import APIClient
from django.test import TestCase


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_endpoint(self, api_client):
        """Test basic health check."""
        response = api_client.get('/api/health')
        assert response.status_code == 200
        assert response.data['status'] == 'healthy'
    
    def test_ready_endpoint(self, api_client):
        """Test readiness check."""
        response = api_client.get('/api/ready')
        assert response.status_code == 200
        assert 'database' in response.data
        assert 'cache' in response.data
    
    def test_metrics_endpoint(self, api_client):
        """Test metrics endpoint."""
        response = api_client.get('/api/metrics')
        # Metrics endpoint may require authentication or return different formats
        assert response.status_code in [200, 401, 403]

