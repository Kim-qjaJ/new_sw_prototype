from app.config import settings
from app.providers.base import ProviderNotConfigured


class WeatherProvider:
    name = "weather"

    async def get_weather(
        self,
        location_name: str | None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        if not settings.public_data_service_key:
            raise ProviderNotConfigured("PUBLIC_DATA_API_KEY가 설정되지 않았습니다.")
        if not settings.kma_api_url:
            raise ProviderNotConfigured(
                "공공데이터포털 인증키는 설정됐지만 KMA_API_URL이 아직 연결되지 않았습니다."
            )

        # 사용할 기상청 API 링크를 확인한 뒤 요청 파라미터/응답 필드를 연결한다.
        return {}
