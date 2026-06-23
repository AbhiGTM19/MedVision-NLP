---
name: fastapi-ml
description: Overarching constraints for the FastAPI + PyTorch Backend ML application.
---
# Backend ML Directives (FastAPI + PyTorch)

When operating within the backend logic (`backend/api/`, `backend/core/`, `backend/schemas/`), strictly adhere to the following constraints:

## 1. Inference Server Reliability
- Models are loaded eagerly at startup via the singleton `ModelService()` in `backend/services/model_service.py`, `KnowledgeService()` in `backend/services/knowledge_service.py`, and `LLMService()` in `backend/services/llm_service.py`. Never load model weights inside a route handler per-request.
- Input validation MUST be strictly typed using Pydantic schemas.

## 2. Boundary Strictness
- Ensure data schemas accurately reflect the inputs the frontend will send. Coordinate with Integration QA.
- Maintain four core routes: `/predict`, `/predict-image` (deprecated), `/predict-rag`, and `/chat`.

## 3. Reproducibility
- All PyTorch model runs must be properly seeded.
- Track experiments meticulously using MLflow in `backend/models/tracking/mlruns.db`.
