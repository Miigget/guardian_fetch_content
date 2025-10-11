#!/usr/bin/env python3
"""
Test runner script for Guardian Content Fetcher.

This script provides a convenient way to run different types of tests
with various options and configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description=""):
    """
    Run a shell command and handle errors.
    
    Args:
        command (list): Command to execute
        description (str): Description of what the command does
        
    Returns:
        bool: True if command succeeded, False otherwise
    """
    if description:
        print(f"\n🚀 {description}")
        print("-" * 50)
    
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        print(f"✅ Command completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        return False

def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    command = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        command.append("-v")
    
    if coverage:
        command.extend(["--cov=src/guardian_content_fetcher", "--cov-report=term-missing"])
    
    return run_command(command, "Running unit tests")

def run_linting():
    """Run code linting checks."""
    success = True
    
    # Flake8 for style checking (PEP-8 compliance)
    print("\n🔍 Running Flake8 style checks...")
    flake8_result = run_command(
        ["python", "-m", "flake8", "src/", "tests/"],
        "Checking code style with Flake8"
    )
    success = success and flake8_result
    
    # Black for code formatting check
    print("\n🔍 Running Black format checks...")
    black_result = run_command(
        ["python", "-m", "black", "--check", "src/", "tests/"],
        "Checking code formatting with Black"
    )
    success = success and black_result
    
    return success

# Type checking removed - not required by project specification
# def run_type_checking():
#     """Run static type checking with mypy."""
#     return run_command(
#         ["python", "-m", "mypy", "src/guardian_content_fetcher/", "--ignore-missing-imports"],
#         "Running static type checking with MyPy"
#     )

def run_security_checks():
    """Run security vulnerability checks (required by project spec)."""
    # Bandit for security issues - REQUIRED by task_description_pl.md
    print("\n🔒 Running Bandit security checks...")
    bandit_result = run_command(
        ["python", "-m", "bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json"],
        "Checking for security vulnerabilities with Bandit"
    )
    
    return bandit_result

def run_package_install():
    """Test package installation."""
    return run_command(
        ["python", "-m", "pip", "install", "-e", "."],
        "Testing package installation"
    )

def run_all_checks(verbose=False):
    """Run all quality checks (as required by task_description_pl.md)."""
    print("🧪 Guardian Content Fetcher - Quality Check Suite")
    print("=" * 60)
    print("Required checks: Unit Tests, PEP-8 Compliance, Security")
    print("=" * 60)
    
    checks = [
        ("Package Installation", lambda: run_package_install()),
        ("Unit Tests", lambda: run_unit_tests(verbose=verbose, coverage=True)),
        ("Code Linting (PEP-8)", lambda: run_linting()),
        ("Security Checks", lambda: run_security_checks()),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 Running {check_name}...")
        result = check_func()
        results.append((check_name, result))
        
        if result:
            print(f"✅ {check_name} passed")
        else:
            print(f"❌ {check_name} failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 QUALITY CHECK SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All quality checks passed! Your code is ready for production.")
        return True
    else:
        print("⚠️  Some quality checks failed. Please review and fix the issues.")
        return False

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Test runner for Guardian Content Fetcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all required checks
  python run_tests.py --tests-only       # Run only unit tests
  python run_tests.py --lint-only        # Run only linting (PEP-8)
  python run_tests.py --security-only    # Run only security checks (Bandit)
  python run_tests.py --verbose          # Verbose output
        """
    )
    
    parser.add_argument(
        "--tests-only",
        action="store_true",
        help="Run only unit tests"
    )
    
    parser.add_argument(
        "--lint-only",
        action="store_true",
        help="Run only linting checks"
    )
    
    # Type checking removed - not required by project
    # parser.add_argument(
    #     "--type-check-only",
    #     action="store_true",
    #     help="Run only type checking"
    # )
    
    parser.add_argument(
        "--security-only",
        action="store_true",
        help="Run only security checks"
    )
    
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="Test only package installation"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Include coverage report in tests"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    if project_root.name != "guardian_fetch_content":
        print("❌ Error: This script must be run from the project root directory")
        return 1
    
    success = True
    
    if args.tests_only:
        success = run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.lint_only:
        success = run_linting()
    elif args.security_only:
        success = run_security_checks()
    elif args.install_only:
        success = run_package_install()
    else:
        # Run all required checks
        success = run_all_checks(verbose=args.verbose)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
