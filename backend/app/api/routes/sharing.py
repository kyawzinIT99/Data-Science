import os
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.database import shares_table, files_table, Share, File
from app.services.file_parser import extract_text, extract_dataframe, SUPPORTED_EXTENSIONS
from app.services.analyzer import analyze_document, generate_dashboard
from app.models.schemas import ShareRequest, ShareResponse, SharedReportResponse

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


@router.post("/share", response_model=ShareResponse)
async def create_share(request: ShareRequest):
    _find_file_path(request.file_id)  # validate file exists

    share_id = str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=request.expires_hours)

    # Get filename from db or fallback
    file_record = files_table.get(File.file_id == request.file_id)
    filename = file_record["filename"] if file_record else "document"

    shares_table.insert({
        "share_id": share_id,
        "file_id": request.file_id,
        "filename": filename,
        "include_analysis": request.include_analysis,
        "include_dashboard": request.include_dashboard,
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
    })

    share_url = f"{settings.SHARE_BASE_URL}?id={share_id}"

    return ShareResponse(
        share_id=share_id,
        share_url=share_url,
        expires_at=expires.isoformat(),
    )


@router.get("/shared/{share_id}", response_model=SharedReportResponse)
async def get_shared_report(share_id: str):
    share = shares_table.get(Share.share_id == share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Shared report not found")

    expires_at = datetime.fromisoformat(share["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        shares_table.remove(Share.share_id == share_id)
        raise HTTPException(status_code=410, detail="This shared link has expired")

    file_id = share["file_id"]
    file_path = _find_file_path(file_id)
    text = extract_text(file_path)
    df = extract_dataframe(file_path)

    analysis = None
    dashboard = None

    if share.get("include_analysis", True):
        analysis = analyze_document(file_id, text, df)

    if share.get("include_dashboard", True):
        dashboard = generate_dashboard(file_id, text, df)

    return SharedReportResponse(
        filename=share.get("filename", "document"),
        analysis=analysis,
        dashboard=dashboard,
        created_at=share["created_at"],
    )
