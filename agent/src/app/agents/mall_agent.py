from langchain.agents import create_agent
from langchain_core.documents import Document
from langchain_core.tools import StructuredTool
from langchain_core.messages import ToolMessage, HumanMessage
from app.config.model import openai_model
from app.prompts.prompt_loader import PromptLoader
from app.tools import CsTool


class MallAgent:
    def __init__(self) -> None:
        """도구 이름을 설정하고 쇼핑몰 CS 매뉴얼을 검색하는 에이전트를 생성합니다.

        설정된 대화 모델에 CsTool 검색 도구와 쇼핑몰 CS 전용
        시스템 프롬프트를 연결합니다.
        """

        self.tool_name = "gd_mall_cs_agent_tool"  # 에이전트 도구 고유 이름
        self.agent = create_agent(
            model=openai_model.get_model(),
            tools=[CsTool().as_tool()],
            system_prompt=PromptLoader.load_text("agent/mall/system.yaml"),
        )

    def as_tool(self) -> StructuredTool:
        """쇼핑몰 CS 에이전트를 질문을 입력받는 도구로 반환합니다.

        Returns:
            답변을 content로, 검색된 원본 문서 목록을 artifact로 반환하는 도구.
        """

        def ask(query: str) -> tuple[str, list[Document]]:
            """쇼핑몰 CS 질문을 처리하고 답변과 검색된 원본 문서를 반환합니다.

            Args:
                query: 쇼핑몰 CS 문의 내용과 사용자가 제공한 조건입니다.

            Returns:
                마지막 답변의 텍스트와 도구 메시지에서 수집한 원본 문서 목록.
                검색 문서가 없으면 문서 목록은 비어 있습니다.
            """
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
            description=PromptLoader.load_text("agent/mall/description.yaml"),
            response_format="content_and_artifact",
        )
