"""
Test Runner für Live Recorder Tests

Usage:
    python -m pytest tests/live_recorder/ -v
    python -m pytest tests/live_recorder/ -v --cov=live_recorder --cov-report=html
    python tests/live_recorder/run_tests.py
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """
    Führt alle Live Recorder Tests aus
    """
    
    # Workspace Root finden
    workspace_root = Path(__file__).parent.parent.parent
    test_dir = workspace_root / "tests" / "live_recorder"
    
    print("=" * 70)
    print("Live Recorder Test Suite")
    print("=" * 70)
    print(f"Workspace: {workspace_root}")
    print(f"Test Dir:  {test_dir}")
    print("=" * 70)
    
    # Test Command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ]
    
    print(f"\nRunning: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, cwd=str(workspace_root))
        return result.returncode
    except FileNotFoundError:
        print("\n❌ pytest nicht gefunden!")
        print("   Install mit: pip install pytest")
        return 1


def run_tests_with_coverage():
    """
    Führt Tests mit Coverage-Report aus
    """
    
    workspace_root = Path(__file__).parent.parent.parent
    test_dir = workspace_root / "tests" / "live_recorder"
    
    print("=" * 70)
    print("Live Recorder Test Suite (mit Coverage)")
    print("=" * 70)
    
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "-s",
        "--cov=live_recorder",
        "--cov-report=term-missing",
        "--cov-report=html"
    ]
    
    print(f"\nRunning: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, cwd=str(workspace_root))
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("✅ Alle Tests bestanden!")
            print("📊 Coverage Report: htmlcov/index.html")
            print("=" * 70)
        
        return result.returncode
        
    except FileNotFoundError:
        print("\n❌ pytest oder pytest-cov nicht gefunden!")
        print("   Install mit: pip install pytest pytest-cov")
        return 1


if __name__ == "__main__":
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Live Recorder Test Runner")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run specific test file (e.g., test_happy_path.py)"
    )
    
    args = parser.parse_args()
    
    if args.test:
        # Run specific test
        workspace_root = Path(__file__).parent.parent.parent
        test_file = workspace_root / "tests" / "live_recorder" / args.test
        
        cmd = [sys.executable, "-m", "pytest", str(test_file), "-v", "-s"]
        print(f"Running: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, cwd=str(workspace_root))
        sys.exit(result.returncode)
    
    elif args.coverage:
        sys.exit(run_tests_with_coverage())
    
    else:
        sys.exit(run_tests())
