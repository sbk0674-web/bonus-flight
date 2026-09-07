"""대한항공 국내공항별 취항 국제선 목적지 정적 데이터.

대한항공 공식 API(getRouteByAirport, /booking/reservation-guide/route-map)를 실사로
조회해 갱신함 (2026-08-16 기준, 향후 30일 스케줄 기준 안내). 국내선 목적지는 이 앱의
스코프(국제선 왕복)에서 제외했다.
"""
from app.models.schemas import RouteOption

ROUTE_MAP: dict[str, list[RouteOption]] = {
    "ICN": [
        RouteOption(dest="KOJ", dest_name="가고시마"),
        RouteOption(dest="KMQ", dest_name="고마쓰"),
        RouteOption(dest="UKB", dest_name="고베"),
        RouteOption(dest="CAN", dest_name="광저우"),
        RouteOption(dest="KMJ", dest_name="구마모토"),
        RouteOption(dest="NGS", dest_name="나가사키"),
        RouteOption(dest="NGO", dest_name="나고야"),
        RouteOption(dest="NKG", dest_name="난징"),
        RouteOption(dest="KIJ", dest_name="니가타"),
        RouteOption(dest="DLC", dest_name="다롄"),
        RouteOption(dest="NRT", dest_name="도쿄/나리타"),
        RouteOption(dest="HND", dest_name="도쿄/하네다"),
        RouteOption(dest="MFM", dest_name="마카오"),
        RouteOption(dest="PEK", dest_name="베이징/서우두"),
        RouteOption(dest="CTS", dest_name="삿포로/치토세"),
        RouteOption(dest="PVG", dest_name="상하이/푸동"),
        RouteOption(dest="XMN", dest_name="샤먼"),
        RouteOption(dest="SHE", dest_name="선양"),
        RouteOption(dest="SZX", dest_name="선전"),
        RouteOption(dest="XIY", dest_name="시안/셴양"),
        RouteOption(dest="AOJ", dest_name="아오모리"),
        RouteOption(dest="YNJ", dest_name="옌지"),
        RouteOption(dest="KIX", dest_name="오사카/간사이"),
        RouteOption(dest="OKJ", dest_name="오카야마"),
        RouteOption(dest="OKA", dest_name="오키나와"),
        RouteOption(dest="WUH", dest_name="우한"),
        RouteOption(dest="DYG", dest_name="장자제"),
        RouteOption(dest="CGO", dest_name="정저우"),
        RouteOption(dest="CSX", dest_name="창사"),
        RouteOption(dest="TAO", dest_name="칭다오"),
        RouteOption(dest="KMG", dest_name="쿤밍"),
        RouteOption(dest="TPE", dest_name="타이베이/타오위엔"),
        RouteOption(dest="TSN", dest_name="톈진"),
        RouteOption(dest="FOC", dest_name="푸저우"),
        RouteOption(dest="HGH", dest_name="항저우"),
        RouteOption(dest="HFE", dest_name="허페이"),
        RouteOption(dest="HKG", dest_name="홍콩"),
        RouteOption(dest="FUK", dest_name="후쿠오카"),
        RouteOption(dest="CXR", dest_name="나트랑"),
        RouteOption(dest="DAD", dest_name="다낭"),
        RouteOption(dest="DPS", dest_name="덴파사르 (발리)"),
        RouteOption(dest="DEL", dest_name="델리"),
        RouteOption(dest="MNL", dest_name="마닐라"),
        RouteOption(dest="BKK", dest_name="방콕/수완나품"),
        RouteOption(dest="CEB", dest_name="세부"),
        RouteOption(dest="SIN", dest_name="싱가포르/창이"),
        RouteOption(dest="RGN", dest_name="양곤"),
        RouteOption(dest="CGK", dest_name="자카르타/수카르노 하타"),
        RouteOption(dest="KTM", dest_name="카트만두"),
        RouteOption(dest="KUL", dest_name="쿠알라룸푸르"),
        RouteOption(dest="HKT", dest_name="푸껫"),
        RouteOption(dest="PQC", dest_name="푸꾸옥"),
        RouteOption(dest="KTI", dest_name="프놈펜/떼쪼"),
        RouteOption(dest="HAN", dest_name="하노이"),
        RouteOption(dest="SGN", dest_name="호찌민"),
        RouteOption(dest="JFK", dest_name="뉴욕/존 F. 케네디"),
        RouteOption(dest="DFW", dest_name="댈러스/포트워스"),
        RouteOption(dest="LAS", dest_name="라스베이거스/해리 리드"),
        RouteOption(dest="LAX", dest_name="로스앤젤레스"),
        RouteOption(dest="YVR", dest_name="밴쿠버"),
        RouteOption(dest="BOS", dest_name="보스턴"),
        RouteOption(dest="SFO", dest_name="샌프란시스코"),
        RouteOption(dest="SEA", dest_name="시애틀/터코마"),
        RouteOption(dest="ORD", dest_name="시카고/오헤어"),
        RouteOption(dest="ATL", dest_name="애틀랜타/하츠필드잭슨"),
        RouteOption(dest="IAD", dest_name="워싱턴/덜레스"),
        RouteOption(dest="YYZ", dest_name="토론토/피어슨"),
        RouteOption(dest="HNL", dest_name="호놀룰루 (하와이)"),
        RouteOption(dest="LHR", dest_name="런던/히스로"),
        RouteOption(dest="FCO", dest_name="로마/레오나르도 다빈치"),
        RouteOption(dest="LIS", dest_name="리스본"),
        RouteOption(dest="MAD", dest_name="마드리드"),
        RouteOption(dest="MXP", dest_name="밀라노/말펜사"),
        RouteOption(dest="BUD", dest_name="부다페스트"),
        RouteOption(dest="VIE", dest_name="비엔나"),
        RouteOption(dest="AMS", dest_name="암스테르담/스키폴"),
        RouteOption(dest="IST", dest_name="이스탄불"),
        RouteOption(dest="ZRH", dest_name="취리히"),
        RouteOption(dest="CDG", dest_name="파리/샤를 드 골"),
        RouteOption(dest="PRG", dest_name="프라하"),
        RouteOption(dest="FRA", dest_name="프랑크푸르트"),
        RouteOption(dest="GUM", dest_name="괌"),
        RouteOption(dest="BNE", dest_name="브리즈번"),
        RouteOption(dest="SYD", dest_name="시드니/킹즈퍼드 스미스"),
        RouteOption(dest="AKL", dest_name="오클랜드"),
        RouteOption(dest="UBN", dest_name="울란바타르/칭기즈칸 국제공항"),
    ],
    "GMP": [
        RouteOption(dest="HND", dest_name="도쿄/하네다"),
        RouteOption(dest="PEK", dest_name="베이징/서우두"),
        RouteOption(dest="SHA", dest_name="상하이/홍차오"),
        RouteOption(dest="KIX", dest_name="오사카/간사이"),
    ],
    "PUS": [
        RouteOption(dest="NGO", dest_name="나고야"),
        RouteOption(dest="NRT", dest_name="도쿄/나리타"),
        RouteOption(dest="PEK", dest_name="베이징/서우두"),
        RouteOption(dest="PVG", dest_name="상하이/푸동"),
        RouteOption(dest="TAO", dest_name="칭다오"),
        RouteOption(dest="TPE", dest_name="타이베이/타오위엔"),
        RouteOption(dest="DAD", dest_name="다낭"),
    ],
    "CJU": [
        RouteOption(dest="NRT", dest_name="도쿄/나리타"),
        RouteOption(dest="PEK", dest_name="베이징/서우두"),
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
