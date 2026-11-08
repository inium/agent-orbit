from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    """관리자 조회 API 인증 설정입니다. 키가 없으면 조회를 허용하지 않습니다."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_prefix="ADMIN_",
        extra="ignore",
    )
    api_key: SecretStr | None = None


admin_settings = AdminSettings()
