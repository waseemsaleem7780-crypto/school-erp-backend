from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.chatbot_service import get_chatbot_response
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    role: str


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """
    User ka message lo, AI se response lo, wapas bhejo.
    """
    if not request.message or len(request.message.strip()) == 0:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if len(request.message) > 1000:
        raise HTTPException(status_code=400, detail="Message too long (max 1000 chars)")

    reply = get_chatbot_response(
        user_message=request.message,
        user_role=current_user.get("role", "user"),
        user_name=current_user.get("name", "User"),
        school_id=school_id
    )

    return {
        "reply": reply,
        "role": current_user.get("role", "user")
    }