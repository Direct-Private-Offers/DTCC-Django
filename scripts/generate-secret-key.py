#!/usr/bin/env python
"""
Generate a Django secret key for use in .env file
Usage: python scripts/generate-secret-key.py
"""
import os
import sys
import django

# Add parent directory to path to import Django settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    from django.core.management.utils import get_random_secret_key
    secret_key = get_random_secret_key()
    print("=" * 60)
    print("Django Secret Key Generated:")
    print("=" * 60)
    print(secret_key)
    print("=" * 60)
    print("\nAdd this to your .env file:")
    print(f"DJANGO_SECRET_KEY={secret_key}")
    print("\n⚠️  Keep this secret! Never commit it to version control.")
except Exception as e:
    # Fallback if Django is not set up
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(alphabet) for i in range(50))
    print("=" * 60)
    print("Django Secret Key Generated (fallback method):")
    print("=" * 60)
    print(secret_key)
    print("=" * 60)
    print("\nAdd this to your .env file:")
    print(f"DJANGO_SECRET_KEY={secret_key}")
    print("\n⚠️  Keep this secret! Never commit it to version control.")

