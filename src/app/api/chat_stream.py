import asyncio
from collections.abc import AsyncIterator
import json
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import HumanMessage
from app.api.schemas.chat import ChatRequest
from app.api.services.usage import collect_usage

logger = logging.getLogger(__name__)
router = APIRouter()


def encode_event(event: str, data: dict[str, object]) -> str:
    """이벤트 이름과 JSON 데이터를 SSE 형식으로 변환합니다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "/chat/stream",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    """상위 에이전트의 답변을 SSE 이벤트로 반환합니다."""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="질문을 입력해 주세요.")

    async def generate() -> AsyncIterator[str]:
        """상위 모델의 텍스트와 스트림 종료 상태를 전달합니다."""
        yield encode_event("start", {"thread_id": str(body.thread_id)})

        # usage_callback 객체를 생성하여 사용량 정보를 수집합니다.
        # UsageMetadataCallbackHandler는 LangChain에서 모델 사용량을 추적하는 콜백 핸들러입니다.
        # - 직접 텍스트를 토큰으로 계산하는 것이 아니라, 모델이 응답에 담아준 usage_metadata를 읽습니다.
        usage_callback = UsageMetadataCallbackHandler()
        has_text = False

        try:
            async for chunk, metadata in request.app.state.supervisor_agent.astream(
                {"messages": [HumanMessage(content=message)]},
                config={
                    "configurable": {"thread_id": str(body.thread_id)},
                    "callbacks": [usage_callback],
                },
                stream_mode="messages",
            ):
                if (
                    metadata.get("langgraph_node") == "model"
                    and "supervisor_output" in metadata.get("tags", [])
                    and chunk.text
                ):
                    has_text = True
                    yield encode_event("token", {"text": chunk.text})

            if not has_text:
                yield encode_event(
                    "error", {"message": "답변 내용을 확인할 수 없습니다."}
                )
                return

            usage = collect_usage(usage_callback)

            yield encode_event(
                "done",
                {
                    "thread_id": str(body.thread_id),
                    "usage": usage.model_dump() if usage is not None else None,
                },
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("에이전트 스트리밍 실패")
            yield encode_event(
                "error", {"message": "답변 생성에 실패했습니다. 다시 시도해주세요."}
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
