---
title: MedVision NLP
emoji: 🏥
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
---

# MedVision NLP: Medical Specialty Classification & AI Assistant

[![Language](https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow-000?style=for-the-badge&logo=m&logoColor=F0523A)](https://mlflow.org/)
[![Data](https://img.shields.io/badge/Dataset-MTSamples-2196F3?style=for-the-badge&logo=huggingface)](https://huggingface.co/datasets/tchebonenko/MedicalTranscriptions)

A full-stack web application that performs **Medical Specialty Classification** on raw clinical texts and prescription images. This project demonstrates end-to-end MLOps and advanced generative AI integrations, from dataset preparation and model inference to Explainable AI (XAI) UI rendering, RAG-augmented chatbot capabilities, and containerized deployment.

---

## 🌟 Architecture & Skills Highlighted

This project serves as a comprehensive portfolio piece demonstrating modern, production-ready software, machine learning, and AI engineering practices in the **Healthcare NLP** domain.

### 🧠 Machine Learning & MLOps
-   **Medical Specialty Classification**: A robust sequence classification pipeline powered by **Bio_ClinicalBERT**, fine-tuned to categorize unstructured clinical text into specific medical specialties (e.g., Cardiology, Neurology).
-   **Explainable AI (XAI)**: Features highly transparent predictions using **PyTorch Captum** (Integrated Gradients) to calculate word-level feature attributions, dynamically highlighting influential tokens directly in the user interface.
-   **Retrieval-Augmented Generation (RAG)**: Integrates **ChromaDB** for semantic search across clinical guidelines, allowing the AI to base its responses on grounded, domain-specific context.
-   **Conversational AI Assistant**: Uses the **Google Gemini 2.5 Flash** LLM for streaming, context-aware chat interactions and summarizing complex medical text for end users.
-   **OCR Integration**: Utilizes **EasyOCR** for spatial extraction of text from uploaded prescription images prior to downstream classification.

### ⚙️ Software Engineering (Backend)
-   **Modern API Framework**: Built a highly performant, asynchronous API gateway using **FastAPI** and **Uvicorn** (ASGI).
-   **Singleton Services**: Models and embeddings are eagerly loaded at startup via centralized singletons (`ModelService`, `OCRService`, `KnowledgeService`, `LLMService`) to ensure zero-latency inference requests.
-   **Type Safety**: Enforced strict data validation and serialization using **Pydantic** schema boundaries.

### 🎨 Frontend Engineering
-   **Vanilla JS & TailwindCSS**: Built a highly responsive Single Page Application (SPA).
-   **Modern UI/UX**: Implemented a healthcare-themed design using elegant Glassmorphism aesthetics, clinical amber color schemes, dynamic DOM manipulation for XAI attribution highlighting, and micro-animations.
-   **Multi-Modal Routing**: The UI seamlessly handles raw text submission, multipart `FormData` image uploads, and SSE (Server-Sent Events) for real-time chatbot streaming.

### 🛡️ Deep Auditing & Security
-   **Strict Boundary Validation**: Maintained precise `HANDOFF_SCHEMA.json` rules verified by custom continuous integration auditing scripts.
-   **Type Safety**: 100% strict Python type hinting enforced across the backend.

### 🚀 DevOps & CI/CD
-   **Containerization**: Built highly optimized **Docker** images ensuring all dependencies (e.g., `libgl1-mesa-glx`) and PyTorch wheels are correctly resolved for efficient cloud deployments.
-   **Automated Testing**: Test-Driven Development (TDD) using **Pytest** with comprehensive mocking of ML services to ensure robust API contracts.

---

## ⚙️ Running Locally

### Prerequisites

-   Python 3.10+ (recommended to manage with `pyenv`)
-   Docker Desktop

### 1. Clone the Repository

```bash
git clone https://github.com/AbhiGTM19/MedVision-NLP.git
cd MedVision-NLP
```

### 2. Set Up the Python Environment

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=your_gemini_api_key
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
docker run -p 7860:7860 --env GEMINI_API_KEY=your_gemini_api_key <your-dockerhub-username>/medvision-nlp
```

The application will be available at `http://localhost:7860`.

---

## API Endpoints

### `/predict`
-   **Method**: `POST`
-   **Description**: Evaluates raw clinical text via Bio_ClinicalBERT for specialty classification.
-   **Response**:
    ```json
    {
      "specialty": "Cardiology",
      "confidence": 0.985,
      "word_attributions": [
        { "word": "chest", "score": 0.45 },
        { "word": "pain", "score": 0.52 }
      ]
    }
    ```

### `/predict-image`
-   **Method**: `POST`
-   **Description**: Evaluates prescription images using EasyOCR followed by Bio_ClinicalBERT classification.
-   **Body**: `multipart/form-data` with a single `file` field.

### `/predict-rag`
-   **Method**: `POST`
-   **Description**: Evaluates text via Bio_ClinicalBERT and additionally queries ChromaDB to generate a RAG-augmented summary using Gemini.
-   **Response**: Includes standard classification data plus a `rag_response` object containing the generated `answer` and retrieved `sources`.

### `/chat`
-   **Method**: `POST`
-   **Description**: A conversational endpoint that accepts a history of messages and streams responses (SSE) from the Gemini 2.5 Flash LLM.

### `/health`
-   **Method**: `GET`
-   **Description**: Returns the operational status of the inference engines, vector database, and LLM services.

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
