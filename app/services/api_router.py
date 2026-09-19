import asyncio
import time

from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.providers.busan import BusanProvider
from app.providers.kakao import KakaoProvider
from app.providers.mock import MockProvider
from app.providers.naver import NaverProvider
from app.providers.tour import TourProvider
from app.schemas.api import ProviderStatus
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


BUSAN_EXHIBIT_KEYWORDS = (
    "전시공간",
    "전시장",
    "갤러리",
    "미술관",
    "문화공간",
    "문화시설",
    "문화회관",
    "문화센터",
    "공연장",
    "극장",
    "예술회관",
    "대관",
)


class APIRouterService:
    def __init__(self) -> None:
        self.providers: list[PlaceProvider] = [
            KakaoProvider(),
            NaverProvider(),
            TourProvider(),
            BusanProvider(),
        ]
        if settings.use_mock_places:
            self.providers.insert(0, MockProvider())

    def select_providers(self, request: PlaceRequest) -> list[PlaceProvider]:
        selected: list[PlaceProvider] = []
        search_text = " ".join(
            value
            for value in (request.query, request.subcategory)
            if value
        ).lower()

        for provider in self.providers:
            if provider.name == "busan":
                # 현재 부산 Provider에는 '전시공간 목록 서비스'만 실제 연결되어 있다.
                # 관련 없는 음식점/카페 검색에 전시공간 데이터가 섞이지 않도록 제한한다.
                if not any(keyword in search_text for keyword in BUSAN_EXHIBIT_KEYWORDS):
                    continue
            selected.append(provider)

        return selected

    async def search(
        self, request: PlaceRequest, location: str | None
    ) -> tuple[list[Place], dict[str, ProviderStatus]]:
        async def timed_search(provider: PlaceProvider):
            started = time.perf_counter()

            def elapsed() -> float:
                return round((time.perf_counter() - started) * 1000, 2)

            try:
                result = await asyncio.wait_for(
                    provider.search(request=request, location=location),
                    timeout=settings.provider_timeout_seconds,
                )
                return provider.name, result, ProviderStatus(
                    status="ok", count=len(result), elapsed_ms=elapsed()
                )
            except ProviderNotConfigured as exc:
                return provider.name, [], ProviderStatus(
                    status="not_configured", elapsed_ms=elapsed(), detail=str(exc)
                )
            except asyncio.TimeoutError:
                return provider.name, [], ProviderStatus(
                    status="timeout",
                    elapsed_ms=elapsed(),
                    detail=f"{settings.provider_timeout_seconds}초 안에 응답하지 않았습니다.",
                )
            except Exception as exc:  # noqa: BLE001 - 한 Provider 오류가 전체 요청을 막지 않게 한다.
                return provider.name, [], ProviderStatus(
                    status="error", elapsed_ms=elapsed(), detail=f"{type(exc).__name__}: {exc}"
                )

        results = await asyncio.gather(
            *(timed_search(provider) for provider in self.select_providers(request))
        )

        places: list[Place] = []
        statuses: dict[str, ProviderStatus] = {}
        for provider_name, provider_places, status in results:
            places.extend(provider_places)
            statuses[provider_name] = status

        return places, statuses
