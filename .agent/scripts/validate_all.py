#!/usr/bin/env python3
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

    # Also lint the root HANDOFF_SCHEMA.json
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
            # Check for 'name' field
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
    ghost_terms = ["Generic Manager", "boundary_sync.py", "audit_script.py", "review_text", "sentiment_score", "sklearn_logreg", "Lifespan Handled", "movie", "imdb", "aclImdb", "medtext", "MedText", "Sentiment Scope", "train.py", "train_transformer.py", "SGDClassifier", "DistilBERT", "model_choice", "DualStreamFusionNER", "EntitySchema", "EasyOCR", "ocr_service", "dual_stream", "Token Classification", "Token-Level NER"]
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
    # Check HANDOFF_SCHEMA.json matches backend/schemas/predict.py
    if os.path.exists(handoff_path) and os.path.exists(os.path.join(root_dir, "backend", "schemas", "predict.py")):
        with open(handoff_path, 'r') as f:
            handoff = json.load(f)
        with open(os.path.join(root_dir, "backend", "schemas", "predict.py"), 'r') as f:
            schema_content = f.read()
        
        # Check input field names exist in the Pydantic schema
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
        
        if errors == 0:
            print("  PASS: HANDOFF_SCHEMA.json ↔ backend/schemas/predict.py alignment verified.")
    
    # ── Summary ──
    print("\n" + "═" * 50)
    if errors == 0:
        print(f"SUCCESS: Global Ecosystem Validation Passed! ({warnings} warnings)")
        sys.exit(0)
    else:
        print(f"FAILURE: Validation completed with {errors} errors, {warnings} warnings.")
        sys.exit(1)

if __name__ == "__main__":
    validate_all()
