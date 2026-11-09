export default class ChatApp {
  /**
   * Constructor
   *
   * 입력값, 대화방 목록과 추천 질문 카드 초기화
   * @param {string} requestUrl - 에이전트 스트리밍 API URL
   */
  constructor(requestUrl) {
    // 스트리밍 URL을 재할당할 수 없는 멤버 속성으로 정의합니다.
    Object.defineProperty(this, "requestUrl", {
      value: requestUrl,
      writable: false,
      configurable: false,
      enumerable: true,
    });

    this.prompt = ""; // 현재 입력 중인 질문
    this.mode = "균형 잡힌 답변"; // 현재 선택된 답변 모드
    this.roomsOpen = false; // 대화방 목록 열림 여부
    this.rooms = []; // 대화방 목록
    this.activeId = null; // 현재 선택된 대화방의 UUID
    this.copied = false; // 마지막으로 복사한 메시지 여부
    this.cards = ChatApp.createCards(); // 추천 질문 카드 목록
  }

  /**
   * 서버 오류 JSON에서 사용자에게 표시할 메시지만 추출합니다.
   *
   * @param {unknown} data - 서버가 반환한 오류 JSON 또는 일반 텍스트
   * @param {string} fallback - 오류 메시지를 추출할 수 없을 때 사용할 기본 문구
   * @returns {string} 추출한 오류 메시지 또는 기본 문구
   */
  static errorMessage(data, fallback) {
    if (typeof data === "string") {
      return data.trim() || fallback;
    }

    if (!data || typeof data !== "object") {
      return fallback;
    }

    for (const key of ["message", "detail", "error"]) {
      const value = data[key];
      if (typeof value === "string" && value.trim()) {
        return value.trim();
      }

      if (Array.isArray(value)) {
        const messages = value
          .filter((item) => typeof item?.msg === "string")
          .map((item) => item.msg);

        if (messages.length) {
          return messages.join("\n");
        }
      }
    }
    return fallback;
  }

  /**
   * 에이전트 스트리밍 응답을 읽고 처리하는 함수
   *
   * @param {Response} response - fetch 요청의 Response 객체
   * @param {function(string): void} onText - 새로운 텍스트를 처리하는 콜백 함수
   * @returns {Promise<Object|null>} 완료 이벤트의 LLM 토큰 사용량
   */
  static async readAgentStream(response, onText) {
    if (!response.body) {
      throw new Error("스트리밍 응답을 읽을 수 없습니다.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finished = false;
    let usage = null;

    function handleEvent(block) {
      let event = "message";
      const lines = [];
      for (const line of block.split(/\r\n|\n|\r/)) {
        if (line.startsWith(":")) continue;
        const separator = line.indexOf(":");
        const field = separator < 0 ? line : line.slice(0, separator);
        const value =
          separator < 0 ? "" : line.slice(separator + 1).replace(/^ /, "");
        if (field === "event") event = value;
        if (field === "data") lines.push(value);
      }
      const payload = lines.join("\n");
      if (event === "error") {
        let data = payload;
        try {
          data = JSON.parse(payload);
        } catch {
          // JSON이 아닌 SSE 오류는 텍스트 메시지로 처리합니다.
        }
        throw new Error(
          ChatApp.errorMessage(
            data,
            "에이전트 스트림에서 오류가 발생했습니다.",
          ),
        );
      }

      if (event === "done" || payload === "[DONE]") {
        if (event === "done" && payload && payload !== "[DONE]") {
          const data = JSON.parse(payload);
          const reportedUsage = data?.usage;
          if (
            reportedUsage &&
            ["input_tokens", "output_tokens", "total_tokens"].every(
              (key) =>
                Number.isSafeInteger(reportedUsage[key]) &&
                reportedUsage[key] >= 0,
            )
          ) {
            usage = reportedUsage;
          }
        }

        finished = true;

        return;
      }

      if (event === "start") {
        return;
      }

      if (!lines.length || !payload) {
        return;
      }

      let data;

      try {
        data = JSON.parse(payload);
      } catch {
        data = payload;
      }

      if (data?.error) {
        throw new Error(
          typeof data.error === "string"
            ? data.error
            : "에이전트 응답 오류가 발생했습니다.",
        );
      }

      if (event !== "token") {
        return;
      }

      if (typeof data?.text !== "string") {
        throw new Error("토큰 이벤트에 text 문자열이 없습니다.");
      }

      onText(data.text);
    }

    try {
      while (!finished) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });

        let boundary;

        while (!finished && (boundary = /\r\n\r\n|\n\n|\r\r/.exec(buffer))) {
          const block = buffer.slice(0, boundary.index);
          buffer = buffer.slice(boundary.index + boundary[0].length);

          handleEvent(block);
        }

        if (done) {
          if (!finished && buffer.trim()) {
            handleEvent(buffer);
          }

          break;
        }
      }
    } finally {
      try {
        await reader.cancel();
      } finally {
        reader.releaseLock();
      }
    }

    return usage;
  }

  /**
   * Alpine 컴포넌트 초기화 & 첫 대화방 생성
   *
   * @return {void}
   */
  init() {
    this.createRoom();
  }

  /**
   * 현재 선택한 대화방을 반환
   * - 선택된 방이 없으면 undefined 반환
   *
   * @return {Object|undefined} 현재 선택한 대화방 객체 또는 undefined
   */
  get activeRoom() {
    return this.rooms.find((room) => room.id === this.activeId);
  }

  /**
   * 현재 대화방의 메시지 반환
   * - 선택된 방이 없으면 빈 배열 반환
   *
   * @return {Array} 현재 대화방의 메시지 배열
   */
  get messages() {
    return this.activeRoom?.messages || [];
  }

  /**
   * 현재 대화방에서 답변을 기다리는 중인지 여부 반환
   *
   * @return {boolean} 답변 대기 중이면 true, 그렇지 않으면 false
   */
  get loading() {
    return this.activeRoom?.loading || false;
  }

  /**
   * 인스턴스마다 독립적으로 사용할 추천 질문 카드 목록 생성
   *
   * @return {Array} 추천 질문 카드 배열
   */
  static createCards() {
    return [
      {
        title: "휴가·근무 규정",
        desc: "연차와 휴가, 근무 기준을 확인해요",
        prompt: "연차휴가의 사용 기준과 신청 절차를 알려 주세요.",
      },
      {
        title: "출장비 안내",
        desc: "출장비 지급 기준과 정산 방법을 알아봐요",
        prompt:
          "국내 2박 3일 출장의 여비 기준과 정산에 필요한 증빙을 알려 주세요.",
      },
      {
        title: "복리후생 안내",
        desc: "복지 혜택과 지원 조건을 확인해요",
        prompt: "회사 복리후생의 지원 항목과 신청 조건을 알려 주세요.",
      },
      {
        title: "주문·배송 응대",
        desc: "주문과 배송 문의의 응대 절차를 확인해요",
        prompt:
          "배송 지연 문의가 들어왔을 때 확인할 사항과 고객 안내 문구를 알려 주세요.",
      },
      {
        title: "취소·교환·반품",
        desc: "처리 조건과 절차, 비용 기준을 알아봐요",
        prompt:
          "단순 변심 반품의 접수 조건과 절차, 배송비 부담 기준을 알려 주세요.",
      },
      {
        title: "고객 불만 응대",
        desc: "매뉴얼에 맞는 대응 방법을 찾아봐요",
        prompt:
          "상품 불량으로 불만을 제기한 고객의 응대 절차와 안내 문구를 알려 주세요.",
      },
    ];
  }

  /**
   * 현재 입력 중인 초안을 보관하고 새 대화방을 생성해 선택
   *
   * @return {void}
   */
  createRoom() {
    // 새 대화방 객체 생성
    const room = {
      id: crypto.randomUUID(),
      title: "새로운 대화",
      messages: [],
      loading: false,
      draft: "",
    };

    // 현재 선택된 방이 있으면 초안을 보관
    if (this.activeRoom) {
      this.activeRoom.draft = this.prompt;
    }

    this.rooms.unshift(room); // 새 대화방을 목록 맨 앞에 추가
    this.activeId = room.id; // 새 대화방을 선택
    this.prompt = ""; // 입력창 초기화
    this.copied = false; // 복사 상태 초기화
  }

  /**
   * 대화방을 삭제하고, 선택된 방이었다면 인접한 방 선택 후 오픈
   * 마지막 방을 삭제하면 빈 대화방을 새로 생성
   *
   * @param {string} id - 삭제할 대화방의 UUID
   */
  deleteRoom(id) {
    // 삭제할 방의 인덱스를 찾음
    const index = this.rooms.findIndex((room) => room.id === id);
    if (index < 0) {
      return;
    }

    const wasActive = this.activeId === id; // 삭제할 방이 현재 선택된 방인지 확인
    this.rooms.splice(index, 1);
    if (!wasActive) {
      return;
    }

    this.activeId = null; // 선택된 방이 삭제되었으므로 activeId를 null로 초기화
    this.prompt = ""; // 선택된 방이 없으므로 입력창을 비움
    this.copied = false; // 복사 상태 초기화

    // 삭제 후 남은 방이 없으면 새 방 생성, 있으면 인접한 방 선택
    if (!this.rooms.length) {
      this.createRoom();
    } else {
      this.selectRoom(this.rooms[Math.min(index, this.rooms.length - 1)].id);
    }
  }

  /**
   * 현재 초안을 보관하고 선택한 대화방의 초안과 메시지 화면 복원
   *
   * @param {string} id - 목록에 존재하는 대화방의 UUID
   */
  selectRoom(id) {
    // 현재 선택된 방이 있으면 초안을 보관
    if (this.activeRoom) {
      this.activeRoom.draft = this.prompt;
    }

    this.activeId = id; // 선택한 방의 UUID를 activeId로 설정
    this.prompt = this.activeRoom.draft; // 선택한 방의 초안을 입력창에 복원
    this.copied = false; // 복사 상태 초기화
    this.roomsOpen = false; // 대화방 목록 닫기

    this.scroll(); // 선택한 방의 메시지 화면을 맨 아래로 스크롤
  }

  /**
   * 현재 질문을 전송하고 SSE(Server-Sent Events) 토큰을
   * 해당 대화방의 답변에 순서대로 추가
   * 빈 입력과 중복 전송을 방지하며, 실패 시 오류 메시지 표시
   *
   * @returns {Promise<void>} 응답 처리와 로딩 상태 해제가 완료되면 종료
   */
  async send() {
    // 입력값을 공백 제거 후 확인
    const value = this.prompt.trim();
    if (!value || this.loading) {
      return;
    }

    // 현재 선택된 대화방을 가져옴
    const room = this.activeRoom;
    if (!room.messages.length) {
      room.title = value;
    }

    // 질문 메시지를 대화방에 추가하고 입력창 초기화
    room.messages.push({ role: "user", text: value });
    room.draft = "";
    this.prompt = "";
    room.loading = true;
    this.scroll();

    try {
      // 에이전트에게 질문을 전송하고 SSE 응답을 처리
      const response = await fetch(this.requestUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ thread_id: room.id, message: value }),
      });

      if (!response.ok) {
        const fallback = `에이전트 요청에 실패했습니다. (HTTP ${response.status})`;
        let message = fallback;
        try {
          message = ChatApp.errorMessage(await response.json(), fallback);
        } catch {
          // 프록시의 HTML 오류 페이지 등은 표시하지 않고 상태 코드로 안내합니다.
        }
        throw new Error(
          message === fallback ? fallback : `${fallback}\n${message}`,
        );
      }

      // 응답의 Content-Type이 SSE 형식인지 확인
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("text/event-stream")) {
        throw new Error("서버가 SSE 형식으로 응답하지 않았습니다.");
      }

      // SSE 응답을 읽고 처리하며, 답변 메시지를 대화방에 추가
      let answerIndex = null;
      const usage = await ChatApp.readAgentStream(response, (text) => {
        // 새로운 텍스트가 없으면 처리하지 않음
        if (!text) {
          return;
        }

        // 답변 메시지가 없으면 새 메시지를 추가하고 인덱스를 저장
        if (answerIndex === null) {
          answerIndex = room.messages.length;
          room.messages.push({ role: "assistant", text: "", usage: null });
        }

        room.messages[answerIndex].text += text;

        // 현재 선택된 방이 답변을 받고 있는 방이면 스크롤
        if (this.activeId === room.id) {
          this.scroll();
        }
      });

      if (answerIndex === null) {
        throw new Error("에이전트가 빈 답변을 반환했습니다.");
      }

      room.messages[answerIndex].usage = usage;
    } catch (error) {
      // 에러 발생 시 대화방에 오류 메시지 추가
      room.messages.push({
        role: "error",
        text:
          error instanceof TypeError
            ? "에이전트에 연결하지 못했습니다. API 서버 연결과 CORS 설정을 확인한 뒤 다시 시도해 주세요."
            : error.message ||
              "답변을 가져오지 못했습니다. 다시 시도해 주세요.",
      });
    } finally {
      // 로딩 상태 해제
      room.loading = false;

      // 현재 선택된 방이 답변을 받고 있는 방이면 스크롤
      if (this.activeId === room.id) {
        this.scroll();
      }
    }
  }

  /**
   * Alpine의 화면 갱신이 끝나면 대화 영역을 맨 아래로 스크롤
   *
   * @return {void}
   */
  scroll() {
    this.$nextTick(() => {
      const el = document.getElementById("conversation");

      el.scrollTop = el.scrollHeight;
    });
  }
}
