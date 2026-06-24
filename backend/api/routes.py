
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse

from core.rate_limiter import rate_limit_dependency
from schemas.predict import (
    ChatRequest,
    PredictionRAGResponse,
    PredictionRequest,
    PredictionResponse,
)
from services.llm_service import llm_service
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


@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """
    Predicts medical specialty from raw clinical text and provides XAI word attributions.
    """
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Input text is too short to be meaningful clinical text.")

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

@router.post("/predict-rag", response_model=PredictionRAGResponse)
async def predict_rag(request: PredictionRequest, _rate_limit: None = Depends(rate_limit_dependency)):
    """
    Predicts medical specialty from raw clinical text, provides XAI word attributions, and returns a RAG response.
    """
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Input text is too short to be meaningful clinical text.")

    try:
        specialty, confidence, word_attributions, rag_response = await model_service.predict_with_rag(request.text)
        return PredictionRAGResponse(
            specialty=specialty,
            confidence=confidence,
            word_attributions=word_attributions,
            extracted_text=request.text,
            rag_response=rag_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest, _rate_limit: None = Depends(rate_limit_dependency)):
    """
    Interactive chat using LLM and clinical context.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Chat messages cannot be empty.")

    return StreamingResponse(
        llm_service.generate_chat_response_stream(request.messages),
        media_type="text/event-stream"
    )

@router.post("/predict-image", response_model=PredictionResponse)
async def predict_image(response: Response, file: UploadFile = File(...)):
    """
    DEPRECATED: Accepts an image, runs OCR via Tesseract OCR, passes text to Bio_ClinicalBERT for 
    sequence classification, and provides XAI word attributions.
    """
    response.headers["X-Deprecated"] = "Use /predict for text input. OCR path deprecated."
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
