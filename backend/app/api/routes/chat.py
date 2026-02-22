from fastapi import APIRouter, HTTPException

from app.services.chat import chat_with_document, get_chat_sessions, get_chat_session, delete_chat_session
from app.models.schemas import ChatRequest, ChatResponse, ChatSession

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return chat_with_document(
        file_id=request.file_id,
        question=request.question,
        chat_history=request.chat_history,
        session_id=request.session_id,
        language=request.language,
    )


@router.get("/chat/sessions/{file_id}", response_model=list[ChatSession])
async def list_sessions(file_id: str):
    return get_chat_sessions(file_id)


@router.get("/chat/session/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str):
    if not delete_chat_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}
