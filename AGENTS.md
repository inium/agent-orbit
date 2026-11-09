# Agent Orbit 작업 안내

## 프로젝트 구성

가상의 회사 (주)길동상사의 사내 규정·쇼핑몰 CS 안내 에이전트다. Python 3.14 이상과 uv를 사용하며, LangChain·LangGraph 기반 백엔드와 Alpine.js·Tailwind CSS 기반 정적 웹으로 구성한다.

- `src/app/agents/`: Supervisor와 인사·쇼핑몰 전문 에이전트
- `src/app/tools/`: 규정 검색, 시간 조회, 기능 소개 및 원문 요약 도구
- `src/app/prompts/templates/`: 에이전트·도구·대화 압축 프롬프트. `PromptLoader`로 읽는다
- `src/app/api/`: 채팅·SSE·관리자 API와 요청·응답 스키마
- `src/app/config/`: 모델, 벡터 저장소, 대화 저장소 및 관리자 설정
- `src/app/rag/`, `src/app/doc_importer.py`, `data/`: 문서 적재·검색과 원본 PDF
- `web/index.html`, `web/assets/`: 화면, JavaScript, CSS, SVG 및 로컬 글꼴
- `tests/`: 테스트. 실제 외부 서비스 없이 실행 가능한 테스트를 우선한다
- `docker-compose-local.yml`, `.devcontainer/`: 로컬 서비스와 개발 컨테이너 설정

## 구현 시 확인할 계약

- Supervisor가 도구를 선택하며 규정·CS 답변은 검색 근거와 출처에 기반한다. 실제 인사 신청·주문 변경·환불·지원금 지급 기능은 없다.
- 도구는 기존 `as_tool()` 패턴을 따른다. 새 기능은 Supervisor 등록과 기능 소개에 반영되는지 확인한다.
- `summarize_text`는 사용자 원문 요약 도구다. 내부 LangGraph는 요약·대조 후 최대 2회 수정하며, 대화 기록 압축용 `SummarizationMiddleware`와 구분한다.
- 요약 도구의 원문 한도는 12,000자지만 채팅 API의 `message`는 1,000자다. 한쪽을 바꾸면 스키마·도구 설명·README의 제한을 함께 확인한다.
- 대화 상태는 `thread_id`로 구분한다. SSE는 `start`, `token`, `done`, `error` 이벤트를 사용하며, 화면에는 Supervisor의 최종 응답만 스트리밍한다.
- 관리자 대화 조회는 `ADMIN_API_KEY`와 `X-Admin-API-Key` 헤더를 사용한다. 키를 웹 자산이나 로그에 포함하지 않는다.
- 웹은 밝게·어둡게·시스템 테마를 지원한다. 스타일 수정 시 CSS 변수, Tailwind 선택자 우선순위, 모바일 화면과 키보드 포커스를 확인한다.

## 실행과 검증

- 개발 컨테이너의 Python 환경은 `/opt/venv/bin/python`이다. 실행 방법과 환경 변수는 `README.md`, `.env.example`을 참고한다.
- 로컬 서비스: `docker compose -f docker-compose-local.yml up --build -d`
- 웹: `http://localhost:16123`, API 명세: `http://localhost:16124/docs`
- Python 포맷: `uv run black --check <변경한 Python 파일>`
- 웹·문서 포맷: `npx prettier --check <변경한 파일>`
- 요약 그래프 단위 테스트: `uv run python -m unittest discover -s tests -p test_summary_tool.py -v`
- 변경 범위에 맞는 검증을 실행하고, 실제 모델·임베딩·DB 호출 여부와 실행하지 못한 검증을 구분해 보고한다.
- 서버 초기화와 문서 적재는 외부 API 호출이나 DB 접근·변경을 유발할 수 있다. 검증을 위해 실행할 때는 영향을 먼저 확인한다.
- `shutdown.sh`는 DB 볼륨을 삭제한다. 데이터 보존이 필요한 종료는 `docker compose -f docker-compose-local.yml down`을 사용한다.

## 프로젝트 스킬

### 커밋

커밋 생성 또는 커밋 메시지 작성 요청을 처리할 때는 먼저 [git-commit 스킬](.agents/skills/git-commit/SKILL.md)을 읽고 따른다.

- `type(scope): gitmoji 한글 설명` 형식을 사용한다. scope는 `.vscode/settings.json`의 `conventionalCommits.scopes`에서 선택한다.
- 추가 지시 없이 `$git-commit`만 호출하면 현재 스테이징된 변경을 커밋한다. 미스테이징·미추적 파일은 자동 추가하지 않으며, 스테이징이 비어 있으면 종료한다.
- 커밋 전 보안 점검·필요한 코드 리뷰·검증과 Git 훅을 실행한다. 메시지 초안 요청이나 스킬 수정 요청 자체는 커밋 실행 요청이 아니다.

### 코드 리뷰

코드 리뷰 요청을 처리할 때는 먼저 [code-review 스킬](.agents/skills/code-review/SKILL.md)을 읽고 따른다. 발견 사항과 수정안을 보고하고 사용자의 수정 승인을 받은 뒤 적용한다.

### 보안 점검

보안 검사, 민감정보·취약점 또는 deprecated 코드 점검 요청을 처리할 때는 먼저 [security-check 스킬](.agents/skills/security-check/SKILL.md)을 읽고 따른다. 민감한 값은 출력하지 않고 발견 사항을 보고하며, 사용자 승인 후 수정한다.
