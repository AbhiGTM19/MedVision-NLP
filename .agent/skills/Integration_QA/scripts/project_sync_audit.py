#!/usr/bin/env python3
"""
Project Sync Audit — Validates schema ↔ frontend ↔ HANDOFF_SCHEMA alignment.

Extracts Pydantic field names from schemas/predict.py and verifies they appear
in HANDOFF_SCHEMA.json and are correctly referenced in static/script.js.
"""
import ast
import json
import os
import sys


def extract_pydantic_fields(schema_file):
    """Parse a Python file's AST to extract field names from BaseModel classes."""
    with open(schema_file, 'r') as f:
        tree = ast.parse(f.read())

    models = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if any base is BaseModel
            is_basemodel = any(
                (isinstance(b, ast.Name) and b.id == 'BaseModel') or
                (isinstance(b, ast.Attribute) and b.attr == 'BaseModel')
                for b in node.bases
            )
            if is_basemodel:
                fields = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        fields.append(item.target.id)
                models[node.name] = fields
    return models


def sync_boundaries(root_dir):
    """Validates that schema fields are consistently used across boundaries."""
    print("--- 🔄 Project Sync Audit ---")
    errors = 0

    schemas_dir = os.path.join(root_dir, "schemas")
    handoff_path = os.path.join(root_dir, "HANDOFF_SCHEMA.json")
    frontend_js = os.path.join(root_dir, "static", "script.js")

    # 1. Extract Pydantic models
    schema_file = os.path.join(schemas_dir, "predict.py")
    if not os.path.exists(schema_file):
        print(f"⚠️  Schema file not found: {schema_file}")
        return 1

    models = extract_pydantic_fields(schema_file)
    print(f"Found {len(models)} Pydantic model(s): {list(models.keys())}")
    for name, fields in models.items():
        print(f"  {name}: {fields}")

    # 2. Check HANDOFF_SCHEMA.json alignment
    if os.path.exists(handoff_path):
        with open(handoff_path, 'r') as f:
            handoff = json.load(f)

        payload = handoff.get("payload", {})
        input_schema = payload.get("input_schema", {}).get("PredictionRequest", {})
        output_schema = payload.get("output_schema", {}).get("PredictionResponse", {})

        # Check input fields
        req_fields = models.get("PredictionRequest", [])
        for field in req_fields:
            if field not in input_schema:
                print(f"🚩 DRIFT: PredictionRequest.{field} exists in code but missing from HANDOFF_SCHEMA input_schema")
                errors += 1

        # Check output fields
        resp_fields = models.get("PredictionResponse", [])
        for field in resp_fields:
            if field not in output_schema:
                print(f"🚩 DRIFT: PredictionResponse.{field} exists in code but missing from HANDOFF_SCHEMA output_schema")
                errors += 1

        print(f"HANDOFF_SCHEMA alignment: {'✅ PASS' if errors == 0 else '🚩 FAIL'}")
    else:
        print("⚠️  HANDOFF_SCHEMA.json not found. Skipping handoff check.")

    # 3. Check frontend references
    if os.path.exists(frontend_js):
        with open(frontend_js, 'r') as f:
            js_content = f.read()

        req_fields = models.get("PredictionRequest", [])
        for field in req_fields:
            if field not in js_content:
                print(f"🚩 DRIFT: PredictionRequest.{field} not found in static/script.js")
                errors += 1
            else:
                print(f"  ✅ Frontend references '{field}'")
    else:
        print("⚠️  static/script.js not found. Skipping frontend check.")

    if errors == 0:
        print("✅ PASS: No schema drift detected.")
    else:
        print(f"🚩 FAIL: {errors} schema drift(s) detected!")

    return errors


if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    sys.exit(sync_boundaries(root_dir))
