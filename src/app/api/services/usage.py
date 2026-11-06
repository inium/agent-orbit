from langchain_core.callbacks import UsageMetadataCallbackHandler

from app.api.schemas.chat import TokenUsage


def collect_usage(callback: UsageMetadataCallbackHandler) -> TokenUsage | None:
    """모델별로 보고된 사용량을 합산하며 수집되지 않은 경우 None을 반환합니다."""
    if not callback.usage_metadata:
        return None
    return TokenUsage(
        input_tokens=sum(
            usage["input_tokens"] for usage in callback.usage_metadata.values()
        ),
        output_tokens=sum(
            usage["output_tokens"] for usage in callback.usage_metadata.values()
        ),
        total_tokens=sum(
            usage["total_tokens"] for usage in callback.usage_metadata.values()
        ),
    )
