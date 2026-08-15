"""정적 노선 조회 라우터."""
from fastapi import APIRouter, Query

from app.data.route_map import get_routes_for
from app.models.schemas import RouteOption

router = APIRouter()


@router.get("/api/routes", response_model=list[RouteOption])
def list_routes(
    dep: str = Query(..., description="출발 국내공항 IATA 코드"),
    month: str = Query(..., description="출발월 YYYY-MM"),
) -> list[RouteOption]:
    """출발지에서 갈 수 있는 노선 목록을 반환한다 (정적 데이터, 즉시 응답)."""
    return get_routes_for(dep)
