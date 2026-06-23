---
description: A strict checklist for safely updating the Medical Specialty Classification Model.
---

# Workflow: ML Feature Update

Updating the Machine Learning pipeline is highly sensitive.

## Execution Checklist:
1. **Update Training Notebooks:** Modify `backend/notebooks/` or related `backend/scripts/`.
2. **Track with MLflow:** Ensure new runs are logged correctly in `backend/models/tracking/mlruns.db`.
3. **Smoke Test:** Evaluate the model via `/predict` locally to ensure no performance degradation.
4. **Final Sync Pass:** Run `/sync-pass` to ensure no boundaries broke.