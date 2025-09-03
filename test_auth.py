#!/usr/bin/env python3
"""
Simple authentication test script for They Might Say MVP
Tests the core authentication functionality without requiring full Docker setup.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from auth.security import verify_password, get_password_hash, create_access_token, verify_token
from models.user import User
from database import get_db, engine, Base
from sqlalchemy.orm import Session
from services.init_data import create_demo_admin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_password_hashing():
    """Test password hashing and verification."""
    logger.info("Testing password hashing...")
    
    password = "admin123"
    hashed = get_password_hash(password)
    
    # Test correct password
    assert verify_password(password, hashed), "Password verification failed"
    logger.info("✅ Password hashing and verification works")
    
    # Test incorrect password
    assert not verify_password("wrongpassword", hashed), "Password verification should fail for wrong password"
    logger.info("✅ Password verification correctly rejects wrong password")

async def test_jwt_tokens():
    """Test JWT token creation and verification."""
    logger.info("Testing JWT tokens...")
    
    # Create test token
    test_data = {"sub": "admin", "role": "admin"}
    token = create_access_token(data=test_data)
    
    # Verify token
    payload = verify_token(token)
    assert payload is not None, "Token verification failed"
    assert payload.get("sub") == "admin", "Token payload incorrect"
    assert payload.get("role") == "admin", "Token role incorrect"
    
    logger.info("✅ JWT token creation and verification works")

async def test_database_connection():
    """Test database connection and user model."""
    logger.info("Testing database connection...")
    
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Test database session
        db = next(get_db())
        
        # Check if demo admin exists or create it
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            logger.info("Creating demo admin user...")
            await create_demo_admin(db)
            logger.info("✅ Demo admin user created")
        else:
            logger.info("✅ Demo admin user already exists")
        
        # Verify admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        assert admin_user is not None, "Admin user not found"
        assert admin_user.role == "admin", "Admin user role incorrect"
        assert verify_password("admin123", admin_user.password_hash), "Admin password incorrect"
        
        logger.info("✅ Database connection and user model works")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        raise

async def test_authentication_flow():
    """Test complete authentication flow."""
    logger.info("Testing complete authentication flow...")
    
    # This would normally be done via API, but we'll test the core logic
    db = next(get_db())
    
    # Find admin user
    admin_user = db.query(User).filter(User.username == "admin").first()
    assert admin_user is not None, "Admin user not found"
    
    # Verify password
    assert verify_password("admin123", admin_user.password_hash), "Password verification failed"
    
    # Create token
    token_data = {
        "sub": admin_user.username,
        "user_id": str(admin_user.id),
        "role": admin_user.role
    }
    token = create_access_token(data=token_data)
    
    # Verify token
    payload = verify_token(token)
    assert payload is not None, "Token verification failed"
    assert payload.get("sub") == "admin", "Token username incorrect"
    assert payload.get("role") == "admin", "Token role incorrect"
    
    logger.info("✅ Complete authentication flow works")
    
    db.close()

async def main():
    """Run all authentication tests."""
    logger.info("🚀 Starting They Might Say Authentication Tests")
    logger.info("=" * 50)
    
    try:
        # Test password hashing
        await test_password_hashing()
        
        # Test JWT tokens
        await test_jwt_tokens()
        
        # Test database connection
        await test_database_connection()
        
        # Test complete authentication flow
        await test_authentication_flow()
        
        logger.info("=" * 50)
        logger.info("🎉 All authentication tests passed!")
        logger.info("✅ System is ready for deployment")
        
        return True
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"❌ Authentication tests failed: {e}")
        logger.error("🔧 Please check your configuration and try again")
        return False

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)