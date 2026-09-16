from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma4:e4b"

    kakao_rest_api_key: str | None = None
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    busan_api_key: str | None = None
    tour_api_key: str | None = None
    kma_api_key: str | None = None


settings = Settings()
