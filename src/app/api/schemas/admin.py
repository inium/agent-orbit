from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ConversationMessage(BaseModel):
    """체크포인트에서 복원한 메시지입니다."""

    role: str
    content: str | list[str | dict[str, Any]]
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ConversationResponse(BaseModel):
    """최신 대화 상태입니다. 요약 이전의 전체 기록과는 다를 수 있습니다."""

    thread_id: UUID
    checkpoint_ns: str
    checkpoint_id: str
    message_count: int
    messages: list[ConversationMessage]
