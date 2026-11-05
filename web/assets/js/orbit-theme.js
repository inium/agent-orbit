export default class OrbitTheme {
  /**
   * Constructor
   * 저장된 테마를 불러오고, 유효하지 않으면 시스템 설정을 사용해 초기 화면에 적용
   */
  constructor() {
    this.themes = ["light", "dark", "system"]; // 테마 목록
    this.media = window.matchMedia("(prefers-color-scheme: dark)"); // 시스템 테마 감지용 MediaQueryList
    this.theme = localStorage.getItem("orbit-theme") || "system"; // 현재 선택된 테마

    if (!this.themes.includes(this.theme)) {
      this.theme = "system";
    }

    this.applyTheme();
  }

  /**
   * Alpine.js 초기화 시 시스템 테마 변경을 감지할 이벤트 핸들러 등록
   */
  init() {
    this.onSystemThemeChange = this.onSystemThemeChange.bind(this);

    this.media.addEventListener("change", this.onSystemThemeChange);
  }

  /**
   * Alpine.js 컴포넌트가 제거될 때 시스템 테마 변경 이벤트 핸들러 해제
   */
  destroy() {
    this.media.removeEventListener("change", this.onSystemThemeChange);
  }

  /**
   * 선택한 테마와 시스템 설정에 따라 문서의 dark 클래스 갱신
   */
  applyTheme() {
    document.documentElement.classList.toggle(
      "dark",
      this.theme === "dark" || (this.theme === "system" && this.media.matches),
    );
  }

  /**
   * 시스템 테마가 변경되면, 사용자가 system 모드를 선택한 경우에만 화면에 반영
   *
   * @returns {void}
   */
  onSystemThemeChange() {
    if (this.theme === "system") {
      this.applyTheme();
    }
  }

  /**
   * 선택한 테마를 화면에 적용하고 다음 방문에도 유지하도록 로컬스토리지에 저장
   *
   * @param {"light" | "dark" | "system"} theme - 적용할 테마 모드
   * @returns {void}
   */
  setTheme(theme) {
    this.theme = theme;
    this.applyTheme();

    localStorage.setItem("orbit-theme", theme);
  }
}
