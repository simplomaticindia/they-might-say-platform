"""
Authentication dependencies for FastAPI routes.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models.user import User, UserRole
from auth.security import verify_token

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Authentication error exception."""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionError(HTTPException):
    """Permission error exception."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    
    if not credentials:
        raise AuthenticationError("Missing authentication token")
    
    # Verify token
    payload = verify_token(credentials.credentials, "access")
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User account is disabled")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise AuthenticationError("User account is disabled")
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control."""
    
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_permission(required_role):
            raise PermissionError(
                f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


# Common role dependencies
require_admin = require_role(UserRole.ADMIN)
require_host = require_role(UserRole.HOST)
require_producer = require_role(UserRole.PRODUCER)
require_viewer = require_role(UserRole.VIEWER)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials, "access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None


def check_rate_limit(request: Request) -> bool:
    """Basic rate limiting check (can be enhanced with Redis)."""
    # For now, just return True
    # In production, implement proper rate limiting
    return True


async def validate_request_size(request: Request) -> bool:
    """Validate request size to prevent DoS attacks."""
    content_length = request.headers.get("content-length")
    if content_length:
        # Limit request size to 100MB
        if int(content_length) > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
    return True