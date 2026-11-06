from pathlib import Path
from app.rag.loaders.pdf_text_splitter import PdfTextSplitter
from app.rag.vector_store.document_importer import DocumentImporter


def main():
    # 실행 위치와 관계없이 프로젝트 루트의 data 폴더를 참조합니다.
    data_dir = Path(__file__).resolve().parents[2] / "data"
    files = [
        {
            "path": data_dir / "취업규칙 - (주)길동상사.pdf",
            "table_name": "gd_hr_rules_of_employment",
        },
        {
            "path": data_dir / "복리후생 규정 - (주)길동상사.pdf",
            "table_name": "gd_hr_welfare_of_employment",
        },
        {
            "path": data_dir / "출장여비 규정 - (주)길동상사.pdf",
            "table_name": "gd_hr_travel_of_employment",
        },
        {
            "path": data_dir / "쇼핑몰 CS 실무 매뉴얼 - (주)길동상사.pdf",
            "table_name": "gd_mall_cs",
        },
    ]

    for index, file in enumerate(files, start=1):
        documents = PdfTextSplitter.split(str(file["path"]))

        DocumentImporter.open(table_name=file["table_name"]).add_documents(documents)

        print(f"{index} of {len(files)} 완료")

    print("\n모든 문서가 import 완료되었습니다.")


if __name__ == "__main__":
    main()
