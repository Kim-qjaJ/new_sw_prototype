from pathlib import Path
from urllib.parse import unquote

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    # 실행 위치와 상관없이 프로젝트 루트의 .env를 읽는다.
    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma4:e4b"
    ollama_timeout_seconds: float = 60.0
    ollama_keep_alive: str = "30m"
    ollama_structured_output: bool = True

    use_mock_places: bool = True
    provider_timeout_seconds: float = 5.0

    # 지도/장소 검색 API
    kakao_rest_api_key: str | None = None
    naver_client_id: str | None = None
    naver_client_secret: str | None = None

    # 공공데이터포털은 일반 인증키 1개를 공통으로 사용한다.
    public_data_api_key: str | None = None

    # 이전 설정과의 호환용. 비어 있으면 PUBLIC_DATA_API_KEY를 사용한다.
    busan_api_key: str | None = None
    tour_api_key: str | None = None
    kma_api_key: str | None = None

    # 실제 활용 신청한 공공데이터 API의 요청 URL.
    # API마다 URL/응답 필드가 달라서 링크를 확인한 뒤 연결한다.
    busan_api_url: str | None = None
    tour_api_url: str | None = None
    kma_api_url: str | None = None

    @staticmethod
    def _decode_service_key(value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip()
        return unquote(value) if value else None

    @property
    def public_data_service_key(self) -> str | None:
        """공공데이터포털 Encoding/Decoding 키 어느 쪽도 입력 가능하게 정규화한다."""
        return self._decode_service_key(
            self.public_data_api_key
            or self.busan_api_key
            or self.tour_api_key
            or self.kma_api_key
        )


settings = Settings()
