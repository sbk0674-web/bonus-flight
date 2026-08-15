"""대한항공 로그인 자격증명 로컬 저장소.

설정 화면에서 입력한 아이디/비밀번호를 로컬 파일(credentials.json)에 저장한다.
파일이 없으면 환경변수(KOREANAIR_ID, KOREANAIR_PW)를 대신 사용한다.
"""
import json
import os
from pathlib import Path

CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "credentials.json"


def get_credentials() -> tuple[str, str] | None:
    """저장된 자격증명을 반환한다. 파일 우선, 없으면 환경변수, 둘 다 없으면 None.

    Returns:
        (koreanair_id, koreanair_pw) 튜플, 설정 안 됐으면 None.
    """
    if CREDENTIALS_PATH.exists():
        data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
        koreanair_id = data.get("koreanair_id")
        koreanair_pw = data.get("koreanair_pw")
        if koreanair_id and koreanair_pw:
            return koreanair_id, koreanair_pw

    env_id = os.environ.get("KOREANAIR_ID")
    env_pw = os.environ.get("KOREANAIR_PW")
    if env_id and env_pw:
        return env_id, env_pw

    return None


def save_credentials(koreanair_id: str, koreanair_pw: str) -> None:
    """자격증명을 로컬 파일에 저장한다.

    Args:
        koreanair_id: 대한항공 SKYPASS 아이디.
        koreanair_pw: 대한항공 SKYPASS 비밀번호.
    """
    CREDENTIALS_PATH.write_text(
        json.dumps({"koreanair_id": koreanair_id, "koreanair_pw": koreanair_pw}, ensure_ascii=False),
        encoding="utf-8",
    )
