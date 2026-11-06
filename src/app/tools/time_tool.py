from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from app.prompts import PromptLoader


class TimeInput(BaseModel):
    country: str = Field(
        default="한국",
        description=(
            "변환할 국가 시간입니다. 한글 및 영문 국가명 또는 IANA 시간대 입니다."
            "예: [한국, 일본, 중국, 싱가포르, 'kr', 'jp', 'cn', 'sg', Asia/Seoul, America/New_York]"
            "기본값은 한국 입니다."
        ),
    )


class TimeTool:
    """국가별 시간대 설정과 현재 시간 조회 도구를 제공합니다."""

    def __init__(self):
        # Agent Tool Name
        self.tool_name = "get_current_time"

        # 에이전트에게 도구의 용도, 호출 조건 설명
        self.tool_description = PromptLoader.load_text(
            filename="tools/time/description.yaml"
        )

        self.timezones = {
            "한국": "Asia/Seoul",
            "대한민국": "Asia/Seoul",
            "kr": "Asia/Seoul",
            "south korea": "Asia/Seoul",
            "일본": "Asia/Tokyo",
            "jp": "Asia/Tokyo",
            "japan": "Asia/Tokyo",
            "중국": "Asia/Shanghai",
            "cn": "Asia/Shanghai",
            "china": "Asia/Shanghai",
            "인도": "Asia/Kolkata",
            "in": "Asia/Kolkata",
            "india": "Asia/Kolkata",
            "영국": "Europe/London",
            "gb": "Europe/London",
            "uk": "Europe/London",
            "united kingdom": "Europe/London",
            "독일": "Europe/Berlin",
            "de": "Europe/Berlin",
            "germany": "Europe/Berlin",
            "싱가포르": "Asia/Singapore",
            "sg": "Asia/Singapore",
            "singapore": "Asia/Singapore",
        }

    def get_current_time(self, country: str = "한국") -> str:
        """국가명·코드 또는 IANA 시간대의 현재 시간을 반환합니다.

        Args:
            country (str): 조회할 국가 또는 시간대입니다. 기본값은 한국입니다.
                시간대가 여러 개인 국가는 America/New_York처럼 지정하세요.

        Returns:
            str: 날짜, 시간, 시간대 및 UTC 오프셋 또는 입력 확인 안내입니다.
        """
        country = country.strip()
        timezone_name = self.timezones.get(country.casefold(), country)
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError, ValueError:
            return (
                f"국가 또는 시간대를 확인해주세요: {country!r}. "
                "시간대가 여러 개인 국가는 America/New_York 같은 "
                "IANA 시간대로 지역을 지정해주세요."
            )

        return datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")

    def as_tool(self) -> StructuredTool:
        """country만 입력받는 에이전트용 시간 조회 도구를 생성합니다."""
        return StructuredTool.from_function(
            func=self.get_current_time,
            name=self.tool_name,
            description=self.tool_description,
            args_schema=TimeInput,
        )
