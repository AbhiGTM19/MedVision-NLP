---
description: A strict checklist for safely updating the Clinical OCR-NLP Model.
---

# Workflow: ML Feature Update

Updating the Machine Learning pipeline is highly sensitive.

## Execution Checklist:
1. **Update Training Script:** Modify `backend/train.py` or `backend/train_transformer.py`.
2. **Track with MLflow:** Ensure new runs are logged correctly in `backend/mlruns/`.
3. **Smoke Test:** Evaluate the model using `backend/evaluate_models.py`.
4. **Final Sync Pass:** Run `/sync-pass` to ensure no boundaries broke.