# MedVision RAG & Safety Architecture

## 1. Dual-Layer Routing Logic
Any AI Agent interacting with the MedVision RAG pipeline MUST respect the Dual-Layer architecture:
- **Action Layer (Indian Guidelines)**: Clinical guidelines sourced from Indian medical textbooks (e.g., API Textbook of Medicine, KD Tripathi). These chunks are given an L2-distance relevance boost (multiplier `0.5`) during retrieval to ensure priority over generic texts.
- **Foundation Layer (Global Standards)**: Standard western references (e.g., CDC guidelines). These act as fallbacks if no Action Layer chunk is relevant.

**Rule**: Never bypass this routing logic. Do not directly inject external global guidelines into the prompt if Indian Action Layer text is available in the vector store.

## 2. Safety Interceptors (Crucial)
The backend enforces strict safety mechanisms in `llm_service.py` to mitigate clinical liability:
- **Dosing Interceptor (Regex-Based)**: A regex pattern (`mg|mcg|mL|g|IU`) scans the final LLM output. If quantitative dosing is detected, a mandatory markdown warning is appended inline to the response, explicitly advising that the AI is not a doctor and dosages must be verified by a licensed professional.
- **Diagnostic Liability (Prompt-Based)**: The `RAG_SYSTEM_PROMPT` explicitly forbids the LLM from generating definitive medical diagnoses. It may only state "Symptoms are consistent with X" and must advise consulting a physician.
- **Medical-Only Constraint (Prompt-Based)**: The `CHAT_BASE_SYSTEM_PROMPT` strictly confines the assistant to medical queries, rejecting out-of-domain interactions.

**Rule**: Any modifications to `llm_service.py` MUST preserve the dosing regex interceptor and the prompt-level guardrails. Under no circumstances should the LLM be allowed to output unchecked medication dosages without the appended safety warning.
