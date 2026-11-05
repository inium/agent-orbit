from collections.abc import Sequence
from langchain_core.tools import BaseTool, StructuredTool
from app.prompts.prompt_loader import PromptLoader


class IntroductionTool:
    """AI 에이전트 길동이의 역할, 지원 기능과 사용 방법을 안내합니다."""

    def __init__(self, tools: Sequence[BaseTool]) -> None:
        """에이전트에 등록할 도구 목록을 보관합니다.

        Args:
            tools: 지원 기능 안내에 사용할 도구 목록입니다.
                실행하지 않고 각 도구의 이름과 설명만 읽습니다. 전달된 목록을
                참조하므로 목록의 추가·삭제는 이후 소개 호출에도 반영됩니다.
        """
        self.tool_name = "introduction_tool"
        self.tool_description = PromptLoader.load_text(
            "tools/introduction/description.yaml"
        )
        self.tools = tools

    def introduce(self) -> str:
        """등록된 도구의 이름과 설명에서 지원 기능 안내를 생성합니다."""
        capabilities = "\n".join(
            f"- {tool.name}: {' '.join(tool.description.split())}"
            for tool in self.tools
            if tool.name != self.tool_name
        )

        return PromptLoader.load_text(
            "tools/introduction/introduce.yaml",
            capabilities=capabilities or "현재 등록된 기능 도구가 없습니다.",
        )

    def as_tool(self) -> StructuredTool:
        """입력 인자 없이 호출하는 길동이 소개 도구를 생성합니다."""
        return StructuredTool.from_function(
            func=self.introduce,
            name=self.tool_name,
            description=self.tool_description,
        )
