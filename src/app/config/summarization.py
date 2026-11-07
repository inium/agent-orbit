from typing import Literal
from pydantic import Field
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import SummarizationMiddleware
from pydantic_settings import BaseSettings
from app.prompts.prompt_loader import PromptLoader
from app.config.model import openai_model


class Summarization(BaseSettings):
    """대화 요약 설정을 관리하고 SummarizationMiddleware를 생성합니다.

    max_summary_tokens는 요약 출력 한도, trigger_clause와 trigger_counter는
    요약 실행 기준, keep_summary_messages는 원문으로 유지할 최근 메시지 수입니다.
    요약 모델과 프롬프트를 조합하며, 과거 체크포인트 삭제는 처리하지 않습니다.
    """

    # 요약 모델이 한 번에 생성할 수 있는 최대 출력 토큰
    max_summary_tokens: int = Field(default=2000, ge=1000)

    # 요약 트리거 조건
    trigger_clause: Literal["tokens", "messages"] = "tokens"

    # 트리거 조건에 따른 토큰 수 또는 메시지 수
    trigger_counter: int = Field(default=8000, ge=100, le=40000)

    # 요약 후에도 유지할 메시지 수
    keep_summary_messages: int = Field(default=10, ge=1, le=100)

    def get_middleware(self) -> SummarizationMiddleware:
        """요약 모델과 프롬프트에 클래스 설정을 적용한 미들웨어를 반환합니다.

        출력 토큰 한도, 요약 실행 기준과 최근 메시지 보존 범위를 설정하며,
        반환된 객체는 create_agent()의 middleware 목록에 추가해 사용합니다.

        Returns:
            별도로 생성한 요약 모델과 프롬프트, 요약 실행 기준 및 최근 메시지
            보존 설정이 적용된 SummarizationMiddleware 객체.
        """

        max_tokens = self.max_summary_tokens
        summary_prompt = PromptLoader.load_text("middleware/summarization.yaml")
        trigger = (self.trigger_clause, self.trigger_counter)
        keep = ("messages", self.keep_summary_messages)

        return SummarizationMiddleware(
            model=openai_model.get_summary_model(max_tokens=max_tokens),  # 요약 모델
            summary_prompt=summary_prompt,  # 요약 모델이 사용할 프롬프트
            trigger=trigger,  # 요약 방법(tokens|messages)과 토큰 수
            keep=keep,  # 요약 후에도 유지할 메시지 수
        )


summarization = Summarization()
