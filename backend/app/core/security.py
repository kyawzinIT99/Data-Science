from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED

security = HTTPBearer()

# Simple static token for cloud access
CLOUD_ACCESS_TOKEN = "kyawzin_cloud_access_v4"

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != CLOUD_ACCESS_TOKEN:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
