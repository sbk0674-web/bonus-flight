"""KoreanAirClient 원시 응답 파서 테스트 (fixture 기반, 네트워크 없음)."""
import json
from pathlib import Path

from app.clients.korean_air_client import parse_calendar_response

FIXTURE = Path(__file__).parent / "fixtures" / "calendar_response_sample.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_parse_maps_seat_fields_to_seat_counts():
    """원시 응답의 economySeats/businessSeats/firstSeats를 SeatCounts로 매핑한다."""
    days = parse_calendar_response(_load_fixture())
    first_day = days[0]
    ke001 = next(f for f in first_day.flights if f.flight_no == "KE001")
    assert ke001.seats.economy == 3
    assert ke001.seats.business == 1
    assert ke001.seats.first == 0


def test_parse_excludes_flights_with_zero_seats_in_all_classes():
    """세 등급 모두 0석인 편(KE005)은 파싱 결과에서 제외된다."""
    days = parse_calendar_response(_load_fixture())
    first_day = days[0]
    flight_numbers = [f.flight_no for f in first_day.flights]
    assert "KE005" not in flight_numbers


def test_parse_excludes_dates_with_no_available_flights():
    """모든 편이 0석인 날짜(09-11) 자체가 결과에서 빠진다."""
    days = parse_calendar_response(_load_fixture())
    dates = [d.date for d in days]
    assert "2026-09-11" not in dates
    assert "2026-09-10" in dates
