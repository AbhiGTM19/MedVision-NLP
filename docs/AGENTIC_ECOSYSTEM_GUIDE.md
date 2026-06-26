# Antigravity Agentic Ecosystem Guide

> **This document is the absolute master source of truth** for the `MedVision-NLP` multi-agent ecosystem. All agents, scripts, and workflows must defer to this document for architectural context.

---

## Overview

The Antigravity ecosystem utilizes a deeply nested, hierarchical agentic structure with strict programmatic boundaries. Every agent role is codified as a `SKILL.md` file following a mandatory 9-section template, enforced by the Karpathy Execution Protocol.

## Directory Structure

```
MedVision-NLP/
├── HANDOFF_SCHEMA.json              # Cross-boundary contract (Backend ↔ Frontend)
├── .agent/
│   ├── rules/
│   │   ├── 01-karpathy-protocol.md  # XML-strict reasoning + audit mandate
│   │   ├── 02-tailwind-frontend.md  # Frontend styling constraints
│   │   ├── 03-fastapi-ml.md         # Backend ML constraints
│   │   └── 04-rag-safety.md         # RAG & Safety Architecture
│   ├── scripts/
│   │   └── validate_all.py          # Global ecosystem validation
│   ├── skills/
│   │   ├── Integration_QA/
│   │   │   ├── SKILL.md
│   │   │   ├── SKILL_STATE.json
│   │   │   └── scripts/
│   │   │       ├── surgical_audit.py
│   │   │       ├── project_sync_audit.py
│   │   │       └── env_guard.py
│   │   ├── Lead_Frontend/
│   │   │   ├── core-architecture/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── SKILL_STATE.json
│   │   │   └── design-system/
│   │   │       ├── SKILL.md
│   │   │       ├── SKILL_STATE.json
│   │   │       └── animation-vocabulary.md
│   │   ├── Lead_ML_Backend/
│   │   │   ├── inference-server/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── SKILL_STATE.json
│   │   │   └── model-trainer/
│   │   │       ├── SKILL.md
│   │   │       └── SKILL_STATE.json
│   │   └── Lead_DevOps/
│   │       ├── SKILL.md
│   │       └── SKILL_STATE.json
│   └── workflows/
│       ├── sync-pass.md             # /sync-pass — boundary check
│       ├── surgical-audit.md        # /surgical-audit — code precision check
│       └── ml-update.md             # /ml-update — ML pipeline update checklist
└── docs/
    └── AGENTIC_ECOSYSTEM_GUIDE.md   # This file
```

## Global Rules

All agents must adhere to the rules defined in `.agent/rules/`:

| Rule File | Purpose |
| :--- | :--- |
| `01-karpathy-protocol.md` | Enforces XML-strict reasoning (`<thought>`, `<surgical_plan>`, `<verification_log>`) and the 3-file atomicity rule. |
| `02-tailwind-frontend.md` | Constrains frontend to Tailwind utility classes, mandates `npm run build:css`. |
| `03-fastapi-ml.md` | Constrains backend to eager-singleton model loading via `ModelService()`, strict Pydantic validation, and MLflow tracking. |
| `04-rag-safety.md` | Enforces Dual-Layer RAG routing and strict safety interceptors (dosing regex, diagnostic liability prompt guardrails). |

## The Handoff Contract

The root-level `HANDOFF_SCHEMA.json` is the **immutable boundary contract** between the backend and frontend. It specifies:
- **API Endpoints:** `POST /predict`, `POST /predict-rag`, `POST /chat`, `GET /health` (Note: OCR is strictly DEPRECATED)
- **Input Schema:** `PredictionRequest { text: string }`, `ChatRequest`
- **Output Schema:** `PredictionResponse`, `PredictionRAGResponse`
- **Model Artifacts:** Sequence Classification via `Bio_ClinicalBERT`, Dense Vector Embeddings via `all-MiniLM-L6-v2`, Generative LLM via `Gemini 3.1 Flash Lite`.

Any agent modifying schemas or API routes **must** update `HANDOFF_SCHEMA.json` and run `/sync-pass`.

## Active Departments & Roles

### 1. Integration QA Specialist
**SKILL:** `.agent/skills/Integration_QA/SKILL.md`
**Mission:** Test system boundaries, verify authorized file modifications, and detect schema/DTO drift across XAI DOM boundaries and API contracts.
**Scripts:**
- `scripts/surgical_audit.py` — Parses Git diffs for XML-strict compliance and 3-file atomicity.
- `scripts/project_sync_audit.py` — Validates `schemas/` ↔ `templates/` parity.
- `scripts/env_guard.py` — Verifies `requirements.txt` existence.

---

### 2. Lead Frontend Engineer

#### 2a. Core Architecture
**SKILL:** `.agent/skills/Lead_Frontend/core-architecture/SKILL.md`
**Owns:** `templates/`, `static/js/script.js`, `static/js/chat_script.js`
**Key Constraint:** The UI must correctly parse the `word_attributions` array and inject Captum XAI feature attribution highlights dynamically into the DOM.

#### 2b. Design System
**SKILL:** `.agent/skills/Lead_Frontend/design-system/SKILL.md`
**Owns:** `static/css/input.pcss`, `frontend/tailwind.config.js`, `static/css/styles.css`
**Key Constraint:** Run `npm run build:css` after every style change. Ensure styling adheres to the ambient medical/clinical amber aesthetic.

---

### 3. Lead ML/Backend Engineer

#### 3a. Inference Server
**SKILL:** `.agent/skills/Lead_ML_Backend/inference-server/SKILL.md`
**Owns:** `main.py`, `api/routes.py`, `schemas/predict.py`, `schemas/knowledge.py`, `services/model_service.py`, `services/knowledge_service.py`, `services/llm_service.py`
**Key Constraint:** Models (Bio_ClinicalBERT), Embeddings (ChromaDB), and GenAI clients (Gemini) are loaded eagerly via singleton services. Strict Regex Safety Interceptors must execute BEFORE LLM invocation.

#### 3b. Model Trainer
**SKILL:** `.agent/skills/Lead_ML_Backend/model-trainer/SKILL.md`
**Owns:** `scripts/data_preparation/finetune_bert.py`, `scripts/evaluation/`, `scripts/ingest_textbooks.py`, `scripts/ingest_knowledge.py`, `notebooks/`, `data/chroma_db/`, `models/tracking/mlruns.db`
**Key Constraint:** All experiments tracked via MLflow. Must compute Dense Vector Embeddings (all-MiniLM-L6-v2) using RecursiveCharacterTextSplitter for Dual-Layer RAG.

---

### 4. Lead DevOps
**SKILL:** `.agent/skills/Lead_DevOps/SKILL.md`
**Owns:** `Dockerfile`, `.dockerignore`, `.github/workflows/`, `requirements.txt`
**Key Constraint:** Multi-stage Docker builds, no `latest` tags, CPU-only PyTorch wheels for cost-effective deployments.

## Workflows (Slash Commands)

| Command | Script / Action | Purpose |
| :--- | :--- | :--- |
| `/sync-pass` | `project_sync_audit.py` | Check backend ↔ frontend schema boundaries. |
| `/surgical-audit` | `surgical_audit.py` | Validate XML-strict compliance on code diffs. |
| `/ml-update` | Checklist | Safe ML pipeline update (train → track → evaluate → sync). |

## Agent Metadata

Every skill directory contains a `SKILL_STATE.json` with the following structure:
```json
{
  "agent_id": "<unique_id>",
  "status": "idle | active",
  "confidence_score": 10,
  "last_audit_passed": true,
  "open_tasks": []
}
```
Agents must update their state upon task completion.

## Validation

Run the global ecosystem validator at any time:
```bash
python3 .agent/scripts/validate_all.py
```
This checks 6 phases: JSON linting, 9-section compliance, YAML frontmatter, filesystem paths, ghost references, and HANDOFF_SCHEMA ↔ backend schema parity.
