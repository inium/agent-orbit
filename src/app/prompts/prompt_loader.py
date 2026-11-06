import json
from pathlib import Path

import yaml
from typing import Any
from langchain_core.prompts import BasePromptTemplate, PromptTemplate


class PromptLoader:
    """app/prompts/templates 내부의 프롬프트를 읽습니다."""

    def __init__(self, base_dir: Path | None = None) -> None:
        """프롬프트 파일 경로를 해석할 기준 디렉터리를 설정합니다.

        Args:
            base_dir (Path | None): 프롬프트 기준 디렉터리입니다. 생략하면
                이 모듈과 같은 위치의 templates 디렉터리를 사용합니다.
                상대 경로를 전달하면 현재 작업 디렉터리를 기준으로 해석합니다.

        기준 경로는 심볼릭 링크와 상위 경로를 해석한 절대 경로로 보관합니다.
        디렉터리를 생성하거나 존재 여부를 별도로 검증하지는 않습니다.
        """
        self.base_dir = (
            base_dir
            if base_dir is not None
            else Path(__file__).resolve().parent / "templates"
        ).resolve()

    def _resolve_path(self, filename: str) -> Path:
        """파일 경로를 정규화하고 기준 디렉터리 내부인지 확인합니다.

        Args:
            filename (str): 기준 디렉터리에 대한 상대 경로입니다.
                절대 경로도 기준 디렉터리 내부인 경우 허용합니다.

        Returns:
            Path: 심볼릭 링크와 상위 경로를 해석한 절대 경로입니다.
                파일의 존재 여부나 확장자는 별도로 검증하지 않습니다.

        Raises:
            ValueError: 해석한 경로가 기준 디렉터리 밖을 가리키는 경우입니다.
        """
        path = (self.base_dir / filename).resolve()

        if not path.is_relative_to(self.base_dir):
            raise ValueError("프롬프트 디렉터리 내부의 경로를 지정하세요.")

        return path

    @classmethod
    def load(cls, filename: str, base_dir: Path | None = None) -> BasePromptTemplate:
        """기준 디렉터리의 YAML·JSON 설정으로 PromptTemplate을 생성합니다.

        Args:
            filename (str): 기준 디렉터리 내부의 프롬프트 파일 경로입니다.
                기본 기준 경로는 app/prompts/templates입니다.
            base_dir (Path | None): 이번 호출에 사용할 기준 디렉터리입니다.
                생략하면 기본 templates 디렉터리를 사용합니다.

        Returns:
            BasePromptTemplate: LangChain이 파일 설정으로 생성한 프롬프트 객체입니다.
                문자열이 필요하면 반환 객체의 format()에 필요한 변수를 전달합니다.
                이 메서드는 변수를 적용하거나 LLM을 호출하지 않습니다.

        Raises:
            ValueError: 경로가 기준 디렉터리를 벗어나거나 확장자,
                _type, template 또는 template_format이 지원되지 않는 경우입니다.
            FileNotFoundError: 지정한 파일이 없는 경우입니다.

        매번 새 로더를 생성하므로 기존 인스턴스의 base_dir는 사용하지 않습니다.
        파일 읽기·파싱·설정 검증 중 발생한 오류는 그대로 전파합니다.
        """
        loader = cls(base_dir=base_dir)
        path = loader._resolve_path(filename)

        if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            raise ValueError("프롬프트 파일은 YAML 또는 JSON이어야 합니다.")

        content = path.read_text(encoding="utf-8")
        config = (
            json.loads(content)
            if path.suffix.lower() == ".json"
            else yaml.safe_load(content)
        )
        if not isinstance(config, dict) or config.get("_type", "prompt") != "prompt":
            raise ValueError("_type이 prompt인 설정 객체가 필요합니다.")
        config = dict(config)
        config.pop("_type", None)
        if not isinstance(config.get("template"), str):
            raise ValueError("문자열 template 필드가 필요합니다.")
        if config.get("template_format", "f-string") != "f-string":
            raise ValueError("template_format은 f-string만 지원합니다.")
        return PromptTemplate(**config)

    @classmethod
    def load_text(
        cls,
        filename: str,
        base_dir: Path | None = None,
        **variables: Any,
    ) -> str:
        """프롬프트를 읽고 변수를 적용한 문자열을 반환합니다.

        Args:
            filename (str): 기준 디렉터리 내부의 YAML·JSON 파일 경로입니다.
            base_dir (Path | None): 기준 디렉터리입니다. 생략하면 templates를 사용합니다.
            **variables (Any): 템플릿의 {변수명}에 넣을 값을 키워드 인자로 전달합니다.
                예를 들어 {capabilities}가 있으면 capabilities="지원 기능 목록"을
                전달합니다. 여러 변수는 name="길동이", company="길동상사"처럼
                지정하며, 딕셔너리는 **values로 펼쳐 전달할 수 있습니다.
                변수가 없는 템플릿은 생략할 수 있고, 필수 변수가 누락되면
                포맷 과정에서 오류가 발생합니다.

        Returns:
            str: 변수를 적용하고 앞뒤 공백과 줄바꿈을 제거한 문자열입니다.

        사용 예시:
            values = {
                "name": "길동이",
                "company": "길동상사",
                "capabilities": "취업규칙 검색, 현재 시간 조회",
            }
            text = PromptLoader.load_text("tools/example.yaml", **values)

            or

            text = PromptLoader.load_text(
                "tools/example.yaml",
                name="길동이",
                company="길동상사",
                capabilities="취업규칙 검색, 현재 시간 조회",
            )

        파일 로딩과 포맷 오류는 그대로 전파합니다. LLM을 호출하지 않습니다.
        """
        return cls.load(filename, base_dir=base_dir).format(**variables).strip()
