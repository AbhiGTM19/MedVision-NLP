---
name: sync-pass
description: Executes the ecosystem boundary check.
---
# Workflow: Project Sync Pass

1. **Locate Target Script:** Find `.agent/skills/Integration_QA/scripts/project_sync_audit.py`.
2. **Execute Script:** Run the script using Python: `python3 .agent/skills/Integration_QA/scripts/project_sync_audit.py`.
3. **Analyze Schema Drift:** If a mismatch is detected, fix the API interfaces or schemas to align with `HANDOFF_SCHEMA.json`.
4. **Report:** Present the pass/fail status in the Integration QA Report format.
