"""PostgreSQL 체크포인터에 저장된 대화의 최신 상태를 조회합니다.

실행 예시 (프로젝트 루트):
    PYTHONPATH=src python -m app.dump <thread_id>
"""

import argparse
import asyncio
import json
import sys

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.api.services.checkpoint import get_conversation_checkpoint


def format_message(message: BaseMessage | dict) -> str:
    """복원한 메시지를 역할과 본문으로 표시하며 도구 호출 정보도 포함합니다."""
    if isinstance(message, BaseMessage):
        role = message.type
        name = message.name
        content = message.content
        tool_calls = getattr(message, "tool_calls", None)
    else:
        role = message.get("type", message.get("role", "unknown"))
        name = message.get("name")
        content = message.get("content", "")
        tool_calls = message.get("tool_calls")

    label = f"{role} ({name})" if name else role
    text = (
        content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    )
    result = f"[{label}]\n{text}"
    if tool_calls:
        result += "\n도구 호출: " + json.dumps(tool_calls, ensure_ascii=False)
    return result


async def dump_conversation(thread_id: str, checkpoint_ns: str = "") -> bool:
    """최신 체크포인트의 메시지를 출력합니다. DB·모델 상태를 변경하지 않습니다."""
    from app.config.memory_store import memory_store

    async with AsyncPostgresSaver.from_conn_string(
        memory_store.connection_url()
    ) as checkpointer:
        saved = await get_conversation_checkpoint(
            checkpointer, thread_id, checkpoint_ns
        )

    if saved is None:
        print("해당 thread_id와 namespace에 저장된 대화가 없습니다.", file=sys.stderr)
        return False

    messages = saved.checkpoint.get("channel_values", {}).get("messages", [])
    print(f"대화 ID: {thread_id}")
    print(f"메시지 수: {len(messages)}")
    for message in messages:
        print("\n" + format_message(message))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="PostgreSQL에 저장된 최신 대화 조회")
    parser.add_argument("thread_id", help="채팅 API 요청에 사용한 대화 ID")
    parser.add_argument(
        "--namespace", default="", help="체크포인트 namespace (기본: 루트)"
    )
    args = parser.parse_args()
    try:
        return (
            0 if asyncio.run(dump_conversation(args.thread_id, args.namespace)) else 1
        )
    except Exception as error:
        # DB 오류 원문에는 연결 정보가 포함될 수 있으므로 출력하지 않습니다.
        print(
            f"대화 조회에 실패했습니다 ({type(error).__name__}). "
            "MEMORY_DB 설정과 DB 연결 상태를 확인하세요.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
