from app.config import settings
from app.providers.base import PlaceProvider
from app.schemas.place import Place


class KakaoProvider(PlaceProvider):
    name = "kakao"

    async def search(self, query: str, location: str | None = None) -> list[Place]:
        if not settings.kakao_rest_api_key:
            return []

        # TODO: Connect Kakao Local keyword search API.
        # Keep HTTP/API-specific response parsing inside this provider.
        return []
