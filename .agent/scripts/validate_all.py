#!/usr/bin/env python3
import ast
import glob
import json
import os
import re
import sys

MANDATORY_SECTIONS = [
    "## 1. Target Components:",
    "## 2. Source of Truth Mappings:",
    "## 3. Tooling Requirements:",
    "## 4. Strict Workflow Rules:",
    "## 5. Domain-Specific Rules:",
    "## 6. Karpathy Execution Protocol:",
    "## 7. Collaboration & Hand-offs:",
    "## 8. Troubleshooting Decision Tree:",
    "## 9. Strict Output Formats:",
    "## Initial Acknowledgment",
]

def extract_routes(routes_file):
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

def extract_singleton_assignments(service_file, expected_name, expected_class):
    if not os.path.exists(service_file):
        return False
    with open(service_file, 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == expected_name:
                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name) and node.value.func.id == expected_class:
                            return True
    return False

def validate_all():
    print("Starting Global Ecosystem Validation...")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    agent_dir = os.path.join(root_dir, ".agent")
    
    errors = 0
    warnings = 0
    
    # ── Phase 1: JSON Linting ──
    print("\n─── Phase 1: JSON Linting ───")
    json_files = glob.glob(os.path.join(agent_dir, "**", "*.json"), recursive=True)
    for j_file in json_files:
        try:
            with open(j_file, 'r') as f:
                json.load(f)
            print(f"  PASS: {os.path.relpath(j_file, root_dir)}")
        except Exception as e:
            print(f"  FAIL: {os.path.relpath(j_file, root_dir)}: {e}")
            errors += 1

    handoff_path = os.path.join(root_dir, "HANDOFF_SCHEMA.json")
    if os.path.exists(handoff_path):
        try:
            with open(handoff_path, 'r') as f:
                json.load(f)
            print("  PASS: HANDOFF_SCHEMA.json")
        except Exception as e:
            print(f"  FAIL: HANDOFF_SCHEMA.json: {e}")
            errors += 1
    else:
        print("  FAIL: HANDOFF_SCHEMA.json not found at project root!")
        errors += 1

    # ── Phase 2: SKILL.md 9-Section Compliance ──
    print("\n─── Phase 2: SKILL.md 9-Section Compliance ───")
    skill_files = glob.glob(os.path.join(agent_dir, "skills", "**", "SKILL.md"), recursive=True)
    for s_file in skill_files:
        rel_path = os.path.relpath(s_file, root_dir)
        with open(s_file, 'r') as f:
            content = f.read()
        
        missing = []
        for section in MANDATORY_SECTIONS:
            if section not in content:
                missing.append(section)
        
        if missing:
            print(f"  FAIL: {rel_path} missing sections: {missing}")
            errors += 1
        else:
            print(f"  PASS: {rel_path} (all 9 sections + acknowledgment)")

    # ── Phase 3: YAML Frontmatter Validation ──
    print("\n─── Phase 3: YAML Frontmatter Validation ───")
    all_md_with_frontmatter = skill_files + glob.glob(os.path.join(agent_dir, "rules", "*.md")) + glob.glob(os.path.join(agent_dir, "workflows", "*.md"))
    for md_file in all_md_with_frontmatter:
        rel_path = os.path.relpath(md_file, root_dir)
        with open(md_file, 'r') as f:
            content = f.read()
        
        if not content.startswith("---"):
            print(f"  WARN: {rel_path} has no YAML frontmatter")
            warnings += 1
        else:
            fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if fm_match:
                fm = fm_match.group(1)
                if 'name:' not in fm and 'description:' not in fm:
                    print(f"  WARN: {rel_path} frontmatter missing name/description")
                    warnings += 1
                else:
                    print(f"  PASS: {rel_path}")
            else:
                print(f"  WARN: {rel_path} malformed frontmatter")
                warnings += 1

    # ── Phase 4: Filesystem Path Resolution ──
    print("\n─── Phase 4: Filesystem Path Resolution ───")
    path_regex = re.compile(r'(?<!`)`([^`\n]+)`(?!`)')
    path_issues = 0
    for s_file in skill_files:
        with open(s_file, 'r') as f:
            content = f.read()
        
        matches = path_regex.findall(content)
        for match in matches:
            if match.startswith('--') or match.startswith('http') or match.startswith('<'):
                continue
            if '/' in match or match.endswith('.py') or match.endswith('.md') or match.endswith('.json'):
                if os.path.exists(os.path.join(root_dir, match)) or os.path.exists(os.path.join(os.path.dirname(s_file), match)):
                    pass
                else:
                    print(f"  INFO: Path '{match}' in {os.path.relpath(s_file, root_dir)} might not exist on disk.")
                    path_issues += 1
    
    if path_issues == 0:
        print("  PASS: All referenced paths resolve successfully.")

    # ── Phase 5: Ghost Reference Detection ──
    print("\n─── Phase 5: Ghost Reference Detection ───")
    ghost_terms = ["Generic Manager", "boundary_sync.py", "audit_script.py", "review_text", "sentiment_score", "sklearn_logreg", "Lifespan Handled", "movie", "imdb", "aclImdb", "medtext", "MedText", "Sentiment Scope", "train.py", "train_transformer.py", "SGDClassifier", "DistilBERT", "model_choice", "EntitySchema", "EasyOCR", "ocr_service", "dual_stream", "Token Classification"]
    all_md_files = glob.glob(os.path.join(agent_dir, "**", "*.md"), recursive=True)
    ghost_found = False
    for md_file in all_md_files:
        with open(md_file, 'r') as f:
            content = f.read()
        for term in ghost_terms:
            if term in content:
                print(f"  FAIL: Ghost reference '{term}' found in {os.path.relpath(md_file, root_dir)}")
                errors += 1
                ghost_found = True
    if not ghost_found:
        print("  PASS: No ghost references detected.")

    # ── Phase 6: Cross-Reference Consistency ──
    print("\n─── Phase 6: Cross-Reference Consistency ───")
    if os.path.exists(handoff_path) and os.path.exists(os.path.join(root_dir, "backend", "schemas", "predict.py")):
        with open(handoff_path, 'r') as f:
            handoff = json.load(f)
        with open(os.path.join(root_dir, "backend", "schemas", "predict.py"), 'r') as f:
            schema_content = f.read()
        
        input_fields = handoff.get("payload", {}).get("input_schema", {}).get("PredictionRequest", {})
        for field in input_fields:
            if field not in schema_content:
                print(f"  FAIL: HANDOFF_SCHEMA field '{field}' not found in backend/schemas/predict.py")
                errors += 1
        
        output_fields = handoff.get("payload", {}).get("output_schema", {}).get("PredictionResponse", {})
        for field in output_fields:
            if field not in schema_content:
                print(f"  FAIL: HANDOFF_SCHEMA field '{field}' not found in backend/schemas/predict.py")
                errors += 1
                
        rag_output_fields = handoff.get("payload", {}).get("output_schema", {}).get("PredictionRAGResponse", {})
        for field in rag_output_fields:
            if field not in schema_content:
                print(f"  FAIL: HANDOFF_SCHEMA field '{field}' not found in backend/schemas/predict.py")
                errors += 1
        
        if errors == 0:
            print("  PASS: HANDOFF_SCHEMA.json ↔ backend/schemas/predict.py alignment verified.")

    # ── Phase 7: Route ↔ HANDOFF_SCHEMA Endpoint Parity ──
    print("\n─── Phase 7: Route ↔ HANDOFF_SCHEMA Endpoint Parity ───")
    routes_file = os.path.join(root_dir, "backend", "api", "routes.py")
    if os.path.exists(handoff_path) and os.path.exists(routes_file):
        with open(handoff_path, 'r') as f:
            handoff = json.load(f)
        handoff_endpoints = list(handoff.get("payload", {}).get("api_endpoints", {}).values())
        code_endpoints = extract_routes(routes_file)
        
        clean_handoff_endpoints = [ep.split(" ")[0] for ep in handoff_endpoints]
        
        phase7_errors = 0
        for ep in code_endpoints:
            if ep not in clean_handoff_endpoints:
                print(f"  FAIL: Endpoint {ep} exists in routes.py but missing from HANDOFF_SCHEMA.json")
                errors += 1
                phase7_errors += 1
                
        for ep, clean_ep in zip(handoff_endpoints, clean_handoff_endpoints):
            if clean_ep not in code_endpoints:
                print(f"  FAIL: Endpoint {ep} in HANDOFF_SCHEMA.json missing from routes.py")
                errors += 1
                phase7_errors += 1
                
        if phase7_errors == 0:
            print("  PASS: Route ↔ HANDOFF_SCHEMA parity verified.")

    # ── Phase 8: Singleton Service Integrity ──
    print("\n─── Phase 8: Singleton Service Integrity ───")
    services = [
        ("services/model_service.py", "model_service", "ModelService"),
        ("services/knowledge_service.py", "knowledge_service", "KnowledgeService"),
        ("services/llm_service.py", "llm_service", "LLMService")
    ]
    phase8_errors = 0
    for service_path, expected_name, expected_class in services:
        full_path = os.path.join(root_dir, "backend", service_path)
        if not extract_singleton_assignments(full_path, expected_name, expected_class):
            print(f"  FAIL: Singleton '{expected_name} = {expected_class}()' not found in {service_path}")
            errors += 1
            phase8_errors += 1
    if phase8_errors == 0:
        print("  PASS: All singletons verified.")

    # ── Phase 9: Safety Interceptor Verification ──
    print("\n─── Phase 9: Safety Interceptor Verification ───")
    phase9_errors = 0
    llm_service_path = os.path.join(root_dir, "backend", "services", "llm_service.py")
    if os.path.exists(llm_service_path):
        with open(llm_service_path, 'r') as f:
            content = f.read()
        if r"\d+\.?\d*\s?(mg|mcg|mL|g|IU)" not in content:
            print("  FAIL: Dosing interceptor regex pattern missing from llm_service.py")
            errors += 1
            phase9_errors += 1
            
    prompts_path = os.path.join(root_dir, "backend", "core", "prompts.py")
    if os.path.exists(prompts_path):
        with open(prompts_path, 'r') as f:
            content = f.read()
        if "RAG_SYSTEM_PROMPT = " not in content:
            print("  FAIL: RAG_SYSTEM_PROMPT missing from prompts.py")
            errors += 1
            phase9_errors += 1
        if "CHAT_BASE_SYSTEM_PROMPT = " not in content:
            print("  FAIL: CHAT_BASE_SYSTEM_PROMPT missing from prompts.py")
            errors += 1
            phase9_errors += 1
            
    if phase9_errors == 0:
        print("  PASS: Safety interceptors and guardrails verified.")

    # ── Summary ──
    print("\n" + "═" * 50)
    if errors == 0:
        print(f"SUCCESS: Global Ecosystem Validation Passed! 9/9 Phases OK. ({warnings} warnings)")
        sys.exit(0)
    else:
        print(f"FAILURE: Validation completed with {errors} errors, {warnings} warnings.")
        sys.exit(1)

if __name__ == "__main__":
    validate_all()
