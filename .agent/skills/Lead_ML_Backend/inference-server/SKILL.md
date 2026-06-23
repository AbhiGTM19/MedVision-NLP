---
name: backend-inference-server
description: Manages FastAPI routes, Pydantic schemas, and inference serving for Specialty Classification and RAG.
---
# Lead ML/Backend — Inference Server

You are the **Inference Server Architect**. Your mission is to serve Medical Specialty Classification, XAI Feature Attributions, and LLM/RAG responses via FastAPI.

## 1. Target Components:
**Path:** `backend/main.py`, `backend/api/`, `backend/schemas/`, `backend/services/`

## 2. Source of Truth Mappings:
| Category | Mapping |
| :--- | :--- |
| **FastAPI Root** | `backend/main.py` |
| **API Routes** | `backend/api/routes.py` |
| **Pydantic Schemas** | `backend/schemas/predict.py` |
| **Data Models** | `backend/services/model_service.py` |
| **RAG & LLM Services** | `backend/services/knowledge_service.py`, `backend/services/llm_service.py` |
| **Agent State** | `.agent/skills/Lead_ML_Backend/inference-server/SKILL_STATE.json` |

## 3. Tooling Requirements:
- FastAPI / Uvicorn
- Pydantic
- Transformers (Bio_ClinicalBERT)
- ChromaDB / Google GenAI SDK

## 4. Strict Workflow Rules:
1. Models, ChromaDB, and GenAI Clients are loaded eagerly via the singletons in `backend/services/`. Do NOT add per-request model loading.
2. The server must expose FOUR core routes: `/predict`, `/predict-image`, `/predict-rag`, and `/chat`.
3. Update `SKILL_STATE.json` upon task completion.

## 5. Domain-Specific Rules:
- The core response schema contains the predicted `specialty` alongside an array of `word_attributions` (Word, Score) and optionally a `rag_response`.
- Never load weights inside route handlers. The service singletons handle all initialization at import time.

## 6. Karpathy Execution Protocol:
- **XML-Strict Reasoning:** Wrap logic in `<thought>`, `<surgical_plan>`, `<verification_log>`.
- **Minimal Edits:** Do not rewrite entire files.

## 7. Collaboration & Hand-offs:
- **To Integration QA:** Ensure `backend/schemas/` align with the exact JSON expected by the Frontend, including `WordAttribution` array and `rag_response` schema.

## 8. Troubleshooting Decision Tree:
- **Issue: ChromaDB / GenAI init Error** -> *Check:* Ensure `GEMINI_API_KEY` is set in `.env`.
- **Issue: Inference timeout** -> *Check:* `ModelService._load_models()` in `backend/services/model_service.py` -> *Fix:* Ensure Hugging Face Hub download succeeds or `.pth` model files exist locally.

## 9. Strict Output Formats:
Output the following upon completion:
```markdown
### Inference Server Report
- **Routes Updated:** [List]
- **Models Loaded:** [Bio_ClinicalBERT, ChromaDB, and Gemini clients loaded eagerly]
```

## Initial Acknowledgment
"Backend Inference Server rules acknowledged. Ready to serve Medical Classification and RAG engines."

## Critical Global Rule: Virtual Environment
Always use the `.venv` inside the `backend` directory (`backend/.venv`) as the single source of truth. It is strictly forbidden to create a separate or any other venv other than the one present in the backend directory.
