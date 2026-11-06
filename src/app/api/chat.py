import logging

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage

from app.api.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
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
