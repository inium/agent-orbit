from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pymupdf4llm import PyMuPDF4LLMLoader


class PdfTextSplitter:
    """PDF를 로드하고 토큰 수 기준의 겹치는 청크로 분할합니다.

    split() 정적 메서드로 PDF 경로와 청크 크기, 겹침, 로딩 모드를 지정합니다.
    기본값은 페이지별 로딩과 1000토큰 청크, 200토큰 겹침입니다.
    각 청크는 로더의 메타데이터를 유지하며, source가 누락되거나 비어 있으면
    PDF 파일명으로 보완합니다. 임베딩 생성이나 DB 저장은 수행하지 않습니다.
    """

    @staticmethod
    def split(
        path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name="cl100k_base",
        mode="page",
    ) -> list[Document]:
        """PDF 파일을 로드한 후 문서를 청크(chunk)로 나눕니다.

        Args:
            path (str): 로드할 PDF 파일의 경로입니다.
            chunk_size (int): 청크의 최대 토큰 수입니다. 기본값은 1000입니다.
            chunk_overlap (int): 인접한 청크 사이에 겹치도록 유지할 토큰 수입니다.
                문맥을 이어 주기 위한 설정으로, 기본값은 200입니다.
                0 이상이며 chunk_size 이하여야 합니다.
            encoding_name (str): 청크 분할 시 토큰 수를 계산할 tiktoken 인코딩
                이름입니다. 기본값은 "cl100k_base"입니다. 사용하는 모델에 맞는
                인코딩을 지정하며, PDF 파일의 문자 인코딩과는 별개입니다.
            mode (str): PDF 로딩 단위입니다. 기본값은 "page"입니다.
                "page"는 페이지마다 Document를 생성하고, "single"은 전체 페이지를
                하나의 Document로 합칩니다. 이후 두 방식 모두 청크로 분할합니다.
                페이지별 출처를 유지하려면 "page"를 사용하세요.

        Returns:
            list[Document]: 청크로 분할한 문서 목록입니다. 각 문서는 청크 텍스트를
                담은 page_content와 원본 문서에서 전달된 metadata를 포함합니다.
        """

        loader = PyMuPDF4LLMLoader(path, mode=mode)

        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            encoding_name=encoding_name,
        )

        documents = text_splitter.split_documents(data)

        for document in documents:
            source = document.metadata.get("source")
            if source is None or not str(source).strip():
                document.metadata["source"] = Path(path).name

        return documents
