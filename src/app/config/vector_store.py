from pathlib import Path

from sqlalchemy.engine import URL
from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorStore(BaseSettings):
    """환경 변수와 .env에서 PostgreSQL 벡터 저장소 연결 설정을 읽습니다.

    VECTOR_DB_HOST, VECTOR_DB_PORT, VECTOR_DB_DATABASE,
    VECTOR_DB_USERNAME, VECTOR_DB_PASSWORD를 사용하며,
    환경 변수는 .env 값보다 우선합니다. 포트 기본값은 5432이고 1 이상이어야
    합니다. 환경 변수 이름의 대소문자는 구분하지 않으며 추가 설정은 무시합니다.
    필수 설정이 없거나 값이 유효하지 않으면 인스턴스 생성 시 검증 오류가 발생합니다.

    사용자 이름과 비밀번호는 SecretStr로 출력 시 가려집니다.
    connection_url()은 실제 비밀번호를 포함한 연결 URL을 반환하므로
    로그나 화면에 출력하지 않아야 합니다.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_prefix="VECTOR_DB_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str
    port: int = Field(default=5432, ge=1)
    database: str
    username: SecretStr
    password: SecretStr

    def connection_url(self) -> str:
        """Vector Store Connection URL을 만듭니다.

        출력하지 마세요."""
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.username.get_secret_value(),
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.database,
        ).render_as_string(hide_password=False)


vector_store = VectorStore()
