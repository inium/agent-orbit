from langchain_core.tools import StructuredTool
from app.tools.time_tool import TimeTool
from app.tools.introduction_tool import IntroductionTool
from app.tools.mall.cs_tool import CsTool
from app.tools.hr.rules_tool import RulesTool
from app.tools.hr.travel_tool import TravelTool
from app.tools.hr.welfare_tool import WelfareTool

__all__ = ["TimeTool", "CsTool", "RulesTool", "TravelTool", "WelfareTool"]


def all_tools() -> list[StructuredTool]:
    tools = [
        TimeTool().as_tool(),  # 시간 조회 도구
        CsTool().as_tool(),  # 쇼핑몰 CS 검색 도구
        RulesTool().as_tool(),  # 취업규칙 검색 도구
        TravelTool().as_tool(),  # 출장여비 검색 도구
        WelfareTool().as_tool(),  # 복리후생 검색 도구
    ]
    tools.append(IntroductionTool(tools).as_tool())

    return tools
