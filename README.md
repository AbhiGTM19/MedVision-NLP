# MLOps Final Assignment — Movie Review Classification

This project is part of an MLOps final assignment focused on building, deploying, and sharing a machine learning model for sentiment classification of movie reviews. The model uses NLP techniques and libraries like `nltk`, `scikit-learn`, and is tracked via `MLflow`.

---

## Features

- Movie review classifier using ML pipeline
- Integrated with MLflow for tracking experiments
- Dockerized for consistent and reproducible deployment
- NLTK-based preprocessing with stopwords
- Can be shared via Docker Hub or offline `.tar` image

---

## Run with Docker (Online Method)

If you have Docker installed, pull and run directly from Docker Hub:

```bash
docker pull yugandhar0458/mlops_team10:latest
docker run -p 5000:5000 yugandhar0458/mlops_team10:latest
