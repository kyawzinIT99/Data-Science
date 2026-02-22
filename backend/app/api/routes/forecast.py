import os
import pandas as pd
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.file_parser import SUPPORTED_EXTENSIONS
from app.services.forecast import PriceForecaster
from app.models.schemas import ForecastRequest, ForecastResponse, ForecastDataPoint
from app.utils.serialization import cleanup_serializable

router = APIRouter()


def _find_file_path(file_id: str) -> str:
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
        legacy_path = os.path.join("./uploads", f"{file_id}{ext}")
        if os.path.exists(legacy_path):
            return legacy_path
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest):
    file_path = _find_file_path(request.file_id)
    
    if not file_path.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=400, 
            detail="Forecasting currently only supports CSV and Excel files"
        )

    try:
        # Load data first to check columns
        ext = os.path.splitext(file_path)[1].lower()
        
        # Check if columns exist (we'll read just the header to be fast)
        if ext == '.csv':
            try:
                df_head = pd.read_csv(file_path, nrows=0)
            except Exception:
                df_head = pd.read_csv(file_path, encoding='latin1', nrows=0)
        else:
            df_head = pd.read_excel(file_path, nrows=0)
            
        available_cols = df_head.columns.tolist()
        if request.date_column not in available_cols:
            raise HTTPException(status_code=400, detail=f"Column '{request.date_column}' not found.")
        if request.price_column not in available_cols:
            raise HTTPException(status_code=400, detail=f"Column '{request.price_column}' not found.")

        # --- Modal Remote Execution Hook ---
        from app.utils.modal import get_modal_func
        modal_forecast_run = get_modal_func("run_forecast")
        
        if modal_forecast_run:
            try:
                logger.info("Offloading standalone forecast to Modal...")
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                remote_result = modal_forecast_run.remote(
                    file_content,
                    ext,
                    request.date_column,
                    request.price_column
                )
                forecast_data_raw = remote_result["forecast"]
                metrics = remote_result["metrics"]
                
                return cleanup_serializable(ForecastResponse(
                    file_id=request.file_id,
                    forecast=[ForecastDataPoint(date=d["Forecast_Date"], price=d["Predicted_Price"]) for d in forecast_data_raw],
                    metrics=metrics
                ))
            except Exception as e:
                logger.warning(f"Modal standalone forecast failed, falling back to local: {e}")

        # Local Fallback
        if ext == '.csv':
            try:
                df = pd.read_csv(file_path)
            except Exception:
                df = pd.read_csv(file_path, encoding='latin1')
        else:
            df = pd.read_excel(file_path)

        forecaster = PriceForecaster(
            file_path=file_path,
            date_column=request.date_column,
            price_column=request.price_column
        )
        forecaster.df = df
        forecaster.load_data()
        metrics = forecaster.train_model()
        forecast_df = forecaster.predict_next_months(request.months)
        
        forecast_data = []
        for _, row in forecast_df.iterrows():
            # Handle if row["Forecast_Date"] is a string or datetime
            f_date = row["Forecast_Date"]
            if hasattr(f_date, "strftime"):
                f_date = f_date.strftime("%Y-%m-%d")
                
            forecast_data.append(
                ForecastDataPoint(
                    date=str(f_date),
                    price=float(row["Predicted_Price"])
                )
            )
            
        return cleanup_serializable(ForecastResponse(
            file_id=request.file_id,
            forecast=forecast_data,
            metrics=metrics
        ))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")
