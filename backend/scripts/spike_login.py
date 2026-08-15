"""대한항공 마일리지 로그인+좌석조회 흐름 조사용 스파이크 스크립트.

사람이 직접 headed 모드로 실행해서 로그인(네이버 등 소셜 로그인 포함) →
마일리지 예매 토글 → 좌석 조회까지 수동으로 진행하며 각 단계 DOM/네트워크를
tmp/ 에 덤프한다. 이 결과를 보고 KoreanAirClient의 LOGIN_SUCCESS_MARKER,
CALENDAR_API_PATH 등 플레이스홀더 값을 확정한다.

실행: python scripts/spike_login.py
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

TMP_DIR = Path(__file__).parent.parent / "tmp"


def main() -> None:
  """headed 브라우저를 열고 수동 조작 후 Enter 누르면 DOM/네트워크를 덤프한다."""
  TMP_DIR.mkdir(exist_ok=True)
  requests_log: list[dict[str, str]] = []

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.on(
        "response",
        lambda res: requests_log.append({"url": res.url, "status": str(res.status)})
        if "koreanair" in res.url
        else None,
    )
    page.goto("https://www.koreanair.com/korea/ko.html")

    print("브라우저에서 직접 로그인(네이버 등 소셜 로그인 포함) → 마일리지 예매 토글 → 좌석 조회까지 진행하세요.")
    input("다 끝나면 Enter를 누르세요 (그 시점 DOM/네트워크를 덤프합니다)...")

    (TMP_DIR / "spike_dom_dump.html").write_text(page.content(), encoding="utf-8")
    (TMP_DIR / "spike_network.json").write_text(
        json.dumps(requests_log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"덤프 완료: {TMP_DIR}")
    browser.close()


if __name__ == "__main__":
  main()
