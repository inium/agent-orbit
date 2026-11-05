from pathlib import Path

from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings


class OpenAIModel(BaseSettings):
    """OpenAI 모델 설정을 읽고 임베딩 객체를 생성합니다.

    환경 변수와 .env의 OPENAI_API_KEY, OPENAI_MODEL, OPENAI_EMBEDDING_MODEL을
    사용하며, 환경 변수는 .env 값보다 우선합니다. 이름의 대소문자는 구분하지
    않으며 추가 설정은 무시합니다. 임베딩 모델 기본값은 text-embedding-3-small입니다.
    API 키와 대화 모델은 필수이며 API 키는 SecretStr로 출력 시 가려집니다.

    get_embeddings()는 설정된 모델과 API 키로 새 OpenAIEmbeddings 객체를
    반환합니다. 실제 임베딩 API 요청은 embed_query() 또는 embed_documents()
    호출 시 수행합니다. 문서 적재와 검색에는 같은 임베딩 모델·설정을 사용해야 합니다.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[4] / ".env",
        env_prefix="OPENAI_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_key: SecretStr
    model: str
    model_provider: str = Field(default="openai")
    embedding_model: str = Field(default="text-embedding-3-small")

    def get_embeddings(self) -> OpenAIEmbeddings:
        """설정된 모델과 API 키로 임베딩 객체를 생성합니다."""
        return OpenAIEmbeddings(
            model=self.embedding_model,
            api_key=self.api_key.get_secret_value(),
        )

    def get_model(self, temperature: int = 0):
        """설정된 모델, 제공자와 API 키로 대화 모델 객체를 생성합니다.

        Args:
            temperature: 응답의 무작위성을 조절하는 값. 기본값은 0입니다.

        Returns:
            지정한 temperature가 적용된 대화 모델 객체.
        """
        return init_chat_model(
            model=self.model,
            model_provider=self.model_provider,
            api_key=self.api_key.get_secret_value(),
            temperature=temperature,
        )


openai_model = OpenAIModel()
