import os
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.file_parser import extract_text, SUPPORTED_EXTENSIONS
from app.services.language import detect_language, get_language_name
from app.models.schemas import AnalysisRequest, LanguageDetectResponse

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


@router.post("/detect-language", response_model=LanguageDetectResponse)
async def detect_lang(request: AnalysisRequest):
    file_path = _find_file_path(request.file_id)
    text = extract_text(file_path)
    lang_code, confidence = detect_language(text)
    return LanguageDetectResponse(
        file_id=request.file_id,
        detected_language=get_language_name(lang_code),
        confidence=confidence,
    )
