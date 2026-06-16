import os
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, FileResponse

from core.config import settings, BASE_DIR
from schemas.predict import PredictionRequest, PredictionResponse
from services.model_service import model_service

router = APIRouter()

@router.get("/health")
def health_check() -> dict:
    models_status = {
        "models_loaded": model_service.is_ready()
    }
    overall_status = "ok" if all(models_status.values()) else "degraded"
    
    return {
        "status": overall_status,
        "models": models_status
    }

@router.get("/monitoring", response_class=FileResponse)
def get_monitoring_report():
    report_path = BASE_DIR.parent / "frontend" / "static" / "monitoring_report.html"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Monitoring report not found.")
    return FileResponse(report_path)

@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """
    Predicts medical specialty from raw clinical text and provides XAI word attributions.
    """
    try:
        specialty, confidence, word_attributions = model_service.extract_from_text(request.text)
        return PredictionResponse(
            specialty=specialty,
            confidence=confidence,
            word_attributions=word_attributions,
            extracted_text=request.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-image", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)):
    """
    Accepts an image, runs OCR via Tesseract OCR, passes text to Bio_ClinicalBERT for 
    sequence classification, and provides XAI word attributions.
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        # Extract text and specialty
        extracted_text, specialty, confidence, word_attributions = model_service.extract_from_image(image_bytes)
        
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the image.")
            
        return PredictionResponse(
            specialty=specialty,
            confidence=confidence,
            word_attributions=word_attributions,
            extracted_text=extracted_text
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
