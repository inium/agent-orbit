from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """사용자 요청 모델"""

    thread_id: UUID = Field(default_factory=uuid4, description="스레드 고유 ID")
    message: str = Field(
        min_length=1, max_length=1000, description="사용자가 보낸 메시지"
    )


class ChatResponse(BaseModel):
    """서버 응답 모델"""

    thread_id: UUID = Field(..., description="스레드 고유 ID")
    response: str = Field(..., description="에이전트의 응답 메시지")
