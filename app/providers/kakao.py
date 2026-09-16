from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class KakaoProvider(PlaceProvider):
    name = "kakao"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.kakao_rest_api_key:
            raise ProviderNotConfigured("KAKAO_REST_API_KEY가 설정되지 않았습니다.")

        # TODO: Connect Kakao Local keyword search API.
        # Keep HTTP/API-specific response parsing inside this provider.
        return []
