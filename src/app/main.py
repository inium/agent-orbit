from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.supervisor_agent import SupervisorAgent
from app.api.chat import router as chat_router
from app.api.chat_stream import router as chat_stream_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """서버 시작 시 대화에 사용할 에이전트를 생성합니다."""
    app.state.supervisor_agent = SupervisorAgent().get_agent()
    yield


app = FastAPI(title="Orbit API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(chat_stream_router)
