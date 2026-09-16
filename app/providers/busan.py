from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class BusanProvider(PlaceProvider):
    name = "busan"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.busan_api_key:
            raise ProviderNotConfigured("BUSAN_API_KEY가 설정되지 않았습니다.")

        # TODO: Connect selected Busan public/culture datasets.
        return []
