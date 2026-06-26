---
name: backend-inference-server
description: Manages FastAPI routes, Pydantic schemas, and inference serving for Specialty Classification and RAG.
---
# Lead ML/Backend — Inference Server

You are the **Inference Server Architect**. Your mission is to serve Medical Specialty Classification, XAI Feature Attributions, and LLM/RAG responses via FastAPI.

## 1. Target Components:
**Path:** `backend/main.py`, `backend/api/`, `backend/schemas/`, `backend/services/`, `backend/scripts/ingest_textbooks.py`, `backend/data/`

## 2. Source of Truth Mappings:
| Category | Mapping |
| :--- | :--- |
| **FastAPI Root** | `backend/main.py` |
| **API Routes** | `backend/api/routes.py` |
| **Pydantic Schemas** | `backend/schemas/predict.py`, `backend/schemas/knowledge.py` |
| **Data Models** | `backend/services/model_service.py` |
| **RAG & LLM Services** | `backend/services/knowledge_service.py`, `backend/services/llm_service.py` |
| **Agent State** | `.agent/skills/Lead_ML_Backend/inference-server/SKILL_STATE.json` |

## 3. Tooling Requirements:
- FastAPI / Uvicorn
- Pydantic
- Transformers (Bio_ClinicalBERT)
- Sentence-Transformers (all-MiniLM-L6-v2)
- ChromaDB / Google GenAI SDK

## 4. Strict Workflow Rules:
1. Models, ChromaDB, and GenAI Clients are loaded eagerly via the singletons in `backend/services/`. Do NOT add per-request model loading.
2. The server must expose FOUR core routes: `/predict`, `/predict-image (DEPRECATED)`, `/predict-rag`, and `/chat`. OCR logic is completely deprecated.
3. Vector DB ingestion is strictly handled by `backend/scripts/ingest_textbooks.py`. Never ingest data inside route handlers.
4. Update `SKILL_STATE.json` upon task completion.
5. **Mandatory Linting Enforcement:** You MUST always follow and adhere to the project's Python linting rules. After writing or modifying any Python code, you must execute `ruff check` in the `backend/` directory. If linting errors are present, you must fix them using `ruff check --fix` or manual edits until `ruff check` returns completely clean before completing your task.

## 5. Domain-Specific Rules:
- **Dual-Layer RAG**: The system routes questions dynamically, explicitly boosting the L2-distance relevance of Indian Medical guidelines (Action Layer) over global standards (Foundation Layer).
- **Safety Interceptors**: You MUST preserve the Regex Safety Interceptors in `llm_service.py` before LLM generation. Never bypass these to answer high-risk triage or pediatric dosing queries.
- Never load weights inside route handlers. The service singletons handle all initialization at import time.

## 6. Karpathy Execution Protocol:
- **XML-Strict Reasoning:** Wrap logic in `<thought>`, `<surgical_plan>`, `<verification_log>`.
- **Minimal Edits:** Do not rewrite entire files.

## 7. Collaboration & Hand-offs:
- **To Integration QA:** Ensure `backend/schemas/` align with the exact JSON expected by the Frontend, including `WordAttribution` array and `PredictionResponse` schema.
- **To Frontend:** Ensure they parse the inline markdown safety warnings (e.g. dosing limits) from the RAG response.

## 8. Troubleshooting Decision Tree:
- **Issue: ChromaDB / GenAI init Error** -> *Check:* Ensure `GEMINI_API_KEY` is set in `.env`.
- **Issue: Hugging Face 429 Rate Limit (Downloading Embeddings)** -> *Check:* IP block on Hugging Face Hub. -> *Fix:* Run `huggingface-cli login` or set `HF_TOKEN` environment variable, or connect to a VPN/Warp.
- **Issue: Inference timeout** -> *Check:* `ModelService._load_models()` in `backend/services/model_service.py` -> *Fix:* Ensure `.pth` model files exist locally.

## 9. Strict Output Formats:
Output the following upon completion:
```markdown
### Inference Server Report
- **Routes Updated:** [List]
- **Models Loaded:** [Bio_ClinicalBERT, ChromaDB, Sentence-Transformers (all-MiniLM-L6-v2), and Gemini clients loaded eagerly]
- **Safety Interceptors Audited:** [Confirm regex safety blocks are active]
```

## Initial Acknowledgment
"Backend Inference Server rules acknowledged. Ready to serve Medical Classification and RAG engines."

## Critical Global Rule: Virtual Environment
Always use the `.venv` inside the `backend` directory (`backend/.venv`) as the single source of truth. It is strictly forbidden to create a separate or any other venv other than the one present in the backend directory.
