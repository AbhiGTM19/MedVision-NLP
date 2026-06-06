import nltk
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import os

from core.config import settings
from schemas.predict import PredictionRequest, PredictionResponse
from services.model_service import model_service

router = APIRouter()

@router.get("/health")
def health_check() -> dict:
    nltk_ok = True
    try:
        nltk.data.path.append(settings.NLTK_DATA_PATH)
        nltk.corpus.stopwords.words("english")
        nltk.data.find("tokenizers/punkt")
    except Exception:
        nltk_ok = False

    models_status = {
        "fast_model": model_service.is_fast_ready(),
        "transformer_model": model_service.is_accurate_ready()
    }
    overall_status = "ok" if all(models_status.values()) and nltk_ok else "degraded"
    
    return {
        "status": overall_status,
        "models": models_status,
        "nltk_data": nltk_ok
    }

@router.get("/monitoring", response_class=HTMLResponse)
def get_monitoring_report():
    report_path = "static/monitoring_report.html"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Monitoring report not found. Run scripts/generate_evidently_report.py first.")
    with open(report_path, "r", encoding="utf-8") as f:
        return f.read()

@router.get("/model-info")
def model_info(model: str = "fast") -> dict:
    if model == "fast":
        if model_service.is_fast_ready():
            return model_service.fast_model.get_params()
    elif model == "accurate":
        if model_service.is_accurate_ready():
            return model_service.accurate_pipeline.model.config.to_dict()
    raise HTTPException(status_code=400, detail=f"Model '{model}' is not available.")

@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        if request.model_choice == "fast":
            label, conf, importances = model_service.predict_fast(request.review)
        elif request.model_choice == "accurate":
            label, conf, importances = model_service.predict_accurate(request.review)
        else:
            raise HTTPException(status_code=400, detail="Invalid model choice.")
        
        verdict = "Recommended" if label == "positive" else "Not Recommended"
        return PredictionResponse(
            prediction=label,
            confidence=conf,
            verdict=verdict,
            word_importances=importances,
            model_used=request.model_choice
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
