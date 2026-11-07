from langchain.agents import create_agent
from langchain_core.tools import StructuredTool
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
from app.config.model import openai_model
from app.prompts.prompt_loader import PromptLoader
from app.tools import TimeTool, IntroductionTool
from app.agents.human_resource_agent import HumanResourceAgent
from app.agents.mall_agent import MallAgent


class SupervisorAgent:
    def get_agent(self, checkpointer: BaseCheckpointSaver) -> CompiledStateGraph:
        """등록된 도구와 시스템 프롬프트로 상위 에이전트를 생성합니다.

        Args:
            checkpointer: thread_id별 대화와 실행 상태를 저장·복원하는 체크포인터입니다.
                호출자가 초기화와 연결 수명을 관리하며, 에이전트 실행 중에는
                사용 가능한 상태로 유지해야 합니다.

        Returns:
            인사·쇼핑몰 에이전트 도구, 시간 조회 및 소개 도구를 사용하고
            전달받은 체크포인터가 연결된 컴파일된 에이전트 그래프.
        """
        model = openai_model.get_model()
        model.tags = [*(model.tags or []), "supervisor_output"]

        return create_agent(
            model=model,
            tools=self.__get_tools(),
            system_prompt=PromptLoader.load_text("system.yaml"),
            checkpointer = checkpointer
        )

    def __get_tools(self) -> list[StructuredTool]:
        """상위 에이전트에서 사용할 도구 목록을 생성합니다.

        Returns:
            인사·쇼핑몰 에이전트 도구와 시간 조회 도구에 소개 도구를 추가한 목록.
            소개 도구는 같은 목록을 참조하여 등록된 기능을 안내합니다.
        """
        tools = [
            HumanResourceAgent().as_tool(),
            MallAgent().as_tool(),
            TimeTool().as_tool(),
        ]

        tools.append(IntroductionTool(tools).as_tool())
        return tools
