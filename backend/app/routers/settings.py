"""대한항공 로그인 자격증명 설정 라우터."""
from fastapi import APIRouter

from app.models.schemas import SettingsRequest, SettingsStatus
from app.services.credentials_store import get_credentials, save_credentials

router = APIRouter()


@router.get("/api/settings", response_model=SettingsStatus)
def get_settings() -> SettingsStatus:
    """자격증명 설정 여부를 반환한다. 비밀번호는 절대 내려주지 않는다."""
    credentials = get_credentials()
    if credentials is None:
        return SettingsStatus(configured=False)
    koreanair_id, _ = credentials
    return SettingsStatus(configured=True, koreanair_id=koreanair_id)


@router.post("/api/settings", response_model=SettingsStatus)
def update_settings(body: SettingsRequest) -> SettingsStatus:
    """자격증명을 저장한다."""
    save_credentials(body.koreanair_id, body.koreanair_pw)
    return SettingsStatus(configured=True, koreanair_id=body.koreanair_id)
