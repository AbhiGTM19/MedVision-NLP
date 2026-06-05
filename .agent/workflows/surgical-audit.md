---
name: surgical-audit
description: Executes the Karpathy Execution Protocol surgical audit script to verify XML strictness and code precision.
---
# Workflow: Surgical Audit

This workflow triggers the `Integration QA` surgical audit. Run this before concluding any complex refactoring task.

## Execution Steps:
1. **Locate Target Script:** Find `.agent/skills/Integration_QA/scripts/surgical_audit.py`.
2. **Execute Script:** Run the script and pass the path of the modified file or a generated diff as the argument.
3. **Parse Results:** 
   - If the script outputs `XML-STRICT VIOLATION`, you must fix your tags.
4. **Report to User:** Present the output of the audit to the user.
