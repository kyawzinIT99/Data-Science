import os
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.file_parser import extract_dataframe, SUPPORTED_EXTENSIONS
from app.services.cleaning import assess_data_quality
from app.models.schemas import AnalysisRequest, DataCleaningResponse

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


@router.post("/clean", response_model=DataCleaningResponse)
async def clean(request: AnalysisRequest):
    file_path = _find_file_path(request.file_id)
    df = extract_dataframe(file_path)
    if df is None:
        raise HTTPException(
            status_code=400,
            detail="Data cleaning is only available for structured data files (CSV, Excel, JSON)",
        )
    return assess_data_quality(request.file_id, df)
