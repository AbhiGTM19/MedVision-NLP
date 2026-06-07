---
title: MedVision NLP
emoji: 🏥
colorFrom: teal
colorTo: blue
sdk: docker
app_port: 7860
---

# MedVision NLP: Healthcare NLP Pipeline

[![Language](https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow-000?style=for-the-badge&logo=m&logoColor=F0523A)](https://mlflow.org/)
[![Data](https://img.shields.io/badge/Dataset-MTSamples-2196F3?style=for-the-badge&logo=huggingface)](https://huggingface.co/datasets/tchebonenko/MedicalTranscriptions)

A full-stack web application that classifies clinical notes and medical transcriptions into medical specialties using a production-grade ML pipeline. This project demonstrates end-to-end MLOps, from data preprocessing and hyperparameter tuning to containerized deployment.

---

## 🌟 Architecture & Skills Highlighted

This project serves as a comprehensive portfolio piece demonstrating modern, production-ready software and machine learning engineering practices in the **Healthcare NLP** domain.

### 🧠 Machine Learning & MLOps
-   **Deep Learning (NLP)**: Fine-tuned a **DistilBERT Transformer** on the MTSamples medical transcription dataset for multi-class specialty classification.
-   **Heuristics & Baselines**: Implemented **Scikit-Learn SGD Classifiers** with TF-IDF vectorization for ultra-low latency fallback inference.
-   **Explainable AI (XAI)**: Created a transparent glass-box mechanism to map token weights back to natural language, highlighting exactly *why* a model made its prediction.
-   **Experiment Tracking**: Managed hyperparameters and model lifecycle metrics using **MLflow** and optimized training with **Optuna**.
-   **Data Monitoring**: Integrated **Evidently AI** for model performance and data drift monitoring dashboards.
-   **Dynamic Model Loading**: Completely decoupled ML weights from the source code. Models are dynamically fetched at runtime via the **Hugging Face Hub API**.

### ⚙️ Software Engineering (Backend)
-   **Modern API Framework**: Built a highly performant, asynchronous API gateway using **FastAPI** and **Uvicorn** (ASGI).
-   **N-Tier Architecture**: Strictly decoupled the application layer into Controllers (Routes), Services (Business Logic), and Core configurations, adhering to SOLID principles.
-   **Type Safety**: Enforced strict data validation and serialization using **Pydantic** models.
-   **Monorepo Structure**: Clean separation of `backend/` and `frontend/` with DVC pipeline integration.

### 🎨 Frontend Engineering
-   **Vanilla JS & TailwindCSS**: Built a responsive, zero-dependency Single Page Application (SPA).
-   **Modern UI/UX**: Implemented a healthcare-themed design using Glassmorphism, CSS View Transitions, and reveal-on-scroll animations.
-   **Client-Side Rendering**: Dynamically renders complex Explainable AI data and Mermaid.js architecture diagrams.

### 🛡️ Deep Auditing & Security
-   **Strict Boundary Validation**: Implemented rigid AST-parsing sync checks to prevent schema drift between backend Pydantic models and frontend payloads.
-   **OWASP Compliance**: Enforced strict request limits (`max_length=5000`) and rigorous input sanitization.
-   **Type Safety**: 100% strict Python type hinting enforced across the entire backend.

### 🚀 DevOps & CI/CD
-   **Containerization**: Built highly optimized, multi-stage **Docker** images with secure, non-root user execution.
-   **Continuous Integration**: Automated testing and linting pipelines via **GitHub Actions** with CML reporting.
-   **DVC Pipeline**: Reproducible training via **Data Version Control** (`dvc repro`).
-   **Testing**: Test-Driven Development (TDD) using **Pytest** to ensure robust API contracts.

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
pip install -r requirements.txt

# Download required NLTK data
python -m nltk.downloader punkt punkt_tab stopwords
```

### 4. Train the Model

This script runs within the `backend/` directory. It processes the clinical notes CSV, performs Optuna hyperparameter tuning, and generates model artifacts in `backend/models/`.

```bash
cd backend && python train.py
```

Or use the DVC pipeline:

```bash
dvc repro
```

### 5. Run the Application

```bash
cd backend && uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

---

## 🐳 Docker Deployment

### 1. Build the Docker Image

```bash
# For M1/M2 Macs (Recommended for deployment)
docker build --platform linux/amd64 -t <your-dockerhub-username>/medvision-nlp .

# For other systems
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
-   **Body**: 
    ```json
    { 
      "text": "Patient presents with chest pain radiating to left arm. ECG shows ST elevation.",
      "model_choice": "fast" 
    }
    ```
-   **Response**:
    ```json
    {
      "prediction": "Cardiovascular / Pulmonary",
      "confidence": 0.92,
      "explanation": "Routed to Cardiovascular / Pulmonary based on clinical indicators.",
      "word_importances": {
        "chest": 1.25,
        "ecg": 0.85
      },
      "model_used": "fast",
      "error": null
    }
    ```

### `/model-info`

-   **Method**: `GET`
-   **Query Parameters**: `?model=fast` (default) or `?model=accurate`
-   **Response**: Returns the model's hyperparameters and configuration.

### `/health`

-   **Method**: `GET`
-   **Response**: Returns the operational status of the inference engines and NLTK data.

---

## 📊 Dataset

This project uses the **MTSamples Medical Transcription** dataset, a widely used benchmark for medical specialty classification containing ~5,000 transcribed medical reports across 40+ specialties.

-   **Source**: [Hugging Face - tchebonenko/MedicalTranscriptions](https://huggingface.co/datasets/tchebonenko/MedicalTranscriptions)
-   **Original**: [mtsamples.com](https://mtsamples.com/)

---

## 🧑‍💻 Author

-   **Abhishek Gautam**
-   [LinkedIn](https://www.linkedin.com/in/abhishek-gautam-03b56926b/)
-   [GitHub](https://github.com/AbhiGTM19)
