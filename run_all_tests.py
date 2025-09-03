#!/usr/bin/env python3
"""
Comprehensive test runner for the They Might Say project.
Runs backend API tests, frontend component tests, and E2E tests.
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple

class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.results: Dict[str, bool] = {}
        
    def run_command(self, command: List[str], cwd: Path, timeout: int = 300) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            print(f"🔄 Running: {' '.join(command)} in {cwd}")
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                print(f"✅ Command succeeded")
                return True, result.stdout
            else:
                print(f"❌ Command failed with exit code {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Command timed out after {timeout} seconds")
            return False, "Command timed out"
        except Exception as e:
            print(f"💥 Command failed with exception: {e}")
            return False, str(e)
    
    def setup_environment(self):
        """Set up test environment variables."""
        print("🔧 Setting up test environment...")
        
        # Backend environment
        os.environ["TESTING"] = "true"
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        os.environ["JWT_SECRET_KEY"] = "test-secret-key"
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        
        # Frontend environment
        os.environ["NEXT_PUBLIC_API_URL"] = "http://localhost:8000"
        os.environ["NEXT_PUBLIC_APP_NAME"] = "They Might Say"
        
        print("✅ Environment setup complete")
    
    def run_backend_tests(self) -> bool:
        """Run backend API tests."""
        print("\n" + "="*60)
        print("🧪 RUNNING BACKEND TESTS")
        print("="*60)
        
        if not self.backend_dir.exists():
            print("❌ Backend directory not found")
            return False
        
        # Install dependencies if needed
        requirements_file = self.backend_dir / "requirements.txt"
        if requirements_file.exists():
            print("📦 Installing backend dependencies...")
            success, _ = self.run_command(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                self.backend_dir
            )
            if not success:
                print("❌ Failed to install backend dependencies")
                return False
        
        # Run tests
        success, output = self.run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            self.backend_dir
        )
        
        self.results["backend_tests"] = success
        return success
    
    def run_frontend_unit_tests(self) -> bool:
        """Run frontend unit tests."""
        print("\n" + "="*60)
        print("🧪 RUNNING FRONTEND UNIT TESTS")
        print("="*60)
        
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        
        # Check if node_modules exists
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            success, _ = self.run_command(["npm", "install"], self.frontend_dir)
            if not success:
                print("❌ Failed to install frontend dependencies")
                return False
        
        # Run Jest tests
        success, output = self.run_command(
            ["npm", "run", "test", "--", "--watchAll=false", "--coverage"],
            self.frontend_dir
        )
        
        self.results["frontend_unit_tests"] = success
        return success
    
    def run_frontend_e2e_tests(self) -> bool:
        """Run frontend E2E tests."""
        print("\n" + "="*60)
        print("🧪 RUNNING FRONTEND E2E TESTS")
        print("="*60)
        
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        
        # Install Playwright browsers if needed
        print("🎭 Installing Playwright browsers...")
        success, _ = self.run_command(
            ["npx", "playwright", "install"],
            self.frontend_dir
        )
        if not success:
            print("⚠️  Failed to install Playwright browsers, continuing anyway...")
        
        # Run E2E tests
        success, output = self.run_command(
            ["npm", "run", "test:e2e"],
            self.frontend_dir,
            timeout=600  # E2E tests can take longer
        )
        
        self.results["frontend_e2e_tests"] = success
        return success
    
    def run_type_checking(self) -> bool:
        """Run TypeScript type checking."""
        print("\n" + "="*60)
        print("🔍 RUNNING TYPE CHECKING")
        print("="*60)
        
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        
        success, output = self.run_command(
            ["npm", "run", "type-check"],
            self.frontend_dir
        )
        
        self.results["type_checking"] = success
        return success
    
    def run_linting(self) -> bool:
        """Run linting checks."""
        print("\n" + "="*60)
        print("🔍 RUNNING LINTING")
        print("="*60)
        
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        
        success, output = self.run_command(
            ["npm", "run", "lint"],
            self.frontend_dir
        )
        
        self.results["linting"] = success
        return success
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        for test_name, passed in self.results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed!")
            return True
        else:
            print("💥 Some tests failed!")
            return False
    
    def run_all_tests(self, skip_e2e: bool = False, skip_backend: bool = False):
        """Run all tests in sequence."""
        print("🚀 Starting comprehensive test suite...")
        print(f"Project root: {self.project_root}")
        
        self.setup_environment()
        
        # Run tests in order
        if not skip_backend:
            self.run_backend_tests()
        
        self.run_type_checking()
        self.run_linting()
        self.run_frontend_unit_tests()
        
        if not skip_e2e:
            self.run_frontend_e2e_tests()
        
        # Print summary
        all_passed = self.print_summary()
        
        return all_passed

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive tests for They Might Say")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E tests")
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend tests")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend tests")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.backend_only:
        runner.setup_environment()
        success = runner.run_backend_tests()
        sys.exit(0 if success else 1)
    elif args.frontend_only:
        runner.setup_environment()
        success = (
            runner.run_type_checking() and
            runner.run_linting() and
            runner.run_frontend_unit_tests() and
            (runner.run_frontend_e2e_tests() if not args.skip_e2e else True)
        )
        sys.exit(0 if success else 1)
    else:
        success = runner.run_all_tests(
            skip_e2e=args.skip_e2e,
            skip_backend=args.skip_backend
        )
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()