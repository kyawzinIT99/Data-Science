from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    # Hardcoded credentials as requested by user
    if req.username == "kyawzin" and req.password == "Kyawzin@123456":
        return {
            "access_token": "kyawzin_cloud_access_v4", 
            "token_type": "bearer"
        }
    
    raise HTTPException(status_code=401, detail="Invalid username or password")
