from app.config import settings
from app.providers.base import PlaceProvider
from app.schemas.place import Place


class TourProvider(PlaceProvider):
    name = "tour"

    async def search(self, query: str, location: str | None = None) -> list[Place]:
        if not settings.tour_api_key:
            return []

        # TODO: Connect Korea Tourism Organization tourism data API.
        return []
