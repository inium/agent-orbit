import logging
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Security
from fastapi.security import APIKeyHeader
from langchain_core.messages import BaseMessage

from app.api.schemas.admin import ConversationMessage, ConversationResponse
from app.api.services.checkpoint import get_conversation_checkpoint
from app.config.admin import admin_settings

logger = logging.getLogger(__name__)
api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


def require_admin(api_key: str | None = Security(api_key_header)) -> None:
    """관리자 키를 검증하며, 키가 설정되지 않으면 접근을 차단합니다."""
    expected = admin_settings.api_key
    if expected is None or not expected.get_secret_value():
        raise HTTPException(status_code=503, detail="관리자 API가 설정되지 않았습니다.")
    if api_key is None or not secrets.compare_digest(
        api_key.encode(), expected.get_secret_value().encode()
    ):
        raise HTTPException(status_code=403, detail="관리자 인증이 필요합니다.")


router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def serialize_message(message: BaseMessage | dict) -> ConversationMessage:
    """CLI와 동일하게 역할·본문·도구 호출 정보를 반환합니다."""
    if isinstance(message, BaseMessage):
        return ConversationMessage(
            role=message.type,
            content=message.content,
            name=message.name,
            tool_calls=getattr(message, "tool_calls", None),
        )
    return ConversationMessage(
        role=message.get("type", message.get("role", "unknown")),
        content=message.get("content", ""),
        name=message.get("name"),
        tool_calls=message.get("tool_calls"),
    )


@router.get("/conversations/{thread_id}", response_model=ConversationResponse)
async def get_conversation(
    thread_id: UUID,
    request: Request,
    namespace: str = Query(
        default="", max_length=1000, description="체크포인트 namespace"
    ),
) -> ConversationResponse:
    """관리자 인증 후 PostgreSQL 대화의 최신 메시지를 조회합니다."""
    try:
        saved = await get_conversation_checkpoint(
            request.app.state.checkpointer, str(thread_id), namespace
        )
        if saved is None:
            raise HTTPException(status_code=404, detail="저장된 대화가 없습니다.")
        messages = [
            serialize_message(message)
            for message in saved.checkpoint.get("channel_values", {}).get(
                "messages", []
            )
        ]
        return ConversationResponse(
            thread_id=thread_id,
            checkpoint_ns=namespace,
            checkpoint_id=saved.checkpoint["id"],
            message_count=len(messages),
            messages=messages,
        )
    except HTTPException:
        raise
    except Exception as error:
        # 연결 정보나 대화 내용이 로그에 노출되지 않도록 예외 종류만 기록합니다.
        logger.error("대화 조회 실패: %s", type(error).__name__)
        raise HTTPException(
            status_code=503, detail="대화내역을 조회하지 못했습니다."
        ) from None
