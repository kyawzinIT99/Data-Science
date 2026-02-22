import logging
import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

# Setup logging
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.file_parser import extract_text, extract_dataframe, get_file_extension, SUPPORTED_EXTENSIONS
from app.services.analyzer import analyze_document, generate_dashboard
from app.models.schemas import AnalysisRequest, AnalysisResponse, DashboardResponse

router = APIRouter()


def _find_file_path(file_id: str) -> str:
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
        # Fallback to legacy path
        legacy_path = os.path.join("./uploads", f"{file_id}{ext}")
        if os.path.exists(legacy_path):
            return legacy_path
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    try:
        file_path = _find_file_path(request.file_id)
        text = extract_text(file_path)
        df = extract_dataframe(file_path)
        return analyze_document(request.file_id, text, df, request.custom_prompt, language=request.language)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in /analyze for file {request.file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboard", response_model=DashboardResponse)
async def dashboard(request: AnalysisRequest):
    try:
        file_path = _find_file_path(request.file_id)
        text = extract_text(file_path)
        df = extract_dataframe(file_path)
        return generate_dashboard(request.file_id, text, df, language=request.language)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in /dashboard for file {request.file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
