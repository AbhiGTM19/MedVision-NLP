#!/usr/bin/env python3
"""
Project Sync Audit — Validates schema ↔ frontend ↔ HANDOFF_SCHEMA alignment.

Extracts Pydantic field names from backend/schemas/predict.py and knowledge.py,
verifies they appear in HANDOFF_SCHEMA.json, checks frontend JS paths, 
and validates API route and singleton parity using AST.
"""
import ast
import json
import os
import sys


def extract_pydantic_fields(schema_file):
    """Parse a Python file's AST to extract field names from BaseModel classes."""
    if not os.path.exists(schema_file):
        return {}
        
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


def extract_routes(routes_file):
    """Parse routes.py to extract all @router.get/post endpoints."""
    if not os.path.exists(routes_file):
        return []
        
    with open(routes_file, 'r') as f:
        tree = ast.parse(f.read())
        
    endpoints = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute) and decorator.func.value.id == 'router':
                        if decorator.func.attr in ('get', 'post'):
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                endpoints.append(decorator.args[0].value)
    return endpoints


def extract_singleton_imports(routes_file):
    """Check that singleton services are imported in routes.py."""
    if not os.path.exists(routes_file):
        return []
        
    with open(routes_file, 'r') as f:
        tree = ast.parse(f.read())
        
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == 'services.model_service':
                for alias in node.names:
                    if alias.name == 'model_service':
                        imported.append('model_service')
            elif node.module == 'services.knowledge_service':
                for alias in node.names:
                    if alias.name == 'knowledge_service':
                        imported.append('knowledge_service')
            elif node.module == 'services.llm_service':
                for alias in node.names:
                    if alias.name == 'llm_service':
                        imported.append('llm_service')
    return imported


def sync_boundaries(root_dir):
    """Validates that schema fields, routes, and services are consistently used across boundaries."""
    print("--- 🔄 Project Sync Audit ---")
    errors = 0

    schemas_dir = os.path.join(root_dir, "backend", "schemas")
    handoff_path = os.path.join(root_dir, "HANDOFF_SCHEMA.json")
    frontend_js = os.path.join(root_dir, "frontend", "static", "js", "script.js")
    frontend_chat_js = os.path.join(root_dir, "frontend", "static", "js", "chat_script.js")
    routes_file = os.path.join(root_dir, "backend", "api", "routes.py")

    # 1. Extract Pydantic models
    predict_file = os.path.join(schemas_dir, "predict.py")
    knowledge_file = os.path.join(schemas_dir, "knowledge.py")
    
    models = {}
    models.update(extract_pydantic_fields(predict_file))
    models.update(extract_pydantic_fields(knowledge_file))
    
    print(f"Found {len(models)} Pydantic model(s): {list(models.keys())}")
    for name, fields in models.items():
        print(f"  {name}: {fields}")

    # 2. Check HANDOFF_SCHEMA.json alignment
    handoff_endpoints = []
    if os.path.exists(handoff_path):
        with open(handoff_path, 'r') as f:
            handoff = json.load(f)

        payload = handoff.get("payload", {})
        input_schema = payload.get("input_schema", {}).get("PredictionRequest", {})
        output_schema = payload.get("output_schema", {}).get("PredictionResponse", {})
        rag_output_schema = payload.get("output_schema", {}).get("PredictionRAGResponse", {})
        
        handoff_endpoints = list(payload.get("api_endpoints", {}).values())

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
                
        rag_resp_fields = models.get("PredictionRAGResponse", [])
        for field in rag_resp_fields:
            if field not in rag_output_schema:
                print(f"🚩 DRIFT: PredictionRAGResponse.{field} exists in code but missing from HANDOFF_SCHEMA output_schema")
                errors += 1

        print(f"HANDOFF_SCHEMA schema alignment: {'✅ PASS' if errors == 0 else '🚩 FAIL'}")
    else:
        print("⚠️  HANDOFF_SCHEMA.json not found. Skipping handoff check.")

    # 3. Check Route Alignment
    if os.path.exists(routes_file):
        code_endpoints = extract_routes(routes_file)
        
        # Strip annotations from handoff endpoints for comparison
        clean_handoff_endpoints = []
        for ep in handoff_endpoints:
            # Strip " (DEPRECATED)" or other annotations
            clean_ep = ep.split(" ")[0]
            clean_handoff_endpoints.append(clean_ep)
            
        for ep in code_endpoints:
            if ep not in clean_handoff_endpoints:
                print(f"🚩 ROUTE DRIFT: Endpoint {ep} exists in routes.py but missing from HANDOFF_SCHEMA.json")
                errors += 1
                
        for ep, clean_ep in zip(handoff_endpoints, clean_handoff_endpoints):
            if clean_ep not in code_endpoints:
                print(f"🚩 ROUTE DRIFT: Endpoint {ep} in HANDOFF_SCHEMA.json missing from routes.py")
                errors += 1
                
        print(f"Route alignment: {'✅ PASS' if errors == 0 else '🚩 FAIL'}")
        
        # Check Singleton Imports
        singletons = extract_singleton_imports(routes_file)
        if "model_service" not in singletons:
            print("🚩 SINGLETON DRIFT: model_service not imported in routes.py")
            errors += 1
        if "llm_service" not in singletons:
            print("🚩 SINGLETON DRIFT: llm_service not imported in routes.py")
            errors += 1
            
        print(f"Singleton import alignment: {'✅ PASS' if errors == 0 else '🚩 FAIL'}")
    else:
        print("⚠️  backend/api/routes.py not found. Skipping route/singleton check.")

    # 4. Check frontend references
    frontend_checked = False
    
    if os.path.exists(frontend_js):
        with open(frontend_js, 'r') as f:
            js_content = f.read()

        req_fields = models.get("PredictionRequest", [])
        for field in req_fields:
            if field not in js_content:
                print(f"🚩 DRIFT: PredictionRequest.{field} not found in frontend/static/js/script.js")
                errors += 1
            else:
                print(f"  ✅ Frontend script.js references '{field}'")
        frontend_checked = True
                
    if os.path.exists(frontend_chat_js):
        with open(frontend_chat_js, 'r') as f:
            chat_js_content = f.read()
            
        chat_req_fields = models.get("ChatRequest", [])
        for field in chat_req_fields:
            if field not in chat_js_content:
                print(f"🚩 DRIFT: ChatRequest.{field} not found in frontend/static/js/chat_script.js")
                errors += 1
            else:
                print(f"  ✅ Frontend chat_script.js references '{field}'")
        frontend_checked = True
                
    if not frontend_checked:
        print("⚠️  frontend/static/js/*.js not found. Skipping frontend check.")

    if errors == 0:
        print("✅ PASS: No project sync drift detected.")
    else:
        print(f"🚩 FAIL: {errors} sync drift(s) detected!")

    return errors


if __name__ == "__main__":
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    sys.exit(sync_boundaries(root_dir))
