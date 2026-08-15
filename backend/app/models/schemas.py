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


class SettingsStatus(BaseModel):
    """GET /api/settings 응답. 비밀번호는 절대 포함하지 않는다."""

    configured: bool
    koreanair_id: str | None = None


class SettingsRequest(BaseModel):
    """POST /api/settings 요청 바디."""

    koreanair_id: str
    koreanair_pw: str
