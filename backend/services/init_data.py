"""
Initialize demo data and default accounts.
"""
import logging
from sqlalchemy.orm import Session

from database import SessionLocal
from models.user import User, UserRole
from auth.security import get_password_hash

logger = logging.getLogger(__name__)


async def create_demo_admin():
    """Create demo admin account if it doesn't exist."""
    
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if admin_user:
            logger.info("Demo admin account already exists")
            return admin_user
        
        # Create demo admin account
        hashed_password = get_password_hash("admin123")
        
        admin_user = User(
            username="admin",
            email="admin@theymightsay.com",
            name="System Administrator",
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info("Demo admin account created successfully")
        logger.info("Username: admin")
        logger.info("Password: admin123")
        logger.warning("SECURITY: Change default admin password in production!")
        
        return admin_user
        
    except Exception as e:
        logger.error(f"Error creating demo admin account: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def create_sample_users():
    """Create sample users for testing (optional)."""
    
    db = SessionLocal()
    try:
        sample_users = [
            {
                "username": "host_demo",
                "email": "host@theymightsay.com",
                "name": "Demo Host",
                "password": "host123",
                "role": UserRole.HOST,
            },
            {
                "username": "producer_demo",
                "email": "producer@theymightsay.com",
                "name": "Demo Producer",
                "password": "producer123",
                "role": UserRole.PRODUCER,
            },
            {
                "username": "viewer_demo",
                "email": "viewer@theymightsay.com",
                "name": "Demo Viewer",
                "password": "viewer123",
                "role": UserRole.VIEWER,
            },
        ]
        
        for user_data in sample_users:
            # Check if user already exists
            existing_user = db.query(User).filter(
                User.username == user_data["username"]
            ).first()
            
            if existing_user:
                continue
            
            # Create user
            hashed_password = get_password_hash(user_data["password"])
            
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                name=user_data["name"],
                hashed_password=hashed_password,
                role=user_data["role"],
                is_active=True,
                is_verified=True,
            )
            
            db.add(user)
        
        db.commit()
        logger.info("Sample users created successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample users: {e}")
        db.rollback()
        raise
    finally:
        db.close()