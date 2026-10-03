#!/usr/bin/env python
"""
Quick start script for Network Monitor.
Run this to verify installation and get started quickly.
"""

import sys
import os
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.12+."""
    if sys.version_info < (3, 12):
        print("❌ Python 3.12+ required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_requirements():
    """Check if requirements are installed."""
    try:
        import flask
        import requests
        import psutil
        import schedule
        print("✅ All required packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False


def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("   Creating from .env.example...")
        try:
            import shutil
            shutil.copy(".env.example", ".env")
            print("   ✅ Created .env file")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create .env: {e}")
            return False


def main():
    """Run startup checks."""
    print("\n" + "=" * 50)
    print("Network Monitor - Quick Start")
    print("=" * 50 + "\n")

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_requirements),
        ("Environment", check_env_file),
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        if not check_func():
            all_passed = False

    print("\n" + "=" * 50)

    if not all_passed:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nSetup Instructions:")
        print("1. Install Python 3.12+: https://www.python.org/downloads/")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Create .env file: cp .env.example .env")
        return 1

    print("✅ All checks passed!")
    print("\nNext Steps:")
    print("=" * 50)
    print("\n1. EDIT CONFIGURATION")
    print("   Edit .env file with your settings (especially ROUTER_IP)")
    print("\n2. START MONITOR (Terminal 1)")
    print("   python monitor.py")
    print("\n3. START FLASK APP (Terminal 2)")
    print("   python app.py")
    print("\n4. OPEN DASHBOARD")
    print("   http://localhost:5000")
    print("\n" + "=" * 50 + "\n")

    print("DOCKER ALTERNATIVE:")
    print("  docker-compose up -d\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
