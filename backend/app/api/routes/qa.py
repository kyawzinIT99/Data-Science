import logging
import os
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.file_parser import extract_dataframe, get_file_extension, SUPPORTED_EXTENSIONS
from app.models.schemas import AnalysisRequest

router = APIRouter()

def _find_file_path(file_id: str) -> str:
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
    raise HTTPException(status_code=404, detail="File not found")

@router.post("/qa")
async def check_data_quality(request: AnalysisRequest):
    """
    Scans the uploaded dataset and generates a QA 'health report'.
    If the score is too low, it flags the file for AI Auto-Refinement.
    """
    try:
        file_path = _find_file_path(request.file_id)
        df = extract_dataframe(file_path)
        
        if df is None or df.empty:
            return {
                "requires_refinement": True,
                "score": 0,
                "issues": ["Dataset is completely empty or could not be parsed."]
            }
            
        total_rows = len(df)
        issues = []
        deductions = 0
        
        # 1. Missing Data Check
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()
        null_percentage = (total_nulls / (total_rows * len(df.columns))) * 100
        
        if null_percentage > 5:
            issues.append(f"High missing data rate ({null_percentage:.1f}%).")
            deductions += min(30, int(null_percentage * 2))
            
        for col, count in null_counts.items():
            if count > 0:
                col_null_pct = (count / total_rows) * 100
                if col_null_pct > 20:
                    issues.append(f"Column '{col}' is missing {col_null_pct:.1f}% of values.")
                    deductions += 10
                    
        # 2. Duplicate Check
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            dup_pct = (duplicate_count / total_rows) * 100
            issues.append(f"Found {duplicate_count} exactly duplicated rows ({dup_pct:.1f}%).")
            deductions += min(20, int(dup_pct * 2))
            
        # 3. Numeric Outlier Check
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Check for infinites
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                issues.append(f"Column '{col}' contains {inf_count} infinite values.")
                deductions += 15
                
            # Very basic robust z-score check for extreme madness (e.g. 1e12 in a column of 1000s)
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                extreme_high = (df[col] > q3 + 10 * iqr).sum()
                if extreme_high > 0:
                    issues.append(f"Column '{col}' has {extreme_high} extreme statistical outliers.")
                    deductions += 10

        # Calculate final score
        score = max(0, 100 - deductions)
        
        # Determine if it needs refinement
        requires_refinement = score < 95 or len(issues) > 0
        
        return {
            "score": score,
            "requires_refinement": requires_refinement,
            "issues": issues,
            "row_count": total_rows,
            "col_count": len(df.columns)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in /qa for file {request.file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
