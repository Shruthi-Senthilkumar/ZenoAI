"""POST /chat/message (Backend Spec §12)."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.logic.chat import chat_reply
from backend.schemas.chat import ChatReplyResponse

router = APIRouter()


class ChatMessageRequest(BaseModel):
    student_id: str
    message: str


@router.post("/chat/message", response_model=ChatReplyResponse)
def post_chat_message(payload: ChatMessageRequest) -> ChatReplyResponse:
    return chat_reply(payload.student_id, payload.message)
