from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """사용자 요청 모델"""

    thread_id: UUID = Field(default_factory=uuid4, description="스레드 고유 ID")
    message: str = Field(
        min_length=1, max_length=1000, description="사용자가 보낸 메시지"
    )


class TokenUsage(BaseModel):
    """이번 요청의 모든 LLM 호출에서 보고된 토큰 사용량입니다. 임베딩은 제외합니다."""

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ChatResponse(BaseModel):
    """서버 응답 모델"""

    thread_id: UUID = Field(..., description="스레드 고유 ID")
    response: str = Field(..., description="에이전트의 응답 메시지")
    usage: TokenUsage | None = Field(
        default=None, description="요청별 LLM 토큰 사용량. 보고된 사용량이 없으면 null"
    )
