"""KoreanAirClient 세션 캐시 TTL 로직 테스트 (Playwright 없이)."""
import time

from app.clients.korean_air_client import KoreanAirClient


def test_session_not_expired_right_after_login():
    """로그인 직후에는 세션이 만료되지 않은 것으로 판단한다."""
    client = KoreanAirClient()
    client._session_expires_at = time.time() + 900
    assert client._is_session_valid() is True


def test_session_expired_after_ttl():
    """TTL이 지난 세션은 만료로 판단한다."""
    client = KoreanAirClient()
    client._session_expires_at = time.time() - 1
    assert client._is_session_valid() is False


def test_session_invalid_before_first_login():
    """한 번도 로그인 안 한 상태는 세션이 없는 것으로 판단한다."""
    client = KoreanAirClient()
    assert client._is_session_valid() is False
