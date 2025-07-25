import requests

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code in [200, 500], "Unexpected status code"
    data = response.json()
    assert "status" in data, "Missing 'status' in response"
    assert "models" in data, "Missing 'models' in response"
    assert "fast_model" in data["models"], "Missing fast_model key"
    assert "transformer_model" in data["models"], "Missing transformer_model key"
    assert "nltk_data" in data, "Missing nltk_data key"
    assert data["status"] in ["ok", "degraded"], "Unexpected status message"

def test_predict_fast():
    data = {
        "review": "The movie was absolutely fantastic!",
        "model_choice": "fast"
    }
    response = requests.post(f"{BASE_URL}/predict", json=data)
    assert response.status_code == 200, "Fast model: status code not 200"
    json_data = response.json()
    assert "prediction" in json_data, "Missing prediction"
    assert json_data["model_used"] == "fast", "Model used mismatch"

def test_predict_accurate():
    data = {
        "review": "The movie was absolutely terrible.",
        "model_choice": "accurate"
    }
    response = requests.post(f"{BASE_URL}/predict", json=data)
    assert response.status_code == 200, "Accurate model: status code not 200"
    json_data = response.json()
    assert "prediction" in json_data, "Missing prediction"
    assert json_data["model_used"] == "accurate", "Model used mismatch"