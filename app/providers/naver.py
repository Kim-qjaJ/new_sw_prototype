import html
import re

import httpx

from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_title(value: str) -> str:
    return html.unescape(_TAG_RE.sub("", value or "")).strip()


class NaverProvider(PlaceProvider):
    name = "naver"
    SEARCH_URL = "https://naverapihub.apigw.ntruss.com/search/v1/local"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.naver_client_id or not settings.naver_client_secret:
            raise ProviderNotConfigured("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET가 설정되지 않았습니다.")

        query = f"{location} {request.query}".strip() if location else request.query
        headers = {
            "X-NCP-APIGW-API-KEY-ID": settings.naver_client_id.strip(),
            "X-NCP-APIGW-API-KEY": settings.naver_client_secret.strip(),
        }
        params = {"query": query, "display": 5, "start": 1, "sort": "random"}

        async with httpx.AsyncClient(timeout=settings.provider_timeout_seconds) as client:
            response = await client.get(self.SEARCH_URL, headers=headers, params=params)
            response.raise_for_status()
            items = response.json().get("items", [])

        places: list[Place] = []
        for item in items:
            title = _clean_title(str(item.get("title") or request.query))
            source_id = f"{item.get('mapx', '')}:{item.get('mapy', '')}:{title}"

            # Naver Local Search의 mapx/mapy는 현재 단계에서는 원본 식별값으로만 사용한다.
            # 위/경도는 추후 지도/지오코딩 Provider에서 확정한다.
            places.append(
                Place(
                    id=source_id,
                    name=title,
                    category=request.category,
                    subcategory=request.subcategory,
                    address=item.get("roadAddress") or item.get("address"),
                    latitude=None,
                    longitude=None,
                    distance_m=None,
                    indoor=None,
                    sources=[self.name],
                    source_ids={self.name: source_id},
                )
            )

        return places
