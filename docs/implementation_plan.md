# Structured Phased Workflow: TrOCR & Bio_ClinicalBERT Architecture

Based on the analysis of the evaluation metrics and your architectural feedback, we have identified critical failures in the current pipeline: massive `1.0` F1 score overfitting, hallucination on OOD data, and an inability of EasyOCR to parse cursive handwriting. 

To resolve this, we will transition to a **Dual-Model Architecture**: **TrOCR** (for vision-based handwriting transcription) and **Bio_ClinicalBERT** (for medical entity extraction). 

We will execute this pivot using a strict phased Git workflow, creating separate branches for each phase using the `hotfix/{phase_name}` convention to isolate our rectifications.

---

## 📈 Phase 1: Discrepancy-Free Dataset Preparation & Exploratory Data Analysis
**Branch:** `hotfix/dataset_preparation`

**Goal:** Conduct a rigorous data study of all raw datasets to understand the distributions of images vs. text, resolve missingness, map schemas (e.g., `subject_id`), and output unified, discrepancy-free data.

**Tasks:**
1. **Exploratory Data Study (EDA)**: 
   - **Image vs. Text Breakdown**: We will categorize the datasets. `Handwritten_Medical_Prescriptions_Collection`, `Medical_Prescription_Handwritten_Words`, and `medical_records_parsing_validation_set` (Parquets) are image-based. `mtsamples.csv` and `mimic-iv` are text/structured data.
   - **Parquet Analysis**: Unpack and analyze the schemas of the `.parquet` files in the validation set (which contain embedded `image` bytes, `sample_prompt`, and `rubrics`).
   - **Schema Mapping**: For relational datasets (like `mimic-iv`), establish a common mapping key (e.g., `subject_id`) to link patients to their prescriptions and diagnoses.
   - **Data Cleaning**: Implement handling for missing values (NaNs), duplicates, and schema inconsistencies across the diverse sources.
2. **Refactor `build_unified_dataset.py`**:
   - Create a dedicated parsing pipeline for the Image datasets to generate a comprehensive **TrOCR Dataset** (Image path/bytes -> Text Transcription).
   - Create dedicated parsing functions for the Text/Structured datasets to generate a robust **Bio_ClinicalBERT Dataset** (Clinical Text -> NER labels).
3. **Data Splitting & Output**: Output discrepancy-free, deduplicated, and clean datasets for both models into the `dataset/processed/` directory.

---

## 🧠 Phase 2: Modelling
**Branch:** `hotfix/modelling`

**Goal:** Train and validate the new dual-model architecture.

**Tasks:**
1. **TrOCR Fine-Tuning**: Create/update the TrOCR training script to ingest the handwritten dataset and fine-tune `microsoft/trocr-base-handwritten`.
2. **Bio_ClinicalBERT Fine-Tuning**: Update `kaggle_training.ipynb` to ingest the newly diversified text dataset. Implement aggressive regularization (weight decay, dropout) and early stopping to prevent the `1.0` overfitting seen previously.
3. **Model Evaluation**: Generate updated precision/recall and F1 metrics to verify that the overfitting and OOD hallucinations have been resolved.

---

## 🔌 Phase 3: API & Frontend Integration
**Branch:** `hotfix/api_and_integration`

**Goal:** Connect the backend models to the frontend UI and containerize the application.

**Tasks:**
1. **Dependency Overhaul**: Remove `easyocr` and implement `transformers` TrOCR logic inside `backend/services/model_service.py`.
2. **API Endpoint Wiring**: Refactor `/predict-image` in `routes.py` to route the image bytes to TrOCR, take the extracted string, and pass it to Bio_ClinicalBERT.
3. **Frontend Sync**: Ensure the JSON payload returned aligns perfectly with the UI's XAI bounding-box DOM rendering.
4. **Containerization**: Update the `Dockerfile` to optimize for the TrOCR + BERT dual architecture (ensuring efficient PyTorch CPU wheel resolution).

---

## 🛡️ Phase 4: Exhaustive Audit Pass & Testing
**Branch:** `hotfix/audit_and_testing`

**Goal:** Ensure we do not repeat our previous mistakes.

**Tasks:**
1. **Automated Testing**: Run rigorous Pytest suites against the new dual-model endpoints using mocked services.
2. **Ecosystem Synchronization**: Update `HANDOFF_SCHEMA.json` and all `.agent/skills/` documents (e.g., removing EasyOCR rules and documenting TrOCR).
3. **Karpathy Validation**: Run `.agent/scripts/validate_all.py` to ensure zero ghost references or schema drift.

---

## User Review Required

The plan has been updated to explicitly prioritize the rigorous data study (EDA), Parquet analysis, missingness handling, and common mapping schemas (`subject_id`) you requested in Phase 1. 

If this accurately reflects your data engineering strategy, please approve so we can transition into execution mode and check out the `hotfix/dataset_preparation` branch!
