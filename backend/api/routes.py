import os

import nltk
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from core.config import settings
from schemas.predict import PredictionRequest, PredictionResponse
from services.model_service import model_service
from services.ocr_service import ocr_service

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
    report_path = settings.BASE_DIR.parent / "frontend" / "static" / "monitoring_report.html"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Monitoring report not found. Run backend/scripts/generate_evidently_report.py first.")
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
    """
    Predicts the medical specialty from raw clinical text.
    """
    try:
        if request.model_choice == "fast":
            prediction, confidence, importances = model_service.predict_fast(request.text)
        elif request.model_choice == "accurate":
            prediction, confidence, importances = model_service.predict_accurate(request.text)
        else:
            raise HTTPException(status_code=400, detail="Invalid model choice.")
        
        explanation = f"Patient likely belongs to the {prediction} department."
        return PredictionResponse(
            prediction=prediction,
            confidence=confidence,
            explanation=explanation,
            word_importances=importances,
            model_used=request.model_choice
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-image")
async def predict_image(file: UploadFile = File(...)):
    """
    Accepts an image, runs OCR via EasyOCR, and returns the specialty prediction.
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        # Extract text via EasyOCR
        extracted_text = ocr_service.extract_text(image_bytes)
        
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the image.")
            
        # Predict specialty
        prediction, confidence, importances = model_service.predict_fast(extracted_text)
        
        return {
            "extracted_text": extracted_text,
            "prediction": prediction,
            "confidence": confidence,
            "top_features": importances
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
