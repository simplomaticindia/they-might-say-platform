"""
Authentication API endpoints.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from database import get_db
from models.user import User, UserRole
from auth.security import (
    authenticate_user, 
    create_user_tokens, 
    get_password_hash,
    verify_token,
    validate_password_strength,
    SECURITY_HEADERS
)
from auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response
class UserLogin(BaseModel):
    """User login request model."""
    username: str
    password: str


class UserCreate(BaseModel):
    """User creation request model."""
    username: str
    email: EmailStr
    name: str
    password: str
    role: UserRole = UserRole.VIEWER
    
    @validator('password')
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                'Password must be at least 8 characters with uppercase, lowercase, and digit'
            )
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()


class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: str
    name: str
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    created_at: str
    last_login: Optional[str]


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    response: Response = None
):
    """Authenticate user and return tokens."""
    
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    tokens = create_user_tokens(user)
    
    # Add security headers
    if response:
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
    
    return TokenResponse(
        **tokens,
        user=UserResponse(**user.to_dict())
    )


@router.post("/login-json", response_model=TokenResponse)
async def login_json(
    login_data: UserLogin,
    db: Session = Depends(get_db),
    response: Response = None
):
    """Authenticate user with JSON payload."""
    
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    tokens = create_user_tokens(user)
    
    # Add security headers
    if response:
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
    
    return TokenResponse(
        **tokens,
        user=UserResponse(**user.to_dict())
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Get user
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new tokens
    tokens = create_user_tokens(user)
    
    return TokenResponse(
        **tokens,
        user=UserResponse(**user.to_dict())
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    response: Response = None
):
    """Logout user (client should discard tokens)."""
    
    # In a production system, you might want to blacklist the token
    # For now, we just return success and let the client handle token removal
    
    if response:
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse(**current_user.to_dict())


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # Only admins can create users
):
    """Register a new user (admin only)."""
    
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=True,
        is_verified=True,  # Auto-verify admin-created users
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(**new_user.to_dict())


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users (admin only)."""
    
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse(**user.to_dict()) for user in users]


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user (admin only)."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update allowed fields
    allowed_fields = ['name', 'email', 'role', 'is_active', 'is_verified']
    for field, value in user_data.items():
        if field in allowed_fields and hasattr(user, field):
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(**user.to_dict())


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete user (admin only)."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}