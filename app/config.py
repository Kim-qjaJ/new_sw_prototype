from pathlib import Path

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

    kakao_rest_api_key: str | None = None
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    busan_api_key: str | None = None
    tour_api_key: str | None = None
    kma_api_key: str | None = None


settings = Settings()
