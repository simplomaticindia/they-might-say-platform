#!/usr/bin/env python3
"""Test runner script for the backend API."""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests with coverage reporting."""
    
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🧪 Running Backend API Tests...")
    print("=" * 50)
    
    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-exclude=tests/*",
        "--cov-exclude=alembic/*",
        "--cov-exclude=venv/*",
        "--cov-exclude=__pycache__/*"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/index.html")
        else:
            print(f"\n❌ Tests failed with exit code {result.returncode}")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest not found. Please install test dependencies:")
        print("pip install pytest pytest-asyncio pytest-cov")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_specific_test(test_path):
    """Run a specific test file or test function."""
    
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print(f"🧪 Running specific test: {test_path}")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        return run_specific_test(test_path)
    else:
        # Run all tests
        return run_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)