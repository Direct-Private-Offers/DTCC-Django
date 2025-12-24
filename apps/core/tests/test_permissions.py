"""
Tests for permission classes.
"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User, Group
from apps.core.permissions import IsInGroup


class TestIsInGroupPermission:
    """Test IsInGroup permission class."""
    
    def test_user_in_required_group(self, api_client):
        """Test user with required group has permission."""
        user = User.objects.create_user(username='test', password='pass')
        group = Group.objects.create(name='issuer')
        user.groups.add(group)
        
        permission = IsInGroup.with_names(['issuer'])
        request = type('Request', (), {'user': user})()
        
        # Mock authenticated user
        request.user.is_authenticated = True
        
        assert permission.has_permission(request, None) is True
    
    def test_user_not_in_required_group(self, api_client):
        """Test user without required group is denied."""
        user = User.objects.create_user(username='test', password='pass')
        
        permission = IsInGroup.with_names(['issuer'])
        request = type('Request', (), {'user': user})()
        request.user.is_authenticated = True
        
        assert permission.has_permission(request, None) is False
    
    def test_user_in_multiple_groups(self, api_client):
        """Test user in one of multiple required groups."""
        user = User.objects.create_user(username='test', password='pass')
        group = Group.objects.create(name='ops')
        user.groups.add(group)
        
        permission = IsInGroup.with_names(['issuer', 'ops'])
        request = type('Request', (), {'user': user})()
        request.user.is_authenticated = True
        
        assert permission.has_permission(request, None) is True
    
    def test_unauthenticated_user(self, api_client):
        """Test unauthenticated user is denied."""
        user = User.objects.create_user(username='test', password='pass')
        user.is_authenticated = False
        
        permission = IsInGroup.with_names(['issuer'])
        request = type('Request', (), {'user': user})()
        
        assert permission.has_permission(request, None) is False

