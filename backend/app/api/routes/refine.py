import logging
import os
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.file_parser import extract_dataframe, get_file_extension, SUPPORTED_EXTENSIONS
from app.models.schemas import AnalysisRequest
from app.services.analyzer import refine_dataframe

router = APIRouter()

def _find_file_path(file_id: str) -> str:
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
    raise HTTPException(status_code=404, detail="File not found")

@router.post("/refine")
async def refine_dataset(request: AnalysisRequest):
    """
    The AI Auto-Refinement worker endpoint.
    Retrieves the messy dataset, runs advanced AI cleaning/imputation logic, 
    and saves the clean payload back to disk for the Dashboard engine.
    """
    try:
        file_path = _find_file_path(request.file_id)
        df = extract_dataframe(file_path)
        
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Dataset is completely empty or could not be parsed.")
            
        print(f"Refining data for file {request.file_id}. Initial rows: {len(df)}")
        
        # 1. De-duplication
        df.drop_duplicates(inplace=True)
        
        # 2. Advanced Imputation & Outlier Removal (Using our existing rigorous cleaner)
        df_clean = refine_dataframe(df)

        print(f"Finished Refinement. Final rows: {len(df_clean)}")

        # 3. Overwrite the file on disk so that the dashboard loads the pristine data
        df_clean.to_csv(file_path, index=False)
        
        return {
            "success": True,
            "message": f"Successfully refined dataset. Cleaned {len(df) - len(df_clean)} toxic/duplicate rows.",
            "final_rows": len(df_clean),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in /refine for file {request.file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
