import sys


def audit_surgical_precision(diff_file):
    """Audits a diff file for surgical precision according to Karpathy standards."""
    print("--- 🔬 Karpathy Surgical Audit ---")
    
    with open(diff_file) as f:
        lines = f.readlines()
    
    added = 0
    deleted = 0
    files_touched = set()
    
    for line in lines:
        if line.startswith('+++ '):
            files_touched.add(line[4:].strip())
        if line.startswith('+') and not line.startswith('+++'):
            added += 1
        if line.startswith('-') and not line.startswith('---'):
            deleted += 1
            
    print("Metrics:")
    print(f"  - Files Touched: {len(files_touched)}")
    print(f"  - Lines Added:   {added}")
    print(f"  - Lines Deleted: {deleted}")
    
    # Heuristics
    if len(files_touched) > 3:
        print("⚠️ WARNING: Task exceeds 3-file atomicity rule.")
    
    if added > 100 and added > (deleted * 3):
        print("⚠️ WARNING: High additive complexity detected. Is this 'Minimum Viable Code'?")
        
    for f in files_touched:
        if "backend/services/llm_service.py" in f:
            print(f"🚩 SAFETY-CRITICAL: {f} modified. Safety interceptors may be affected.")
        elif "backend/core/prompts.py" in f:
            print(f"🚩 SAFETY-CRITICAL: {f} modified. System prompt guardrails may be affected.")
        elif "backend/schemas/" in f:
            print(f"🚩 CONTRACT BOUNDARY: {f} modified. Schema change requires HANDOFF_SCHEMA update.")
        elif "HANDOFF_SCHEMA.json" in f:
            print(f"🚩 CONTRACT BOUNDARY: {f} modified. Run /sync-pass after this change.")
        elif "backend/api/" in f or "backend/core/" in f:
            print(f"🚩 CRITICAL PATH: {f} modified. Ensure NO style-only changes.")
            
        if "backend/services/" in f or "backend/api/" in f:
            print(f"⚠️ TEST REMINDER: {f} modified. Ensure corresponding test files in backend/tests/ are updated.")

    # Karpathy XML-Strict Audit
    content = "".join(lines)
    has_thought = "<thought>" in content
    has_plan = "<surgical_plan>" in content
    has_log = "<verification_log>" in content
    
    if not (has_thought and has_plan and has_log):
        print("\n🚩 XML-STRICT VIOLATION: Missing <thought>, <surgical_plan>, or <verification_log>.")
    else:
        print("\n✅ XML-STRICT: Passed.")

    print("\nAudit Conclusion: Review the above flags before committing.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python surgical_audit.py <DIFF_FILE>")
    else:
        audit_surgical_precision(sys.argv[1])
