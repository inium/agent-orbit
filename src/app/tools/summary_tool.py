"""사용자가 제공한 원문을 요약하고 원문과 대조하는 그래프 도구."""

import json
from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, field_validator

from app.prompts.prompt_loader import PromptLoader


class SummaryInput(BaseModel):
    text: str = Field(
        min_length=1, max_length=12000, description="요약할 원문 전체. 최대 12,000자"
    )
    style: Literal["paragraph", "bullets"] = "bullets"
    focus: str = Field(default="", max_length=500, description="중점적으로 요약할 사항")

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("요약할 원문을 입력해 주세요.")
        return value


class SummaryCheck(BaseModel):
    passed: bool = Field(description="원문에 충실하고 요청한 핵심을 포함하면 true")
    feedback: list[str] = Field(description="원문과 비교해 수정할 구체적인 사항")


class SummaryState(TypedDict):
    text: str  # 요약할 원문 전체
    style: str  # 출력 형식: paragraph(문단) 또는 bullets(글머리표)
    focus: str  # 중점적으로 요약할 주제나 요청 사항
    summary: str  # 현재 요약문. 최초 생성 전에는 빈 문자열
    feedback: list[str]  # 원문 대조에서 확인된 수정 의견
    passed: bool  # 현재 요약문이 모델의 원문 대조를 통과했는지 여부
    revisions: int  # 최초 생성을 제외한 수정 횟수. 최대 2회


class SummarizeTextTool:
    """Supervisor의 ReAct 루프에서 사용하는 제한된 요약·검증 워크플로."""

    def __init__(self, model=None):
        """요약 모델과 구조화된 검증 모델을 설정하고 그래프를 컴파일합니다.

        Args:
            model: 요약 및 원문 대조에 사용할 모델. 생략하면 프로젝트의
                요약 모델을 출력 한도 2,000토큰으로 생성합니다.

        생성 시 프롬프트를 읽고 그래프를 구성하며 모델 호출은 수행하지 않습니다.
        """
        if model is None:
            from app.config.model import openai_model

            model = openai_model.get_summary_model(max_tokens=2000)

        self.model = model
        self.checker = model.with_structured_output(SummaryCheck)
        self.write_prompt = PromptLoader.load_text("tools/summary/write.yaml")
        self.check_prompt = PromptLoader.load_text("tools/summary/check.yaml")

        builder = StateGraph(SummaryState)
        builder.add_node("summarize", self._summarize)
        builder.add_node("check", self._check)
        builder.add_edge(START, "summarize")
        builder.add_edge("summarize", "check")
        builder.add_conditional_edges("check", self._route)
        self.graph = builder.compile()

    def _summarize(self, state: SummaryState, config: RunnableConfig):
        """원문과 요청 조건으로 요약을 생성하거나 기존 요약을 수정합니다.

        Args:
            state: 원문, 형식, 강조 주제, 기존 요약과 검증 피드백을 담은 상태.
            config: 모델 호출에 전달할 콜백 등 LangGraph 실행 설정.

        Returns:
            새 요약과 수정 횟수를 담은 상태 업데이트. 최초 생성은 수정 횟수에
            포함하지 않으며 기존 요약이 있을 때만 횟수를 증가시킵니다.

        Raises:
            ValueError: 모델이 빈 요약을 반환한 경우.
        """
        payload = {
            key: state[key] for key in ("text", "style", "focus", "summary", "feedback")
        }
        message = self.model.invoke(
            [
                SystemMessage(self.write_prompt),
                HumanMessage(json.dumps(payload, ensure_ascii=False)),
            ],
            config=config,
        )
        if not message.text.strip():
            raise ValueError("요약 결과가 비어 있습니다.")
        return {
            "summary": message.text,
            "revisions": state["revisions"] + bool(state["summary"]),
        }

    def _check(self, state: SummaryState, config: RunnableConfig):
        """모델로 원문과 요약을 대조하고 구조화된 검증 결과를 반환합니다.

        Args:
            state: 원문, 요약, 출력 형식과 강조 주제를 담은 상태.
            config: 검증 모델 호출에 전달할 LangGraph 실행 설정.

        Returns:
            통과 여부 passed와 수정 의견 feedback을 담은 상태 업데이트.
            모델의 통과 판정이 요약의 정확성을 보장하지는 않습니다.
        """
        payload = {key: state[key] for key in ("text", "style", "focus", "summary")}
        result = self.checker.invoke(
            [
                SystemMessage(self.check_prompt),
                HumanMessage(json.dumps(payload, ensure_ascii=False)),
            ],
            config=config,
        )
        return {"passed": result.passed, "feedback": result.feedback}

    @staticmethod
    def _route(state: SummaryState) -> Literal["summarize", "__end__"]:
        """검증 상태를 확인하여 종료하거나 요약 수정 노드로 분기합니다.

        Args:
            state: 검증 통과 여부와 현재 수정 횟수를 담은 상태.

        Returns:
            검증을 통과했거나 수정이 2회에 도달하면 END, 그 외에는
            수정을 수행할 summarize 노드 이름.
        """
        return END if state["passed"] or state["revisions"] >= 2 else "summarize"

    @staticmethod
    def _initial(text: str, style: str, focus: str) -> SummaryState:
        """입력을 검증하고 이번 호출에 사용할 독립적인 초기 상태를 만듭니다.

        Args:
            text: 공백만으로 구성되지 않은 최대 12,000자의 원문.
            style: paragraph(문단) 또는 bullets(글머리표) 출력 형식.
            focus: 중점적으로 요약할 사항. 최대 500자.

        Returns:
            검증된 입력과 빈 요약·피드백, 미통과 상태, 수정 횟수 0을 담은 상태.

        Raises:
            pydantic.ValidationError: 입력 길이나 출력 형식이 유효하지 않은 경우.
        """
        validated = SummaryInput(text=text, style=style, focus=focus)
        return {
            **validated.model_dump(),
            "summary": "",
            "feedback": [],
            "passed": False,
            "revisions": 0,
        }

    @staticmethod
    def _result(state: SummaryState) -> str:
        """최종 그래프 상태를 도구 응답용 JSON 문자열로 직렬화합니다.

        Args:
            state: 요약, 검증 통과 여부, 수정 횟수와 피드백을 담은 최종 상태.

        Returns:
            요약문, 검증 상태, 수정 횟수, 남은 문제와 한계 안내를 포함한 JSON.
            검증을 통과한 경우 남은 문제 목록은 비워서 반환합니다.
        """
        return json.dumps(
            {
                "summary": state["summary"],
                "verification_passed": state["passed"],
                "revisions": state["revisions"],
                "remaining_issues": state["feedback"] if not state["passed"] else [],
                "notice": (
                    "모델의 대조 결과이며 정확성을 보장하지 않습니다."
                    if state["passed"]
                    else "수정 한도에 도달하여 원문 대조를 통과하지 못했습니다."
                ),
            },
            ensure_ascii=False,
        )

    def as_tool(self) -> StructuredTool:
        """요약 그래프를 Supervisor가 호출할 수 있는 도구로 감쌉니다.

        Returns:
            SummaryInput 스키마와 동기·비동기 실행 함수를 연결한
            summarize_text 도구. 각 호출에서 초기 상태를 새로 생성합니다.
        """

        def summarize(
            text: str, config: RunnableConfig, style: str = "bullets", focus: str = ""
        ) -> str:
            """원문과 요약 조건을 검증하고 그래프를 동기로 실행해 JSON을 반환합니다."""
            return self._result(
                self.graph.invoke(self._initial(text, style, focus), config=config)
            )

        async def asummarize(
            text: str, config: RunnableConfig, style: str = "bullets", focus: str = ""
        ) -> str:
            """원문과 요약 조건을 검증하고 그래프를 비동기로 실행해 JSON을 반환합니다."""
            return self._result(
                await self.graph.ainvoke(
                    self._initial(text, style, focus), config=config
                )
            )

        return StructuredTool.from_function(
            func=summarize,
            coroutine=asummarize,
            name="summarize_text",
            description=PromptLoader.load_text("tools/summary/description.yaml"),
            args_schema=SummaryInput,
        )
