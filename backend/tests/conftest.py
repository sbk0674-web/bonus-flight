"""테스트 공통 설정."""
import os

# KoreanAirClient는 KOREANAIR_ID/KOREANAIR_PW 환경변수를 요구한다.
# 테스트에서는 실제 자격증명이 필요 없으므로(라우터는 의존성 오버라이드로 목 처리하거나
# 클라이언트 자체를 직접 생성해서 테스트) 더미 값을 기본값으로 채워준다.
os.environ.setdefault("KOREANAIR_ID", "test-id")
os.environ.setdefault("KOREANAIR_PW", "test-pw")
