from copy import deepcopy
from typing import Any, Literal
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStoreRetriever
from app.rag.vector_store.vector_store_base import VectorStoreBase


class DocumentReader(VectorStoreBase):
    """부모 클래스의 벡터 저장소를 사용해 문서 검색 Retriever를 제공합니다.

    연결과 설정은 PgVectorBase에서 상속받습니다. as_retriever()는
    similarity 또는 mmr 검색을 설정한 Retriever를 반환하며,
    기본 설정은 similarity 검색과 최대 4개 문서 반환입니다.
    실제 검색은 반환된 Retriever의 invoke(query)를 호출할 때 수행합니다.

    사용 예시:
        document_store = DocumentReader.open(table_name="gd_hr_rules_of_employment")
        retriever = document_store.as_retriever()
        documents = retriever.invoke("연차휴가 신청 기준을 알려줘")

        for document in documents:
            print(document.page_content)
            print(document.metadata)

        # MMR 검색을 사용할 경우
        mmr_retriever = document_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4, "fetch_k": 20},
        )

    실행에는 PG_* DB 설정과 기본 OpenAI 임베딩의 인증 정보가 필요합니다.
    검색에 사용하는 임베딩 모델·설정은 문서 적재 시와 같아야 합니다.
    현재 open()의 새 테이블 생성 분기에는 vector_size 초기화 누락이 있으므로,
    위 예시는 문서가 적재된 기존 테이블을 대상으로 사용합니다.
    """

    def as_retriever(
        self,
        search_type: Literal["similarity", "mmr"] = "similarity",
        search_kwargs: dict[str, Any] | None = None,
    ) -> VectorStoreRetriever:
        """전달한 검색 설정을 사용하는 Retriever를 반환합니다.

        Args:
            search_type (Literal["similarity", "mmr"]): 검색 유형입니다.
                "similarity"와 "mmr"만 허용하며 기본값은 "similarity"입니다.
            search_kwargs (dict[str, Any] | None): 검색 옵션입니다.
                None이면 {"k": 4}를 사용하고, 지정하면 해당 옵션을 사용합니다.

        Returns:
            VectorStoreRetriever: 검색 설정을 보관하는 Retriever입니다.
                전달받은 옵션은 복사하여 호출자의 딕셔너리와 분리합니다.

        Raises:
            ValueError: search_type이 "similarity" 또는 "mmr"가 아닌 경우입니다.
        """
        if search_type not in ("similarity", "mmr"):
            raise ValueError("search_type은 'similarity' 또는 'mmr'여야 합니다.")

        return self.store.as_retriever(
            search_type=search_type,
            search_kwargs=(
                {"k": 4} if search_kwargs is None else deepcopy(search_kwargs)
            ),
        )

    def get_document_prompt(self) -> PromptTemplate:
        """검색 문서의 출처·페이지·본문을 표시할 PromptTemplate을 반환합니다.

        검색된 각 문서를 어떤 형식으로 보여줄지 지정합니다.
        검색 문서에는 source와 메타데이터가 필요하며,
        page는 0부터 시작하는 PDF 페이지 인덱스입니다.

        Returns:
            PromptTemplate: {source}, {page}, {page_content} 변수를 포함한 문서 템플릿입니다.
        """

        return PromptTemplate.from_template("""
            <document>
                출처: {source}
                페이지: {page}
                내용: {page_content}
            </document>
        """)
