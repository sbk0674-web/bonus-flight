"""API 요청/응답 Pydantic 모델."""
from pydantic import BaseModel


class SeatCounts(BaseModel):
    """등급별 잔여석 수."""

    economy: int
    business: int
    first: int


class FlightOption(BaseModel):
    """하루 중 특정 편의 시간/등급별 잔여석."""

    flight_no: str
    dep_time: str
    arr_time: str
    seats: SeatCounts
    operator_code: str | None = None
    operator_name: str | None = None
    code_share: bool = False


class CalendarDay(BaseModel):
    """특정 날짜에 좌석이 있는 편 목록."""

    date: str
    flights: list[FlightOption]


class RouteOption(BaseModel):
    """출발지에서 갈 수 있는 노선(목적지) 하나."""

    dest: str
    dest_name: str


class CalendarRequest(BaseModel):
    """POST /api/calendar 요청 바디."""

    dep: str
    dest: str
    month: str


class AwardPriceRequest(BaseModel):
    """POST /api/award-price 요청 바디. 왕복 최종 선택 시점에 1번만 호출."""

    dep: str
    dest: str
    outbound_date: str
    outbound_flight_no: str
    inbound_date: str
    inbound_flight_no: str


class LegPrice(BaseModel):
    """편도 1개의 소요 마일리지/운임."""

    mileage: int
    fare_krw: int


class AwardPriceResponse(BaseModel):
    """POST /api/award-price 응답. 못 찾으면 라우터가 404를 돌려준다."""

    outbound: LegPrice
    inbound: LegPrice
