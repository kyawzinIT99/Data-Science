from fastapi import APIRouter

from app.services.apikeys import save_user_api_key, get_key_status, remove_user_api_key
from app.models.schemas import ApiKeyRequest, ApiKeyStatus

router = APIRouter()


@router.get("/settings/api-key", response_model=ApiKeyStatus)
async def get_api_key():
    status = get_key_status()
    return ApiKeyStatus(**status)


@router.post("/settings/api-key", response_model=ApiKeyStatus)
async def set_api_key(request: ApiKeyRequest):
    save_user_api_key(request.openai_api_key)
    status = get_key_status()
    return ApiKeyStatus(**status)


@router.delete("/settings/api-key")
async def delete_api_key():
    remove_user_api_key()
    return {"status": "removed"}
