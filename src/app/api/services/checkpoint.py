from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple


async def get_conversation_checkpoint(
    checkpointer: BaseCheckpointSaver, thread_id: str, checkpoint_ns: str = ""
) -> CheckpointTuple | None:
    """대화의 최신 체크포인트를 읽습니다. 모델 호출이나 DB 변경은 하지 않습니다."""
    return await checkpointer.aget_tuple(
        {"configurable": {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns}}
    )
