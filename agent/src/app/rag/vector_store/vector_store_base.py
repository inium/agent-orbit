import os
from typing import Self
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGEngine, PGVectorStore
from langchain_openai import OpenAIEmbeddings
from app.config.vector_store import VectorStore


class VectorStoreBase:
    """문서 적재·검색 클래스에서 공유할 벡터 저장소 설정과 유틸리티를 제공합니다.

    생성자는 전달받은 테이블 이름, 임베딩 객체, DB 엔진과 저장소를 보관하며
    연결이나 테이블 생성을 직접 수행하지 않습니다. 공통 유틸리티로 PG_*
    환경 변수 기반 연결 URL 생성과 확인용 임베딩을 통한 벡터 차원 계산을 제공합니다.
    """

    def __init__(
        self,
        table_name: str,
        embeddings: Embeddings,
        vector_size: int,
        engine: PGEngine,
        store: PGVectorStore,
    ) -> None:
        """초기화된 연결과 설정을 보관합니다.

        Args:
            table_name (str): 연결된 PostgreSQL 벡터 테이블 이름입니다.
            embeddings (Embeddings): 적재와 검색에 사용할 임베딩 객체입니다.
            vector_size (int): 임베딩 테이블의 벡터 사이즈 입니다.
            engine (PGEngine): 저장소의 DB 연결을 관리하는 초기화된 엔진입니다.
            store (PGVectorStore): 지정한 테이블과 임베딩 설정으로 생성된 저장소입니다.
        """
        self.table_name = table_name
        self.embeddings = embeddings
        self.vector_size = vector_size
        self.engine = engine
        self.store = store

    @classmethod
    def open(
        cls,
        table_name: str,
        embeddings: Embeddings | None = None,
    ):
        """기존 벡터 테이블에 연결하고, 없으면 테이블을 생성 후 Vector Store
        저장소(PGVectorStore)를 생성합니다.

        Args:
            table_name (str): public 스키마에서 사용할 벡터 테이블 이름입니다.
            embeddings (Embeddings | None): 적재·검색에 사용할 임베딩 객체입니다.
                생략하면 OpenAIEmbeddings()를 사용합니다.
            conn (str | None): DB 연결 URL입니다. 생략하면 PG_* 환경 변수를 읽습니다.

        Returns:
            Self: 연결된 엔진과 저장소를 보관하는 호출 클래스의 인스턴스입니다.

        기존 테이블은 재사용하며 모델·차원 일치를 자동 검증하지 않습니다.
        새 테이블 생성 분기는 vector_size를 사용하지만 현재 매개변수나
        지역 변수로 초기화하지 않아 UnboundLocalError가 발생합니다.
        DB 및 임베딩 호출 중 발생한 오류는 그대로 전파합니다.
        """
        load_dotenv()

        embedding_service = embeddings if embeddings is not None else OpenAIEmbeddings()
        connection_url = cls.connection_url()

        lookup_engine = create_engine(connection_url, hide_parameters=True)
        try:
            table_exists = inspect(lookup_engine).has_table(table_name, schema="public")
        finally:
            lookup_engine.dispose()

        engine = PGEngine.from_connection_string(
            url=connection_url,
            hide_parameters=True,
        )

        vector_size = cls.get_embedding_dimensions(embedding_service)
        if vector_size <= 0:
            raise ValueError("임베딩 벡터의 차원은 양수여야 합니다.")

        if not table_exists:
            engine.init_vectorstore_table(
                table_name=table_name,
                vector_size=vector_size,
                overwrite_existing=False,
            )

        store = PGVectorStore.create_sync(
            engine=engine,
            table_name=table_name,
            embedding_service=embedding_service,
        )

        return cls(
            table_name=table_name,
            embeddings=embedding_service,
            vector_size=vector_size,
            engine=engine,
            store=store,
        )

    @staticmethod
    def get_embedding_dimensions(embeddings: Embeddings) -> int:
        """확인용 텍스트를 임베딩해 벡터 차원을 반환합니다.

        Args:
            embeddings (Embeddings): 차원을 확인할 임베딩 객체입니다.

        Returns:
            int: 반환된 임베딩 벡터의 원소 수입니다.

        embed_query()를 실제 호출하므로 API 기반 모델에서는 네트워크 요청과
        비용이 발생할 수 있습니다. 호출 오류는 그대로 전파합니다.
        """
        return len(embeddings.embed_query("dimension check"))

    @staticmethod
    def connection_url() -> str:
        """PG_* 환경 변수로 비밀번호를 포함한 DB URL을 만듭니다. 출력하지 마세요."""
        return VectorStore().connection_url()
