from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from uuid import uuid4, UUID
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.agents.supervisor_agent import SupervisorAgent

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """서버 시작 시 대화에 사용할 에이전트를 생성합니다."""
    app.state.supervisor_agent = SupervisorAgent().get_agent()
    yield


app = FastAPI(title="길동이 API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """사용자 메시지를 받아 에이전트의 응답을 반환합니다."""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    try:
        # 사용자 메시지를 HumanMessage로 변환
        user_message = HumanMessage(content=message)

        result = await request.app.state.supervisor_agent.ainvoke(
            {
                "messages": [user_message],
            },
            config={
                "configurable": {
                    "thread_id": str(body.thread_id),
                },
            },
        )
        answer = (
            result["messages"][-1].text
            if result["messages"]
            else "죄송합니다. 답변을 생성하지 못했습니다."
        )

        return ChatResponse(thread_id=body.thread_id, response=answer)
    except Exception:
        logger.exception("에이전트 답변 생성 실패")
        raise HTTPException(
            status_code=502, detail="답변 생성에 실패했습니다. 다시 시도해주세요."
        ) from None


def encode_event(event: str, data: dict[str, str]) -> str:
    """이벤트 이름과 JSON 데이터를 SSE 형식으로 변환합니다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post(
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
        has_text = False
        try:
            async for chunk, metadata in request.app.state.supervisor_agent.astream(
                {"messages": [HumanMessage(content=message)]},
                config={"configurable": {"thread_id": str(body.thread_id)}},
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
            yield encode_event("done", {"thread_id": str(body.thread_id)})
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
