"""Test configuration and fixtures."""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator

# Set environment variables before importing anything else
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["OPENAI_API_KEY"] = "test-openai-key"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Commented out for basic testing - uncomment when app is ready
# from main import app
# from database.connection import get_db, Base
# from core.auth import create_access_token
# from models.user import User, UserRole, SubscriptionTier

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Commented out for basic testing - uncomment when app is ready
# @pytest.fixture(scope="function")
# def db_session():
#     """Create a fresh database session for each test."""
#     Base.metadata.create_all(bind=engine)
#     session = TestingSessionLocal()
#     try:
#         yield session
#     finally:
#         session.close()
#         Base.metadata.drop_all(bind=engine)


# @pytest.fixture(scope="function")
# def client(db_session):
#     """Create a test client with database dependency override."""
#     def override_get_db():
#         try:
#             yield db_session
#         finally:
#             pass

#     app.dependency_overrides[get_db] = override_get_db
    
#     with TestClient(app) as test_client:
#         yield test_client
    
#     app.dependency_overrides.clear()


# Commented out for basic testing - uncomment when models are ready
# @pytest.fixture
# def test_user(db_session) -> User:
#     """Create a test user."""
#     user = User(
#         username="testuser",
#         email="test@example.com",
#         hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
#         full_name="Test User",
#         role=UserRole.HOST,
#         subscription_tier=SubscriptionTier.PREMIUM
#     )
#     db_session.add(user)
#     db_session.commit()
#     db_session.refresh(user)
#     return user


# @pytest.fixture
# def admin_user(db_session) -> User:
#     """Create an admin test user."""
#     user = User(
#         username="admin",
#         email="admin@example.com",
#         hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
#         full_name="Admin User",
#         role=UserRole.ADMIN,
#         subscription_tier=SubscriptionTier.ENTERPRISE
#     )
#     db_session.add(user)
#     db_session.commit()
#     db_session.refresh(user)
#     return user


# @pytest.fixture
# def auth_headers(test_user) -> dict:
#     """Create authentication headers for test user."""
#     token = create_access_token(data={"sub": test_user.username})
#     return {"Authorization": f"Bearer {token}"}


# @pytest.fixture
# def admin_headers(admin_user) -> dict:
#     """Create authentication headers for admin user."""
#     token = create_access_token(data={"sub": admin_user.username})
#     return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "This is a test PDF document.")
    p.drawString(100, 730, "It contains sample text for testing purposes.")
    p.drawString(100, 710, "Abraham Lincoln was the 16th President of the United States.")
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing."""
    import io
    
    content = """
    Abraham Lincoln was born on February 12, 1809, in a log cabin in Kentucky.
    He became the 16th President of the United States in 1861.
    Lincoln led the nation through the American Civil War and worked to end slavery.
    He was assassinated by John Wilkes Booth on April 14, 1865.
    """
    
    return io.StringIO(content)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "I appreciate your question about the challenges of preserving the Union. During those tumultuous times, I believed that a house divided against itself cannot stand. The preservation of our Union required both firmness in principle and compassion for all Americans, even those who opposed us."
                }
            }
        ],
        "usage": {
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_embedding_response():
    """Mock OpenAI embedding response."""
    return {
        "data": [
            {
                "embedding": [0.1] * 1536  # Mock 1536-dimensional embedding
            }
        ]
    }


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]