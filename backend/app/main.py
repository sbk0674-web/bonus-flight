"""FastAPI 앱 엔트리포인트."""
import asyncio
import sys

if sys.platform == "win32":
    # Windows 기본 SelectorEventLoop는 자식 프로세스(Playwright가 띄우는 브라우저)를
    # 지원하지 않는다. uvicorn이 이벤트 루프를 만들기 전에 정책을 바꿔야 한다.
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.routers import calendar, routes  # noqa: E402

app = FastAPI(title="krean-mileage-backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes.router)
app.include_router(calendar.router)


@app.get("/health")
def health() -> dict[str, str]:
    """헬스체크."""
    return {"status": "ok"}
