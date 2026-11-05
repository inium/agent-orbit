from langchain_core.tools import StructuredTool, create_retriever_tool
from app.rag.vector_store.document_reader import DocumentReader
from app.prompts.prompt_loader import PromptLoader


class WelfareTool:
    def __init__(self):
        """검색도구 설정에 필요한 변수값을 설정합니다."""

        tool_desc = PromptLoader.load_text("tools/hr/travel_description.yaml")

        self.tool_name = "gd_hr_welfare_of_employment_tool"  # Agent Tool Name
        self.tool_description = tool_desc  # 에이전트에게 도구의 용도, 호출 조건 설명
        self.vector_collection = "gd_hr_welfare_of_employment"  # RAG collection
        self.vector_search_type = "similarity"  # 검색 유형. similarity, mmr 중 1
        self.vector_search_kwargs = {"k": 4}  # 검색 파라미터

        self.document_reader = DocumentReader.open(table_name=self.vector_collection)

    def as_tool(self) -> StructuredTool:
        """길동상사 복리후생 규정을 검색하는 에이전트용 Retriever 도구를 생성합니다.

        Returns:
            StructuredTool: 검색어를 입력받아 복리후생 규정 문서를 반환하는 도구입니다.
                최종 답변 생성은 이 도구를 호출한 에이전트가 수행합니다.
        """
        return create_retriever_tool(
            retriever=self.document_reader.as_retriever(
                search_type=self.vector_search_type,
                search_kwargs=self.vector_search_kwargs,
            ),
            name=self.tool_name,
            description=self.tool_description,
            document_prompt=self.document_reader.get_document_prompt(),
            response_format="content_and_artifact",
        )
