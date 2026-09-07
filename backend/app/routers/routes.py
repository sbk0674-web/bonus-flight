"""노선 조회 라우터."""
import asyncio

from fastapi import APIRouter, Depends, Query

from app.data.route_map import get_routes_for
from app.models.schemas import RouteOption
from app.routers.calendar import get_award_search_service
from app.services.award_search_service import AwardSearchService

router = APIRouter()

ROUTE_FILTER_CONCURRENCY = 6


@router.get("/api/routes", response_model=list[RouteOption])
async def list_routes(
    dep: str = Query(..., description="출발 국내공항 IATA 코드"),
    month: str = Query(..., description="출발월 YYYY-MM"),
    service: AwardSearchService = Depends(get_award_search_service),
) -> list[RouteOption]:
    """출발지에서 갈 수 있는 노선 중, 그 달에 실제 좌석이 있는 노선만 반환한다.

    정적 목록(get_routes_for)은 "대한항공이 이 공항에서 어디로 가는지"만 알려주고
    특정 달에 그 노선이 실제로 있는지는 모른다 — bonusSeatView로 노선별로 확인해서
    거른다. 결과는 24시간 캐싱되므로 같은 (출발지, 달) 조합은 이후 요청부터 빠르다.
    """
    candidates = get_routes_for(dep)
    semaphore = asyncio.Semaphore(ROUTE_FILTER_CONCURRENCY)

    async def _check(route: RouteOption) -> RouteOption | None:
        async with semaphore:
            has_seats = await service.has_route_in_month(dep, route.dest, month)
        return route if has_seats else None

    results = await asyncio.gather(*(_check(r) for r in candidates))
    return [r for r in results if r is not None]
