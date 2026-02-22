import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.services.file_parser import extract_text, extract_dataframe, SUPPORTED_EXTENSIONS
from app.services.analyzer import analyze_document, generate_dashboard
from app.services.report import generate_pdf_report
from app.services.ppt_report import generate_pptx_report

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


def _get_original_filename(file_id: str) -> str:
    """Get original extension for display purposes."""
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return f"document{ext}"
    return "document"


@router.get("/export/{file_id}/pdf")
async def export_pdf(file_id: str, include_charts: bool = True):
    file_path = _find_file_path(file_id)
    text = extract_text(file_path)
    df = extract_dataframe(file_path)

    analysis = analyze_document(file_id, text, df)

    dashboard = None
    if include_charts:
        dashboard = generate_dashboard(file_id, text, df)

    filename = _get_original_filename(file_id)
    pdf_buffer = generate_pdf_report(filename, analysis, dashboard)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="analysis_report_{file_id[:8]}.pdf"'},
    )


@router.get("/export/{file_id}/pptx")
async def export_pptx(file_id: str, include_charts: bool = True):
    file_path = _find_file_path(file_id)
    text = extract_text(file_path)
    df = extract_dataframe(file_path)

    analysis = analyze_document(file_id, text, df)

    dashboard = None
    if include_charts:
        dashboard = generate_dashboard(file_id, text, df)

    filename = _get_original_filename(file_id)
    pptx_buffer = generate_pptx_report(filename, analysis, dashboard)

    return StreamingResponse(
        pptx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="analysis_report_{file_id[:8]}.pptx"'},
    )


@router.get("/export/{file_id}/json")
async def export_json(file_id: str):
    file_path = _find_file_path(file_id)
    text = extract_text(file_path)
    df = extract_dataframe(file_path)

    analysis = analyze_document(file_id, text, df)
    dashboard = generate_dashboard(file_id, text, df)

    return {
        "analysis": analysis.model_dump(),
        "dashboard": dashboard.model_dump(),
    }
