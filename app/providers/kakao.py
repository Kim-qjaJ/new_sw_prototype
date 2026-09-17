import httpx

from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class KakaoProvider(PlaceProvider):
    name = "kakao"
    SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.kakao_rest_api_key:
            raise ProviderNotConfigured("KAKAO_REST_API_KEY가 설정되지 않았습니다.")

        query = f"{location} {request.query}".strip() if location else request.query
        headers = {"Authorization": f"KakaoAK {settings.kakao_rest_api_key.strip()}"}
        params = {"query": query, "size": 15}

        async with httpx.AsyncClient(timeout=settings.provider_timeout_seconds) as client:
            response = await client.get(self.SEARCH_URL, headers=headers, params=params)
            response.raise_for_status()
            documents = response.json().get("documents", [])

        places: list[Place] = []
        for item in documents:
            distance_text = str(item.get("distance") or "").strip()
            distance_m = float(distance_text) if distance_text else None

            places.append(
                Place(
                    id=str(item.get("id") or "") or None,
                    name=item.get("place_name") or request.query,
                    category=request.category,
                    subcategory=request.subcategory,
                    address=item.get("road_address_name") or item.get("address_name"),
                    latitude=float(item["y"]) if item.get("y") else None,
                    longitude=float(item["x"]) if item.get("x") else None,
                    distance_m=distance_m,
                    indoor=None,
                    sources=[self.name],
                    source_ids={self.name: str(item.get("id") or "")},
                )
            )

        return places
