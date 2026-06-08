from fastapi.testclient import TestClient

from main import app
from services.model_service import model_service
from services.ocr_service import ocr_service
from schemas.predict import EntitySchema

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code in [200, 500]
    data = response.json()
    assert "status" in data
    assert "models" in data
    assert "dual_stream_fusion" in data["models"]

def test_metrics_route():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_predict_text_mocked(monkeypatch):
    # Mock the extract_from_text function so we don't need models loaded
    def mock_extract(text):
        return [
            EntitySchema(word="Aspirin", tag="B-MEDICATIONS", confidence=0.99)
        ]
    
    monkeypatch.setattr(model_service, "extract_from_text", mock_extract)

    response = client.post("/predict", json={"text": "Patient taking Aspirin."})
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert len(data["entities"]) == 1
    assert data["entities"][0]["word"] == "Aspirin"
    assert data["entities"][0]["tag"] == "B-MEDICATIONS"

def test_predict_image_mocked(monkeypatch):
    # Mock OCR processing
    def mock_ocr(file):
        return [
            EntitySchema(word="Tylenol", tag="B-MEDICATIONS", confidence=0.95)
        ]

    monkeypatch.setattr(ocr_service, "process_prescription", mock_ocr)

    # Use a dummy file payload
    files = {"file": ("test.png", b"dummy_image_bytes", "image/png")}
    response = client.post("/predict-image", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert len(data["entities"]) == 1
    assert data["entities"][0]["word"] == "Tylenol"
    assert data["entities"][0]["tag"] == "B-MEDICATIONS"

def test_predict_empty_text():
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422  # Unprocessable Entity due to min_length=1

def test_predict_massive_text():
    response = client.post("/predict", json={"text": "A" * 5001})
    assert response.status_code == 422  # Unprocessable Entity due to max_length=5000
