from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class TourProvider(PlaceProvider):
    name = "tour"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.tour_api_key:
            raise ProviderNotConfigured("TOUR_API_KEY가 설정되지 않았습니다.")

        # TODO: Connect Korea Tourism Organization data API (KorService2).
        return []
