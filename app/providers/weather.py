from app.config import settings


class WeatherProvider:
    name = "weather"

    async def get_weather(self, location: str) -> dict:
        if not settings.kma_api_key:
            return {}

        # TODO: Connect KMA forecast/current-weather data.
        return {}
