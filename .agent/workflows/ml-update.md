---
description: A strict checklist for safely updating the Healthcare OCR-NLP Model.
---

# Workflow: ML Feature Update

Updating the Machine Learning pipeline is highly sensitive.

## Execution Checklist:
1. **Update Training Notebooks:** Modify `backend/notebooks/kaggle_training.ipynb` or related `backend/scripts/data_preparation/`.
2. **Track with MLflow:** Ensure new runs are logged correctly in `backend/models/tracking/mlruns.db`.
3. **Smoke Test:** Evaluate the model using `backend/scripts/evaluation/evaluate_fusion.py`.
4. **Final Sync Pass:** Run `/sync-pass` to ensure no boundaries broke.