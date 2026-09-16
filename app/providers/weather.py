from app.config import settings
from app.providers.base import ProviderNotConfigured


class WeatherProvider:
    name = "weather"

    async def get_weather(self, location: str) -> dict:
        if not settings.kma_api_key:
            raise ProviderNotConfigured("KMA_API_KEY가 설정되지 않았습니다.")

        # TODO: Connect KMA forecast data. 단기예보는 위경도가 아닌 격자(nx, ny) 좌표를 사용한다.
        return {}
