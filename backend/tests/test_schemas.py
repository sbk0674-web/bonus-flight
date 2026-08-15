"""Pydantic 스키마 검증 테스트."""
from app.models.schemas import (
    CalendarDay,
    CalendarRequest,
    FlightOption,
    RouteOption,
    SeatCounts,
)


def test_seat_counts_holds_three_cabin_classes():
    """SeatCounts는 이코노미/비즈니스/일등석 잔여석을 각각 갖는다."""
    seats = SeatCounts(economy=3, business=1, first=0)
    assert seats.economy == 3
    assert seats.business == 1
    assert seats.first == 0


def test_flight_option_nests_seat_counts():
    """FlightOption은 편명/시간과 SeatCounts를 함께 가진다."""
    flight = FlightOption(
        flight_no="KE001",
        dep_time="09:00",
        arr_time="12:00",
        seats=SeatCounts(economy=2, business=0, first=0),
    )
    assert flight.flight_no == "KE001"
    assert flight.seats.economy == 2


def test_calendar_day_groups_flights_by_date():
    """CalendarDay는 날짜 하나에 여러 FlightOption을 묶는다."""
    day = CalendarDay(
        date="2026-09-10",
        flights=[
            FlightOption(
                flight_no="KE001",
                dep_time="09:00",
                arr_time="12:00",
                seats=SeatCounts(economy=1, business=0, first=0),
            )
        ],
    )
    assert day.date == "2026-09-10"
    assert len(day.flights) == 1


def test_route_option_has_dest_code_and_name():
    """RouteOption은 목적지 공항코드와 표시용 이름을 가진다."""
    route = RouteOption(dest="NRT", dest_name="도쿄(나리타)")
    assert route.dest == "NRT"
    assert route.dest_name == "도쿄(나리타)"


def test_calendar_request_requires_dep_dest_month():
    """CalendarRequest는 출발지/목적지/월을 필수로 받는다."""
    req = CalendarRequest(dep="ICN", dest="NRT", month="2026-09")
    assert req.dep == "ICN"
    assert req.month == "2026-09"
