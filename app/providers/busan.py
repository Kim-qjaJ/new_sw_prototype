from app.config import settings
from app.providers.base import PlaceProvider
from app.schemas.place import Place


class BusanProvider(PlaceProvider):
    name = "busan"

    async def search(self, query: str, location: str | None = None) -> list[Place]:
        if not settings.busan_api_key:
            return []

        # TODO: Connect selected Busan public/culture datasets.
        return []
