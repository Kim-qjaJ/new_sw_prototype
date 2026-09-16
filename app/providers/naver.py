from app.config import settings
from app.providers.base import PlaceProvider
from app.schemas.place import Place


class NaverProvider(PlaceProvider):
    name = "naver"

    async def search(self, query: str, location: str | None = None) -> list[Place]:
        if not settings.naver_client_id or not settings.naver_client_secret:
            return []

        # TODO: Connect Naver Local Search API.
        # Provider-specific popularity/search ordering can be normalized here.
        return []
