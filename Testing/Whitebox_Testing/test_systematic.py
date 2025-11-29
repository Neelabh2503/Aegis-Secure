"""
Systematic Test Runner - Check and Fix Tests Module by Module

Usage:
    python test_systematic.py <module_name>
    
Examples:
    python test_systematic.py config     # Test config.py
    python test_systematic.py validators # Test validators.py
    python test_systematic.py errors     # Test errors.py
    python test_systematic.py auth       # Test auth routes
    python test_systematic.py all        # Run all tests
"""
import subprocess
import sys
import os
import argparse

# Add refactored backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'AegisSecureRefactored', 'Backend'))
sys.path.insert(0, backend_path)


MODULES = {
    # Core Infrastructure (Unit Tests - Priority HIGH)
    "config": {
        "test_file": "tests/test_config.py",
        "source": "config.py",
        "description": "Configuration Management",
        "priority": "HIGH",
        "type": "unit"
    },
    "validators": {
        "test_file": "tests/test_validators.py",
        "source": "validators.py",
        "description": "Input Validation",
        "priority": "HIGH",
        "type": "unit"
    },
    "errors": {
        "test_file": "tests/test_errors.py",
        "source": "errors.py",
        "description": "Error Handling",
        "priority": "HIGH",
        "type": "unit"
    },
    
    # Route Tests (Unit Tests - Priority HIGH)
    "routes_auth": {
        "test_file": "tests/test_routes_auth.py",
        "source": "routes/auth.py",
        "description": "Authentication Routes",
        "priority": "HIGH",
        "type": "unit"
    },
    "routes_sms": {
        "test_file": "tests/test_routes_sms.py",
        "source": "routes/sms.py",
        "description": "SMS Synchronization",
        "priority": "HIGH",
        "type": "unit"
    },
    "routes_gmail": {
        "test_file": "tests/test_routes_gmail.py",
        "source": "routes/gmail.py",
        "description": "Gmail Integration",
        "priority": "HIGH",
        "type": "unit"
    },
    "routes_oauth": {
        "test_file": "tests/test_routes_oauth.py",
        "source": "routes/Oauth.py",
        "description": "OAuth Flow",
        "priority": "HIGH",
        "type": "unit"
    },
    
    # Route Tests (Unit Tests - Priority MEDIUM)
    "routes_notifications": {
        "test_file": "tests/test_routes_notifications.py",
        "source": "routes/notifications.py",
        "description": "Notification Handling",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "routes_dashboard": {
        "test_file": "tests/test_routes_dashboard.py",
        "source": "routes/dashboard.py",
        "description": "Dashboard Statistics",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "routes_analysis": {
        "test_file": "tests/test_routes_analysis.py",
        "source": "routes/analysis.py",
        "description": "ML Analysis Endpoints",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "routes_fcm": {
        "test_file": "tests/test_routes_fcm.py",
        "source": "routes/fcm_service.py",
        "description": "Firebase Cloud Messaging",
        "priority": "MEDIUM",
        "type": "unit"
    },
    
    # Integration Tests (Priority MEDIUM)
    "middleware": {
        "test_file": "tests/test_middleware.py",
        "source": "middleware.py",
        "description": "Security Middleware",
        "priority": "MEDIUM",
        "type": "integration"
    },
    "main": {
        "test_file": "tests/test_main.py",
        "source": "main.py",
        "description": "Application Entry Point",
        "priority": "MEDIUM",
        "type": "integration"
    },
    
    # Models (Unit Tests - Priority HIGH)
    "models": {
        "test_file": "tests/test_models.py",
        "source": "models.py",
        "description": "Pydantic Models",
        "priority": "HIGH",
        "type": "unit"
    },
    
    # Utility Tests (Unit Tests - Priority MEDIUM)
    "utils_password": {
        "test_file": "tests/test_utils_password.py",
        "source": "utils/password_utils.py",
        "description": "Password Utilities",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "utils_format": {
        "test_file": "tests/test_utils_format.py",
        "source": "utils/format_utils.py",
        "description": "Format Utilities",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "utils_color": {
        "test_file": "tests/test_utils_color.py",
        "source": "utils/Color_decoration_utils.py",
        "description": "Color Decoration Utilities",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "utils_jwt": {
        "test_file": "tests/test_utils_jwt.py",
        "source": "utils/jwt_utils.py",
        "description": "JWT Utilities",
        "priority": "HIGH",
        "type": "unit"
    },
    "utils_access_token": {
        "test_file": "tests/test_utils_access_token.py",
        "source": "utils/access_token_util.py",
        "description": "Access Token Utilities",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "utils_otp": {
        "test_file": "tests/test_utils_otp.py",
        "source": "utils/otp_utils.py",
        "description": "OTP Utilities",
        "priority": "HIGH",
        "type": "unit"
    },
    "utils_user_info": {
        "test_file": "tests/test_utils_user_info.py",
        "source": "utils/user_info_utils.py",
        "description": "User Info Utilities",
        "priority": "MEDIUM",
        "type": "unit"
    },
    "utils_spam_prediction": {
        "test_file": "tests/test_utils_spam_prediction.py",
        "source": "utils/SpamPrediction_utils.py",
        "description": "Spam Prediction Utilities",
        "priority": "LOW",
        "type": "unit"
    },
    "utils_dashboard": {
        "test_file": "tests/test_utils_dashboard.py",
        "source": "utils/dashboard_utils.py",
        "description": "Dashboard Utilities",
        "priority": "LOW",
        "type": "unit"
    },
    "utils_get_email": {
        "test_file": "tests/test_utils_get_email.py",
        "source": "utils/get_email_utils.py",
        "description": "Get Email Utilities",
        "priority": "LOW",
        "type": "unit"
    }
}


def print_header(text, char="="):
    """Print a formatted header."""
    print(f"\n{char * 80}")
    print(f"  {text}")
    print(f"{char * 80}\n")


def run_module_tests(module_name, verbose=True):
    """Run tests for a specific module."""
    if module_name not in MODULES:
        print(f"❌ Unknown module: {module_name}")
        print(f"Available modules: {', '.join(MODULES.keys())}")
        return False
    
    module = MODULES[module_name]
    
    print_header(f"Testing: {module['description']}")
    print(f"📁 Source File:  {module['source']}")
    print(f"🧪 Test File:    {module['test_file']}")
    print(f"📊 Type:         {module['type'].upper()}")
    print(f"⚡ Priority:     {module['priority']}")
    print()
    
    # Run pytest
    cmd = [
        sys.executable, "-m", "pytest",
        module['test_file'],
        "-v" if verbose else "-q",
        "--tb=short",
        "--no-header"
    ]
    
    print(f"🚀 Running: pytest {module['test_file']} -v --tb=short\n")
    result = subprocess.run(cmd, capture_output=False)
    
    return result.returncode == 0


def show_test_status():
    """Show current test status for all modules."""
    print_header("📊 AegisSecure Backend - Test Status Dashboard", "=")
    
    print(f"{'Module':<15} {'Type':<12} {'Priority':<10} {'Test File':<30}")
    print("-" * 80)
    
    for name, info in MODULES.items():
        print(f"{name:<15} {info['type']:<12} {info['priority']:<10} {info['test_file']:<30}")
    
    print("\n" + "=" * 80)
    print("Usage: python test_systematic.py <module_name>")
    print("Example: python test_systematic.py config")
    print("=" * 80)


def run_all_tests():
    """Run all tests sequentially."""
    print_header("🧪 Running All Tests Systematically", "=")
    
    results = {}
    
    # Run by priority: HIGH first
    high_priority = [name for name, info in MODULES.items() if info['priority'] == 'HIGH']
    medium_priority = [name for name, info in MODULES.items() if info['priority'] == 'MEDIUM']
    
    all_modules = high_priority + medium_priority
    
    for i, module_name in enumerate(all_modules, 1):
        print(f"\n[{i}/{len(all_modules)}] ", end="")
        passed = run_module_tests(module_name, verbose=False)
        results[module_name] = passed
        
        if not passed:
            print(f"\n⚠️  {module_name} tests failed. Stopping here for review.")
            print(f"Fix issues, then run: python test_systematic.py {module_name}")
            break
    
    # Summary
    print_header("📊 Test Summary", "=")
    
    for module_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status:<12} {module_name:<15} - {MODULES[module_name]['description']}")
    
    total = len(results)
    passed_count = sum(1 for p in results.values() if p)
    
    print(f"\n{'='*80}")
    print(f"Results: {passed_count}/{total} modules passed")
    print(f"{'='*80}")
    
    return all(results.values())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Systematic test runner for AegisSecure Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_systematic.py config      # Test config module
  python test_systematic.py validators  # Test validators module
  python test_systematic.py all         # Run all tests
  python test_systematic.py --list      # Show all modules
        """
    )
    
    parser.add_argument(
        'module',
        nargs='?',
        help='Module to test (config, validators, errors, auth, etc.) or "all"'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available modules'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Less verbose output'
    )
    
    args = parser.parse_args()
    
    if args.list or not args.module:
        show_test_status()
        return 0
    
    if args.module == "all":
        success = run_all_tests()
        return 0 if success else 1
    
    success = run_module_tests(args.module, verbose=not args.quiet)
    
    if success:
        print_header(f"✅ {args.module.upper()} - All Tests Passed!", "=")
        
        # Suggest next module
        module_list = list(MODULES.keys())
        current_idx = module_list.index(args.module)
        if current_idx < len(module_list) - 1:
            next_module = module_list[current_idx + 1]
            print(f"Next: python test_systematic.py {next_module}")
        else:
            print("🎉 All modules tested! Run: python test_systematic.py all")
        
        return 0
    else:
        print_header(f"❌ {args.module.upper()} - Some Tests Failed", "=")
        print("Review failures above and fix issues in:")
        print(f"  - Source: {MODULES[args.module]['source']}")
        print(f"  - Tests:  {MODULES[args.module]['test_file']}")
        print(f"\nRe-run: python test_systematic.py {args.module}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
