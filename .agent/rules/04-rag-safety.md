# MedVision RAG & Safety Architecture

## 1. Dual-Layer Routing Logic
Any AI Agent interacting with the MedVision RAG pipeline MUST respect the Dual-Layer architecture:
- **Action Layer (Indian Guidelines)**: Clinical guidelines sourced from Indian medical textbooks (e.g., API Textbook of Medicine, KD Tripathi). These chunks are given an L2-distance relevance boost (multiplier `0.5`) during retrieval to ensure priority over generic texts.
- **Foundation Layer (Global Standards)**: Standard western references (e.g., CDC guidelines). These act as fallbacks if no Action Layer chunk is relevant.

**Rule**: Never bypass this routing logic. Do not directly inject external global guidelines into the prompt if Indian Action Layer text is available in the vector store.

## 2. Safety Interceptors (Crucial)
The backend enforces strict Regex-based and Prompt-based interceptors in `llm_service.py`:
- **Emergency Triage**: If keywords like "anaphylaxis", "heart attack", or "cannot breathe" are detected, the system MUST refuse analysis and direct the user to emergency services.
- **Pediatric Dosing**: Specifically blocks explicit pediatric medication dosing (e.g., Aspirin for children) due to Reye's syndrome risk.
- **Diagnostic Liability**: The LLM is explicitly forbidden from generating a definitive medical diagnosis. It may only state "Symptoms are consistent with X" and must advise consulting a physician.

**Rule**: Any modifications to `llm_service.py` MUST preserve these regex safety checks before the LLM is even invoked. Under no circumstances should the LLM be allowed to evaluate high-risk pediatric dosages without a safety interceptor catching it first.
