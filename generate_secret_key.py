#!/usr/bin/env python
"""
Generate a secure Django SECRET_KEY
"""
import secrets
import string

def generate_django_secret_key(length=50):
    """Generate a secure Django secret key with the specified length."""
    # Use Django's recommended character set
    chars = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    # Generate random key
    secret_key = ''.join(secrets.choice(chars) for _ in range(length))
    
    return secret_key

if __name__ == "__main__":
    print("🔐 Generating secure Django SECRET_KEY...")
    print()
    
    # Generate a 50-character secret key
    secret_key = generate_django_secret_key(50)
    
    print("Generated SECRET_KEY:")
    print(f"DJANGO_SECRET_KEY={secret_key}")
    print()
    print("📋 Copy this value and set it as an environment variable in Railway:")
    print(f"   Variable Name: DJANGO_SECRET_KEY")
    print(f"   Variable Value: {secret_key}")
    print()
    print("⚠️  Keep this secret key secure and never commit it to version control!")
