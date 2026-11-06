from langchain.agents import create_agent
from langchain_core.documents import Document
from langchain_core.tools import StructuredTool
from langchain_core.messages import ToolMessage, HumanMessage
from app.config.model import openai_model
from app.prompts.prompt_loader import PromptLoader
from app.tools import RulesTool, TravelTool, WelfareTool


class HumanResourceAgent:
    def __init__(self) -> None:
        """도구 이름을 설정하고 인사 규정 검색 도구를 사용하는 에이전트를 생성합니다.

        설정된 대화 모델에 취업규칙·출장여비·복리후생 검색 도구와
        인사 전용 시스템 프롬프트를 연결합니다.
        """

        self.tool_name = "gd_hr_agent_tool"  # 에이전트 도구 고유 이름
        self.agent = create_agent(
            model=openai_model.get_model(),
            tools=[
                RulesTool().as_tool(),
                TravelTool().as_tool(),
                WelfareTool().as_tool(),
            ],
            system_prompt=PromptLoader.load_text("agent/hr/system.yaml"),
        )

    def as_tool(self) -> StructuredTool:
        """인사 에이전트를 질문을 입력받는 도구로 반환합니다.

        Returns:
            답변과 검색된 원본 문서 목록을 반환하는 인사 도구.
        """

        def ask(query: str) -> tuple[str, list[Document]]:
            """인사 질문을 처리하고 답변과 검색 문서를 반환합니다."""
            result = self.agent.invoke({"messages": [HumanMessage(query)]})
            documents = [
                document
                for message in result["messages"]
                if isinstance(message, ToolMessage)
                and isinstance(message.artifact, list)
                for document in message.artifact
                if isinstance(document, Document)
            ]

            return result["messages"][-1].text, documents

        return StructuredTool.from_function(
            func=ask,
            name=self.tool_name,
            description=PromptLoader.load_text("agent/hr/description.yaml"),
            response_format="content_and_artifact",
        )
