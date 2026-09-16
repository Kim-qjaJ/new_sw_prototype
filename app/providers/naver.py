from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class NaverProvider(PlaceProvider):
    name = "naver"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.naver_client_id or not settings.naver_client_secret:
            raise ProviderNotConfigured("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET가 설정되지 않았습니다.")

        # TODO: Connect Naver Local Search API (max 5 results per request).
        return []
