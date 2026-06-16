---
title: MedVision NLP
emoji: 🏥
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
---

# MedVision NLP: Healthcare NLP Pipeline

[![Language](https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow-000?style=for-the-badge&logo=m&logoColor=F0523A)](https://mlflow.org/)
[![Data](https://img.shields.io/badge/Dataset-MTSamples-2196F3?style=for-the-badge&logo=huggingface)](https://huggingface.co/datasets/tchebonenko/MedicalTranscriptions)

A full-stack web application that performs Clinical Token-Level Named Entity Recognition (NER) on raw medical texts and prescription images. This project demonstrates end-to-end MLOps, from dataset preparation and model inference to Explainable AI (XAI) UI rendering and containerized deployment.

---

## 🌟 Architecture & Skills Highlighted

This project serves as a comprehensive portfolio piece demonstrating modern, production-ready software and machine learning engineering practices in the **Healthcare NLP** domain.

### 🧠 Machine Learning & MLOps
-   **DualStreamFusionNER**: A dual-modality pipeline combining **Bio_ClinicalBERT** (for semantic clinical text token classification) and **EasyOCR** (for spatial extraction of text from prescription images).
-   **Explainable AI (XAI)**: Features transparent predictions by extracting token-level bounding boxes and dynamically highlighting the parsed `PROBLEM`, `TREATMENT`, `TEST`, and `MEDICATION` tags directly in the user interface.
-   **Experiment Tracking**: Managed hyperparameters and model lifecycle metrics using **MLflow** tracked in a local SQLite database (`mlruns.db`).
-   **Data Monitoring**: Integrated **Evidently AI** for monitoring medical note length drift, confidence score distributions, and dataset statistics.

### ⚙️ Software Engineering (Backend)
-   **Modern API Framework**: Built a highly performant, asynchronous API gateway using **FastAPI** and **Uvicorn** (ASGI).
-   **Singleton Services**: Models are eagerly loaded at startup via centralized singletons (`ModelService` and `OCRService`) to ensure high-throughput zero-latency requests.
-   **Type Safety**: Enforced strict data validation and serialization using **Pydantic** schema boundaries.

### 🎨 Frontend Engineering
-   **Vanilla JS & TailwindCSS**: Built a highly responsive Single Page Application (SPA).
-   **Modern UI/UX**: Implemented a healthcare-themed design using elegant Glassmorphism aesthetics, dynamic DOM manipulation for XAI entity tag injection, and CSS micro-animations.
-   **Dual Input Routing**: The frontend seamlessly switches between processing raw clinical text (`/predict`) and multipart `FormData` image uploads (`/predict-image`).

### 🛡️ Deep Auditing & Security
-   **Strict Boundary Validation**: Maintained precise `HANDOFF_SCHEMA.json` rules verified by custom continuous integration auditing scripts (`validate_all.py`).
-   **OWASP Compliance**: Enforced strict request limits (`max_length=5000`) and rigorous input sanitization.
-   **Type Safety**: 100% strict Python type hinting enforced across the backend.

### 🚀 DevOps & CI/CD
-   **Containerization**: Built highly optimized **Docker** images ensuring all OpenCV dependencies (`libgl1-mesa-glx`) and PyTorch CPU-only wheels are correctly resolved for efficient cloud deployments (e.g. Hugging Face Spaces).
-   **Continuous Integration**: Automated testing and linting pipelines via **GitHub Actions**.
-   **DVC Pipeline**: Reproducible training and evaluation tracking via **Data Version Control** (`dvc repro`).
-   **Testing**: Test-Driven Development (TDD) using **Pytest** with comprehensive mocking of ML services to ensure robust API contracts without demanding heavy ML weights.

---

## ⚙️ Running Locally

### Prerequisites

-   Python 3.14 (recommended to manage with `pyenv`)
-   Docker Desktop

### 1. Clone the Repository

```bash
git clone https://github.com/AbhiGTM19/MedVision-NLP.git
cd MedVision-NLP
```

### 2. Set Up the Python Environment

```bash
# Install and set the local Python version using pyenv
pyenv install 3.14.4
pyenv local 3.14.4

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Training & Evaluation (Optional)

Model training is conducted natively inside Jupyter Notebooks. Navigate to `backend/notebooks/kaggle_training.ipynb` to view or rerun the fine-tuning of the Bio_ClinicalBERT model on the MTSamples dataset.

To run the full evaluation pipeline reproducibly using Data Version Control:

```bash
cd backend
dvc repro
```

### 5. Run the Application

```bash
cd backend
uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`. 
Metrics and Monitoring dashboards can be accessed at `/metrics` and `/monitoring` respectively.

---

## 🐳 Docker Deployment

### 1. Build the Docker Image

```bash
docker build -t <your-dockerhub-username>/medvision-nlp .
```

### 2. Run the Container Locally

```bash
docker run -p 7860:7860 <your-dockerhub-username>/medvision-nlp
```

The application will be available at `http://localhost:7860`.

---

## API Endpoints

### `/predict`

-   **Method**: `POST`
-   **Description**: Evaluates raw clinical text via Bio_ClinicalBERT.
-   **Body**: 
    ```json
    { 
      "text": "Patient was prescribed 50mg of Aspirin for mild chest pain."
    }
    ```
-   **Response**:
    ```json
    {
      "entities": [
        {
          "word": "Aspirin",
          "tag": "B-MEDICATIONS",
          "confidence": 0.985
        },
        {
          "word": "chest pain",
          "tag": "B-PROBLEM",
          "confidence": 0.921
        }
      ]
    }
    ```

### `/predict-image`

-   **Method**: `POST`
-   **Description**: Evaluates prescription images using EasyOCR spatial extraction followed by Bio_ClinicalBERT token classification.
-   **Body**: `multipart/form-data` with a single `file` field containing the image.
-   **Response**: Same as `/predict`, returning a JSON array of parsed entities.

### `/health`

-   **Method**: `GET`
-   **Response**: Returns the operational status of the dual inference engines.

---

## 📊 Dataset

This project uses the **MTSamples Medical Transcription** dataset, a widely used benchmark for medical specialty and NER classification containing ~5,000 transcribed medical reports across 40+ specialties.

-   **Source**: [Hugging Face - tchebonenko/MedicalTranscriptions](https://huggingface.co/datasets/tchebonenko/MedicalTranscriptions)
-   **Original**: [mtsamples.com](https://mtsamples.com/)

---

## 🧑‍💻 Author

-   **Abhishek Gautam**
-   [LinkedIn](https://www.linkedin.com/in/abhishek-gautam-03b56926b/)
-   [GitHub](https://github.com/AbhiGTM19)
