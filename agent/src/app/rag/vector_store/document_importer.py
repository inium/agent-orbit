from langchain_core.documents import Document
from app.rag.vector_store.vector_store_base import VectorStoreBase


class DocumentImporter(VectorStoreBase):
    """부모 클래스의 벡터 저장소를 사용해 문서 본문과 메타데이터를 추가 저장합니다.

    연결과 설정은 PgVectorBase에서 상속받으며, add_documents()에서
    저장소에 설정된 임베딩 객체로 문서를 임베딩해 저장하고 문서 ID를 반환합니다.
    기존 문서 삭제나 중복 제거는 수행하지 않습니다.

    사용 예시:
        from langchain_core.documents import Document

        documents = [
            Document(
                page_content="저장할 문서 본문",
                metadata={"source": "example.pdf", "page": 0},
            ),
        ]
        ingester = DocumentImporter.open(table_name="gd_hr_rules_of_employment")
        document_ids = ingester.add_documents(documents)

    실행에는 PG_* DB 설정과 기본 OpenAI 임베딩의 인증 정보가 필요합니다.
    add_documents()에는 문서 목록을 전달하며, 반환값은 저장된 문서 ID 목록입니다.
    현재 부모의 open()은 새 테이블 생성 시 vector_size 초기화 누락으로
    오류가 발생하므로, 위 예시는 이미 생성된 테이블을 대상으로 사용해야 합니다.
    """

    def add_documents(self, documents: list[Document]) -> list[str]:
        """문서를 추가 저장하고 ID를 반환합니다. 빈 입력은 빈 목록을 반환합니다.

        Args:
            documents (list[Document]): 임베딩하여 저장할 문서 목록입니다.
                각 문서의 page_content와 metadata를 함께 저장합니다.

        기존 데이터 삭제·중복 제거는 수행하지 않으며 저장 오류는 전파합니다.
        """
        if not documents:
            return []

        return self.store.add_documents(documents)
