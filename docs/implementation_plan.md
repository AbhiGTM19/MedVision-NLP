# Dataset Acquisition & Feature Engineering Plan

This document outlines the proposed strategy for upgrading the MedVision NLP ecosystem. The goal is to gather 5 robust datasets covering both the OCR (Optical Character Recognition) and NLP (Natural Language Processing) domains, perform comprehensive preprocessing, and engineer specialized features.

## Proposed Datasets

To build a robust pipeline that can handle both raw document images and raw clinical text, I propose utilizing the following 5 datasets:

1. **MTSamples (Clinical Text)**
   - *Domain*: NLP (Medical Transcriptions)
   - *Use Case*: Predicting medical specialty based on transcription text. This serves as our baseline classification dataset.
2. **MIMIC-IV Clinical Notes Demo**
   - *Domain*: NLP (Intensive Care Unit Records)
   - *Use Case*: Complex, real-world clinical notes for fine-tuning robust models.
3. **Medical Prescription Handwritten Words (`avi-kai/Medical_Prescription_Handwritten_Words` on HF)**
   - *Domain*: OCR Image Data
   - *Use Case*: Thousands of cropped handwritten medical prescription words. Crucial for fine-tuning the EasyOCR pipeline to recognize doctors' handwriting.
4. **Synthetic Medical Prescriptions (`chinmays18/medical-prescription-dataset` on HF)**
   - *Domain*: OCR Image Data (Synthetic)
   - *Use Case*: Full-page synthetic prescriptions with structured annotations to train document layout extraction (e.g., extracting medicine names, dosages, and instructions).
5. **Medical Records Parsing Validation Set (`ekacare/medical_records_parsing_validation_set` on HF)**
   - *Domain*: OCR + NLP (Multimodal)
   - *Use Case*: A high-quality, privacy-focused dataset of lab reports and prescriptions from real healthcare settings, curated specifically for evaluating AI-driven information extraction.

> [!WARNING]
> **Data Privacy & Access Constraints**
> MIMIC-III requires a formal data use agreement and human subjects training (PhysioNet). If we cannot procure this, we can substitute it with the **i2b2/n2c2 Clinical NLP Challenge** datasets or additional Kaggle open-source clinical notes.

## Proposed Pipeline

### 1. OCR Preprocessing (Computer Vision)
For the raw images (Prescriptions, Lab Reports):
- **Binarization & Grayscale**: Converting colored scans into high-contrast grayscale to improve text contrast.
- **Denoising**: Applying Gaussian blur or median filtering to remove scanner noise/artifacts.
- **Deskewing & Alignment**: Correcting the rotational angle of scanned documents.
- **Bounding Box Localization**: Cropping relevant regions of interest (ROI) before feeding them into EasyOCR.

### 2. NLP Preprocessing (Text)
For the extracted text and raw clinical notes:
- **PHI Scrubbing / De-identification**: Removing any residual personally identifiable information using regex patterns or libraries like `presidio`.
- **Medical Stopword Removal**: Filtering standard English stopwords + common medical stop words (e.g., 'patient', 'presents', 'history').
- **Lemmatization/Stemming**: Standardizing clinical vocabulary (e.g., 'diagnosed', 'diagnosis' -> 'diagnos').
- **Tokenization**: Breaking down text into unigrams and bigrams.

### 3. Feature Engineering
- **TF-IDF Enhancements**: Expanding our current TF-IDF vectorizer to include bigrams and trigrams for capturing complex medical phrases (e.g., "myocardial infarction").
- **Clinical BERT Embeddings**: Using specialized Hugging Face models (e.g., `emilyalsentzer/Bio_ClinicalBERT`) to extract dense vector embeddings from the notes.
- **Heuristic Features**: Engineering meta-features such as text length, document density, and presence of specific medical prefixes/suffixes.

> [!NOTE]
> **Finalized Decisions:**
> 1. We will use the [MIMIC-IV Clinical Database Demo](https://www.kaggle.com/datasets/montassarba/mimic-iv-clinical-database-demo-2-2) from Kaggle as a proxy for the restricted dataset.
> 2. **OCR Strategy:** We will begin with **EasyOCR** (which uses a standard CNN-RNN architecture) as our baseline. As we implement, I will introduce and walk you through **Transformers (like Donut)**, which look at the *entire document image* at once without needing bounding boxes, teaching you the differences between traditional and modern OCR.
> 3. **Storage:** All datasets will be stored locally in `backend/dataset/raw/` and versioned via DVC.

## Verification Plan
1. Validate dataset downloads and file integrity within `backend/dataset/raw/`.
2. Run unit tests on the OCR preprocessing functions with sample images to ensure text clarity improves.
3. Validate NLP tokenization outputs to ensure PHI and noise are properly scrubbed.
