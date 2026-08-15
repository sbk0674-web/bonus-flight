"""로그인 후 실제 DOM을 빠르게 덤프하기 위한 1회용 디버그 스크립트.

브라우저를 띄우고 60초 기다린 뒤(로그인 성공 여부 상관없이) 그 시점 상태를
tmp/debug_dump.* 로 덤프한다. LOGIN_SUCCESS_MARKER를 확정하기 위한 용도.
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

TMP_DIR = Path(__file__).parent.parent / "tmp"
WAIT_SECONDS = 60


async def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    TMP_DIR.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.koreanair.com/korea/ko.html", timeout=30_000)
        print(f"{WAIT_SECONDS}초 기다립니다. 그 안에 브라우저에서 로그인하세요.")
        for i in range(WAIT_SECONDS, 0, -10):
            print(f"{i}초 남음...")
            await asyncio.sleep(10)

        (TMP_DIR / "debug_dump.html").write_text(await page.content(), encoding="utf-8")
        await page.screenshot(path=str(TMP_DIR / "debug_dump.png"))
        (TMP_DIR / "debug_dump_url.txt").write_text(page.url, encoding="utf-8")
        print(f"덤프 완료: {TMP_DIR}")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
