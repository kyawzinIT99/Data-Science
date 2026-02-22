from fastapi import APIRouter, HTTPException

from app.services.compare import compare_files
from app.models.schemas import CompareRequest, CompareResponse

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest):
    if len(request.file_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 files required for comparison")
    if len(request.file_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files for comparison")
    try:
        return compare_files(request.file_ids, request.custom_prompt)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
