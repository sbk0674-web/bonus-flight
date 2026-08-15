"""FastAPI 앱 엔트리포인트."""
from dotenv import load_dotenv

load_dotenv()  # app.routers 등에서 환경 변수를 읽기 전에 .env를 먼저 로드

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.routers import calendar, routes, settings  # noqa: E402

app = FastAPI(title="krean-mileage-backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes.router)
app.include_router(calendar.router)
app.include_router(settings.router)


@app.get("/health")
def health() -> dict[str, str]:
    """헬스체크."""
    return {"status": "ok"}
