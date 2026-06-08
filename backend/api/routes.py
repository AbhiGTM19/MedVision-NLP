import os
import io
import numpy as np
from PIL import Image
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, FileResponse

from core.config import settings, BASE_DIR
from schemas.predict import PredictionRequest, PredictionResponse
from services.model_service import model_service

router = APIRouter()

@router.get("/health")
def health_check() -> dict:
    models_status = {
        "dual_stream_fusion": model_service.is_ready()
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
    Predicts medical entities from raw clinical text.
    """
    try:
        entities = model_service.extract_from_text(request.text)
        return PredictionResponse(entities=entities)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-image", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)):
    """
    Accepts an image, runs OCR via EasyOCR, calculates spatial vision metadata, 
    and returns token-level NER predictions.
    """
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        # Convert to numpy array
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        # Extract text and entities
        extracted_text, entities = model_service.extract_from_image(image_np)
        
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the image.")
            
        return PredictionResponse(entities=entities, extracted_text=extracted_text)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
