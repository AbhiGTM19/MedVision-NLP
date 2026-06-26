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
        "backend/requirements.txt",
        "backend/pyproject.toml",
        "Dockerfile",
        ".dockerignore",
        "HANDOFF_SCHEMA.json",
        "backend/main.py",
        "backend/schemas/predict.py",
        "backend/api/routes.py",
        "backend/services/model_service.py",
        "backend/services/knowledge_service.py",
        "backend/services/llm_service.py",
        "backend/core/config.py",
        "backend/schemas/knowledge.py",
        "backend/core/prompts.py",
        "backend/core/rate_limiter.py",
        "backend/core/utils.py",
        "backend/tests/test_api.py",
    ]

    required_directories = [
        "backend/core/architectures",
        "backend/scripts",
        "backend/scripts/data_preparation",
        "backend/scripts/evaluation",
        "backend/tests",
        "backend/notebooks",
    ]

    for rel_path in required_files:
        full_path = os.path.join(root_dir, rel_path)
        if os.path.exists(full_path):
            print(f"  ✅ {rel_path}")
        else:
            print(f"  ❌ {rel_path} NOT FOUND")
            errors += 1

    for rel_path in required_directories:
        full_path = os.path.join(root_dir, rel_path)
        if os.path.isdir(full_path):
            print(f"  ✅ {rel_path}/")
        else:
            print(f"  ❌ {rel_path}/ NOT FOUND")
            errors += 1

    env_path = os.path.join(root_dir, "backend", ".env")
    if not os.path.exists(env_path):
        print("  ⚠️ backend/.env NOT FOUND (Required at runtime for GEMINI_API_KEY)")

    if errors == 0:
        print("✅ Environment check complete. All critical files and directories found.")
    else:
        print(f"🚩 FAIL: {errors} critical item(s) missing!")

    return errors


if __name__ == "__main__":
    sys.exit(check_env())
