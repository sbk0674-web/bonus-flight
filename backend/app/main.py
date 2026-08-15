"""FastAPI 앱 엔트리포인트."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import calendar, routes

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
