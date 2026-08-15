"""대한항공 국내공항별 취항 국제선 목적지 정적 데이터.

실제 서비스 전에 대한항공 취항지 페이지 기준으로 갱신 필요 (MVP는 주요 노선만).
"""
from app.models.schemas import RouteOption

ROUTE_MAP: dict[str, list[RouteOption]] = {
    "ICN": [
        RouteOption(dest="NRT", dest_name="도쿄(나리타)"),
        RouteOption(dest="KIX", dest_name="오사카"),
        RouteOption(dest="LAX", dest_name="로스앤젤레스"),
        RouteOption(dest="JFK", dest_name="뉴욕"),
        RouteOption(dest="CDG", dest_name="파리"),
        RouteOption(dest="LHR", dest_name="런던"),
        RouteOption(dest="SIN", dest_name="싱가포르"),
        RouteOption(dest="BKK", dest_name="방콕"),
    ],
    "GMP": [
        RouteOption(dest="HND", dest_name="도쿄(하네다)"),
        RouteOption(dest="KIX", dest_name="오사카"),
    ],
    "PUS": [
        RouteOption(dest="NRT", dest_name="도쿄(나리타)"),
        RouteOption(dest="KIX", dest_name="오사카"),
    ],
    "CJU": [
        RouteOption(dest="NRT", dest_name="도쿄(나리타)"),
    ],
}


def get_routes_for(dep: str) -> list[RouteOption]:
    """출발 공항 코드로 갈 수 있는 노선 목록을 반환한다.

    Args:
        dep: 출발 국내공항 IATA 코드 (예: ICN).

    Returns:
        해당 공항에서 취항하는 목적지 목록. 매핑에 없으면 빈 리스트.
    """
    return ROUTE_MAP.get(dep.upper(), [])
