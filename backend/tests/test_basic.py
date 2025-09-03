"""Basic tests to verify setup."""

import pytest
import os


def test_basic_imports():
    """Test that we can import core modules."""
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core dependencies: {e}")


def test_environment_setup():
    """Test environment setup."""
    # These should be set by conftest.py
    assert os.environ.get("TESTING") == "true"
    assert os.environ.get("JWT_SECRET_KEY") == "test-secret-key"
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"


def test_fastapi_basic():
    """Test basic FastAPI functionality."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    # Create a simple test app
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_pydantic_models():
    """Test Pydantic model creation."""
    from pydantic import BaseModel
    
    class TestModel(BaseModel):
        name: str
        value: int
    
    model = TestModel(name="test", value=42)
    assert model.name == "test"
    assert model.value == 42


def test_sqlalchemy_basic():
    """Test SQLAlchemy basic functionality."""
    from sqlalchemy import create_engine, Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    
    Base = declarative_base()
    
    class TestTable(Base):
        __tablename__ = "test_table"
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
    
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Test basic operations
    test_item = TestTable(name="test")
    session.add(test_item)
    session.commit()
    
    result = session.query(TestTable).first()
    assert result.name == "test"
    
    session.close()