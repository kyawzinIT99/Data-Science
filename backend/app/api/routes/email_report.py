import os
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.file_parser import extract_text, extract_dataframe, SUPPORTED_EXTENSIONS
from app.services.analyzer import analyze_document, generate_dashboard
from app.services.report import generate_pdf_report
from app.services.email import send_report_email
from app.models.schemas import EmailReportRequest

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


@router.post("/email-report")
async def email_report(request: EmailReportRequest):
    file_path = _find_file_path(request.file_id)
    text = extract_text(file_path)
    df = extract_dataframe(file_path)

    analysis = analyze_document(request.file_id, text, df)
    dashboard = None
    if request.include_charts:
        dashboard = generate_dashboard(request.file_id, text, df)

    filename = os.path.basename(file_path)
    pdf_buffer = generate_pdf_report(filename, analysis, dashboard)

    try:
        send_report_email(request.email, filename, pdf_buffer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"status": "sent", "email": request.email}
