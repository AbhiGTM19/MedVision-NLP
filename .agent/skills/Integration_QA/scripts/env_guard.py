#!/usr/bin/env python3
"""
Environment Guard — Validates that essential project files exist.
"""
import os
import sys


def check_env():
    """Checks for the existence of critical project files."""
    print("--- 🛡️ Environment Guard ---")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    errors = 0

    required_files = [
        "requirements.txt",
        "pyproject.toml",
        "Dockerfile",
        ".dockerignore",
        "HANDOFF_SCHEMA.json",
        "backend/main.py",
        "backend/schemas/predict.py",
        "backend/api/routes.py",
        "backend/services/model_service.py",
        "backend/core/config.py",
    ]

    for rel_path in required_files:
        full_path = os.path.join(root_dir, rel_path)
        if os.path.exists(full_path):
            print(f"  ✅ {rel_path}")
        else:
            print(f"  ❌ {rel_path} NOT FOUND")
            errors += 1

    if errors == 0:
        print("✅ Environment check complete. All critical files found.")
    else:
        print(f"🚩 FAIL: {errors} critical file(s) missing!")

    return errors


if __name__ == "__main__":
    sys.exit(check_env())
