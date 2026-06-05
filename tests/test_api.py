from fastapi.testclient import TestClient

from main import app
from services.model_service import model_service

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code in [200, 500]
    data = response.json()
    assert "status" in data
    assert "models" in data
    assert "nltk_data" in data

def test_predict_fast_mocked(monkeypatch):
    # Mock the predict_fast function so we don't need models loaded
    def mock_predict_fast(review):
        return "positive", 0.99, {"good": 0.5}
    
    monkeypatch.setattr(model_service, "predict_fast", mock_predict_fast)
    monkeypatch.setattr(model_service, "is_fast_ready", lambda: True)

    response = client.post("/predict", json={"review": "This is great!", "model_choice": "fast"})
    assert response.status_code == 200
    assert response.json()["prediction"] == "positive"
    assert response.json()["model_used"] == "fast"

def test_predict_invalid_model():
    response = client.post("/predict", json={"review": "Testing", "model_choice": "nonexistent"})
    assert response.status_code == 400

def test_predict_empty_review():
    response = client.post("/predict", json={"review": "", "model_choice": "fast"})
    assert response.status_code == 422  # Unprocessable Entity due to min_length=1

def test_predict_massive_review():
    response = client.post("/predict", json={"review": "A" * 5001, "model_choice": "fast"})
    assert response.status_code == 422  # Unprocessable Entity due to max_length=5000
