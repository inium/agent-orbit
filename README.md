# Orbit - 가상의 회사 (주)길동상사의 사내 AI Agent

![Orbit Web](./docs/screenshot-web.png)

![Orbit Web Chat ](./docs/screenshot-chat.png)

가상의 회사 (주)길동상사의 사내 규정과 쇼핑몰 고객 응대 업무를 안내하는 AI 에이전트입니다.

웹 화면은 Tailwind CSS, Penguin UI, Alpine.js로 구성합니다. LangChain·LangGraph 기반 Supervisor가 질문에 맞는 서브에이전트의 도구를 선택하며, 규정 검색에는 PostgreSQL·pgvector를, 대화 저장에는 별도 PostgreSQL 체크포인터를 사용합니다. LLM과 임베딩 모델은 OpenAI의 제품을 이용합니다.

## 주요 기능

| 기능                 | 지원 범위                                                                   |
| -------------------- | --------------------------------------------------------------------------- |
| 인사 규정 안내 (RAG) | 취업규칙의 근무·휴가 기준, 출장여비 지급·정산 기준, 복리후생 지원 조건 검색 |
| 쇼핑몰 CS 안내 (RAG) | 주문·결제·배송·취소·교환·반품·환불 및 고객 불만 응대 매뉴얼 검색            |
| 텍스트 요약          | 사용자가 제공한 원문 요약, 원문 대조 및 최대 2회 수정                       |
| 현재 시간 조회       | 국가명·국가 코드 또는 IANA 시간대의 현재 날짜와 시간 조회                   |
| 기능 소개            | Supervisor에 등록된 도구를 바탕으로 지원 기능 안내                          |

규정과 매뉴얼에 관한 답변은 검색 결과와 출처를 기반으로 제공합니다. 실제 인사 신청, 주문 조회·변경, 환불이나 지원금 지급은 수행하지 않습니다. 검색 근거가 부족하거나 도구가 지원하지 않는 요청은 확인할 수 없다고 안내합니다.

- RAG 임베딩에 사용한 pdf 문서들은 가상의 회사 길동상사에 맞게 제작되었으며, 실제 회사의 문서가 아닙니다.
- 문서는 `/data` 폴더의 문서를 이용합니다.

웹에서는 6개 업무 카드로 질문을 시작하고 대화방을 생성·선택·삭제할 수 있습니다. 밝게·어둡게·시스템 테마, 응답 스트리밍, 답변 복사와 요청별 LLM 토큰 사용량 표시를 지원합니다. 토큰 사용량은 모델이 보고한 입력·출력 합계이며 임베딩 사용량은 제외합니다.

## 개발 환경

### VS Code Dev Container

본 프로젝트는 VS Code의 **Dev Containers** 확장을 이용합니다. 설치 후 프로젝트 오픈 후 명령 팔레트에서 **Dev Containers: Reopen in Container**를 실행하세요.

### Docker

VS Code 없이 실행하거나 Dev Container 를 사용하지 않을 경우, 루트 `docker-compose-local.yml`을 사용합니다.
루트 `.env`가 없다면 `.env.example`을 복사하고 `OPENAI_API_KEY`를 입력하세요.
agent 컨테이너는 루트 `.env`에서 OpenAI 및 DB 설정을 전달받습니다.

- OpenAI 키 발급: https://platform.openai.com/api-keys

```sh
docker compose -f docker-compose-local.yml up --build -d
docker compose -f docker-compose-local.yml logs -f agent
```

| 서비스    | 호스트 접속 주소             | 컨테이너 내부 주소 |
| --------- | ---------------------------- | ------------------ |
| web       | http://localhost:16123       | web:80             |
| agent     | http://localhost:16124/docs  | agent:8000         |
| vector-db | localhost:16125 (PostgreSQL) | vector-db:5432     |
| memory-db | localhost:16126 (PostgreSQL) | memory-db:5432     |

DB는 루트 `.env`의 `VECTOR_DB_USERNAME`, `VECTOR_DB_PASSWORD`,
`VECTOR_DB_DATABASE`를 읽어 PostgreSQL의 `POSTGRES_*` 변수로 매핑합니다.
대화를 저장하는 체크포인터메 DB도 `MEMORY_DB_*` 설정을 같은 방식으로 읽습니다.

또한 본 프로젝트 docker compose의 실행 / 종료를 간편하게 할 수 있도록 `run.sh`, `shutdown.sh` 가 구현되어 있습니다.

`shutdown.sh`를 이용해 종료할 경우 DB 볼륨도 삭제합니다. DB를 보존하려면 아래 명령을 사용하세요.

```sh
docker compose -f docker-compose-local.yml down
```

### 문서 임베딩

본 프로젝트 실행 후 `/data` 내 [취업규칙](<./data/취업규칙%20-%20(주)길동상사.pdf>), [복리후생](<./data/복리후생%20규정%20-%20(주)길동상사.pdf>), [출장여비](<./data/출장여비%20규정%20-%20(주)길동상사.pdf>), [CS 매뉴얼](<./data/쇼핑몰%20CS%20실무%20매뉴얼%20-%20(주)길동상사.pdf>) pdf 파일들을 Vector DB에 임베딩 해야 합니다. 아래 명령어를 이용해 임베딩을 해주세요.

```sh
uv run python ./src/app/doc_importer.py
```

### 실행

프로젝트 실행과 RAG 문서 임베딩이 끝난 후 `http://localhost:16123`을 통해 채팅 페이지를 실행할 수 있으며, `https://localhost:16124/docs` 를 통해 API 구현 명세를 확인할 수 있습니다.

| 서비스 | 호스트 접속 주소            | 설명              |
| ------ | --------------------------- | ----------------- |
| web    | http://localhost:16123      | 채팅 페이지       |
| agent  | http://localhost:16124/docs | 에이전트 API 명세 |

### Code Formatting & Lint

본 프로젝트는 코드 포맷과 커밋 시 사용하는 Lint가 설정되어 있습니다.

python은 black formatter, 그 외 파일들은 prettier를 이용합니다.
커밋 시 커밋 메시지를 검사하는 lint가 설정되어 있습니다.

## HTTP Api

채팅 웹 페이지는 에이전트 API `/chat/stream`와 대화하며, 대화 내역 조회는 Admin API인 `/admin/conversation/{thread_id}`를 통해 조회할 수 있습니다.

- 상세 요청·응답 스키마는 http://localhost:16124/docs에서 확인
- Admin API 호출은 `.env`의 `ADMIN_API_KEY` 필요

| 메서드 | 경로                               | 용도                               |
| ------ | ---------------------------------- | ---------------------------------- |
| POST   | `/chat`                            | 채팅 응답과 토큰 사용량 반환       |
| POST   | `/chat/stream`                     | SSE로 답변 스트리밍                |
| GET    | `/admin/conversations/{thread_id}` | 저장된 대화의 최신 체크포인트 조회 |

채팅 요청은 `message`와 선택적인 UUID `thread_id`를 받습니다. 같은 대화를 이어가려면 동일한 `thread_id`를 전달합니다. 생략하면 새 UUID가 생성됩니다. 스트리밍은 `start`, `token`, `done`, `error` 이벤트를 사용합니다.

관리자 대화 조회는 `.env`의 `ADMIN_API_KEY`를 설정하고 요청 헤더 `X-Admin-API-Key`로 전달해야 합니다. 키가 비어 있으면 503, 인증이 맞지 않으면 403, 저장된 대화가 없으면 404를 반환합니다. `namespace` 쿼리로 체크포인트 namespace를 지정할 수 있으며, 기본값은 루트 namespace입니다. 관리자 키를 웹 코드에 넣지 마세요.

## Skills

프로젝트 개발 작업에 사용하는 Codex 스킬은 `.agents/skills/`에서 관리합니다. 각 스킬의 적용 기준은 [AGENTS.md](AGENTS.md)에 안내되어 있으며, 웹 채팅 에이전트의 도구와는 별개입니다.

| 스킬                                                     | 용도                                                                                | 사용 예시                                    |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------- |
| [git-commit](.agents/skills/git-commit/SKILL.md)         | 타입별 gitmoji와 한글 설명을 사용하는 Conventional Commits 메시지 작성 및 커밋 생성 | `$git-commit`                                |
| [code-review](.agents/skills/code-review/SKILL.md)       | 에이전트·웹·Docker 및 관련 설정의 변경 검토와 수정안 제시                           | `$code-review 스테이징된 변경을 리뷰해줘`    |
| [security-check](.agents/skills/security-check/SKILL.md) | 민감정보 노출, 위험한 코드·설정, 의존성 취약점과 deprecated API 점검                | `$security-check 스테이징된 변경을 점검해줘` |

`$git-commit`만 호출하면 현재 스테이징된 변경을 보안 점검·필요한 코드 리뷰·검증 후 커밋합니다. 미스테이징 변경과 미추적 파일은 자동으로 추가하지 않으며, 스테이징이 비어 있으면 종료합니다. 커밋 메시지는 `type(scope): gitmoji 한글 설명` 형식이며, scope는 `.vscode/settings.json`의 허용 목록에서 선택합니다.

코드 리뷰와 보안 점검에서 문제가 발견되면 발견 사항과 수정안을 먼저 보고하고, 사용자 승인 후 수정합니다. 메시지 초안만 요청한 경우에는 커밋을 생성하지 않습니다.

## LICENSE

MIT
