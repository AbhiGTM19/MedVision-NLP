from fastapi.testclient import TestClient

from main import app
from schemas.predict import WordAttribution
from services.model_service import model_service

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code in [200, 500]
    data = response.json()
    assert "status" in data
    assert "models" in data
    assert "models_loaded" in data["models"]

def test_metrics_route():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_predict_text_mocked(monkeypatch):
    # Mock the extract_from_text function so we don't need models loaded
    def mock_extract(text):
        return "Neurology", 0.99, [WordAttribution(word="Aspirin", score=0.85)]
    
    monkeypatch.setattr(model_service, "extract_from_text", mock_extract)

    response = client.post("/predict", json={"text": "Patient taking Aspirin."})
    assert response.status_code == 200
    data = response.json()
    assert "specialty" in data
    assert data["specialty"] == "Neurology"
    assert "confidence" in data
    assert data["confidence"] == 0.99
    assert "word_attributions" in data
    assert len(data["word_attributions"]) == 1
    assert data["word_attributions"][0]["word"] == "Aspirin"

def test_predict_image_mocked(monkeypatch):
    # Mock the extract_from_image function
    def mock_extract_image(image_bytes):
        return "Transcribed text here.", "Cardiology", 0.95, [WordAttribution(word="Tylenol", score=0.90)]

    monkeypatch.setattr(model_service, "extract_from_image", mock_extract_image)

    # Use a dummy file payload
    files = {"file": ("test.png", b"dummy_image_bytes", "image/png")}
    response = client.post("/predict-image", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "specialty" in data
    assert data["specialty"] == "Cardiology"
    assert "confidence" in data
    assert data["confidence"] == 0.95
    assert "extracted_text" in data
    assert data["extracted_text"] == "Transcribed text here."
    assert "word_attributions" in data
    assert len(data["word_attributions"]) == 1
    assert data["word_attributions"][0]["word"] == "Tylenol"

def test_predict_empty_text():
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422  # Unprocessable Entity due to min_length=1

def test_predict_massive_text():
    response = client.post("/predict", json={"text": "A" * 5001})
    assert response.status_code == 422  # Unprocessable Entity due to max_length=5000
