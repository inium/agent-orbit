import ChatApp from "./chat-app.js";
import OrbitTheme from "./orbit-theme.js";

// SSE(Server-Sent Events) 요청 URL (Agent Orbit 서버의 /chat/stream 엔드포인트)
const requestUrl = "http://localhost:16124/chat/stream";

/**
 * Alpine.js 초기화 이벤트 리스너
 *  - 테마와 채팅 컴포넌트 등록
 */
document.addEventListener("alpine:init", () => {
  // Alpine.js에 OrbitTheme와 ChatApp 컴포넌트 등록
  Alpine.data("orbitTheme", () => new OrbitTheme());
  Alpine.data("chatApp", () => new ChatApp(requestUrl));
});

// 모듈과 컴포넌트 등록 준비가 끝난 뒤 Alpine 로드
const alpineScript = document.createElement("script");
alpineScript.src =
  "https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js";
document.head.appendChild(alpineScript);

/**
 * 단축키 누르면 텍스트 입력 창에 커서 Focus
 * 단축키: Cmd/Ctrl + K
 */
window.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();

    document.querySelector("textarea").focus();
  }
});
