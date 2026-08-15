"""FastAPI 앱 엔트리포인트."""
from fastapi import FastAPI

app = FastAPI(title="krean-mileage-backend")


@app.get("/health")
def health() -> dict[str, str]:
    """헬스체크."""
    return {"status": "ok"}
