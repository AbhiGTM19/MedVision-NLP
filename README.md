---
title: Sentiment Scope
emoji: 🎬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# Sentiment Scope: AI Movie Review Analyzer

[![Deployment](https://img.shields.io/badge/Deployment-Render-000?style=for-the-badge&logo=render)](https://movie-review-sentiment-scope.onrender.com/)
[![Language](https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow-000?style=for-the-badge&logo=m&logoColor=F0523A)](https://mlflow.org/)

A full-stack web application that uses a machine learning model to perform real-time sentiment analysis on movie reviews. This project demonstrates an end-to-end MLOps workflow, from data preprocessing and hyperparameter tuning to containerized deployment.

**🚀 Live Application: [https://movie-review-sentiment-scope.onrender.com/](https://movie-review-sentiment-scope.onrender.com/)**

---

## 🌟 Architecture & Skills Highlighted

This project serves as a comprehensive portfolio piece demonstrating modern, production-ready software and machine learning engineering practices.

### 🧠 Machine Learning & MLOps
-   **Deep Learning (NLP)**: Fine-tuned a **DistilBERT Transformer** using Hugging Face pipelines for high-accuracy semantic analysis.
-   **Heuristics & Baselines**: Implemented **Scikit-Learn SGD Classifiers** with TF-IDF vectorization for ultra-low latency fallback inference.
-   **Explainable AI (XAI)**: Created a transparent glass-box mechanism to map token weights back to natural language, highlighting exactly *why* a model made its prediction.
-   **Experiment Tracking**: Managed hyperparameters and model lifecycle metrics using **MLflow** and optimized training with **Optuna**.
-   **Dynamic Model Loading**: Completely decoupled ML weights from the source code. Models are dynamically fetched at runtime via the **Hugging Face Hub API**, bypassing Git file-size limitations.

### ⚙️ Software Engineering (Backend)
-   **Modern API Framework**: Built a highly performant, asynchronous API gateway using **FastAPI** and **Uvicorn** (ASGI).
-   **N-Tier Architecture**: Strictly decoupled the application layer into Controllers (Routes), Services (Business Logic), and Core configurations, adhering to SOLID principles.
-   **Type Safety**: Enforced strict data validation and serialization using **Pydantic** models.

### 🎨 Frontend Engineering
-   **Vanilla JS & TailwindCSS**: Built a responsive, zero-dependency Single Page Application (SPA).
-   **Modern UI/UX**: Implemented a "Dark Mode Cinema" aesthetic using Glassmorphism, CSS View Transitions, and reveal-on-scroll animations.
-   **Client-Side Rendering**: Dynamically renders complex Explainable AI data and Mermaid.js architecture diagrams on the fly.

### 🚀 DevOps & CI/CD
-   **Containerization**: Built highly optimized, multi-stage **Docker** images. The container runs via a secure, non-root user specifically designed for PaaS environments.
-   **Continuous Integration**: Automated testing and linting pipelines via **GitHub Actions**.
-   **Testing**: Test-Driven Development (TDD) using **Pytest** to ensure robust API contracts and text-preprocessing functions.

---

## ⚙️ Running Locally

### Prerequisites

-   Python 3.14 (recommended to manage with `pyenv`)
-   Docker Desktop

### 1. Clone the Repository

```bash
git clone https://github.com/AbhiGTM19/Movie-Review-Sentiment-Classifier.git
cd Movie-Review-Sentiment-Classifier
```

### 2. Set Up the Python Environment

It is highly recommended to use the specific Python version this project was built with.

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
python -m nltk.downloader punkt stopwords
```

### 4. Train the Model

This script will run the Optuna tuning process and generate the model files (`movies_review_classifier.pkl` and `tfidf_vectorizer.pkl`) inside a `models/` directory.

```bash
python train.py
```

### 5. Run the Application

```bash
python main.py
```

The application will be available at `http://127.0.0.1:5000`.

---

## 🐳 Docker Deployment

### 1. Build the Docker Image

The `Dockerfile` is optimized for production. **If you are on an M1/M2 Mac**, you must build for the `linux/amd64` platform to deploy to Render.

```bash
# For M1/M2 Macs (Recommended for deployment)
docker build --platform linux/amd64 -t <your-dockerhub-username>/sentiment-scope .

# For other systems
docker build -t <your-dockerhub-username>/sentiment-scope .
```

### 2. Run the Container Locally

```bash
docker run -p 5000:5000 <your-dockerhub-username>/sentiment-scope
```

The application will be available at `http://localhost:5000`.

### 3. Push to Docker Hub and Deploy

Push the image to Docker Hub and then deploy it on Render by pointing to your public image URL.

```bash
docker push <your-dockerhub-username>/sentiment-scope
```

---

## API Endpoints

### `/predict`

-   **Method**: `POST`
-   **Body**: `{ "review": "The movie was absolutely fantastic!" }`
-   **Response**:
    ```json
    {
      "confidence": 0.987,
      "prediction": "positive",
      "top_words": ["fantastic", "absolutely"],
      "verdict": "Recommended"
    }
    ```

### `/model-info`

-   **Method**: `GET`
-   **Response**: Returns the model's hyperparameters.
    ```json
    {
      "alpha": 0.0001,
      "loss": "log",
      "penalty": "l2"
    }
    ```

---
## 🧑‍💻 Author

-   **Abhishek Gautam**
-   [LinkedIn](https://www.linkedin.com/in/abhishek-gautam-03b56926b/)
-   [GitHub](https://github.com/AbhiGTM19)
