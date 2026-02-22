from fastapi import APIRouter, HTTPException
from app.services.file_parser import extract_dataframe
from app.services.causal import generate_causal_network, CausalNetwork
from app.api.routes.export import _find_file_path

router = APIRouter()

@router.get("/causal/{file_id}", response_model=CausalNetwork)
async def get_causal_network(file_id: str):
    try:
        file_path = _find_file_path(file_id)
        df = extract_dataframe(file_path)
        if df is None:
            raise HTTPException(status_code=400, detail="Could not extract dataframe from file")
        
        return generate_causal_network(df)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
