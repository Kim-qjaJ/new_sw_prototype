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


class APIRouterService:
    def __init__(self) -> None:
        self.providers: list[PlaceProvider] = [
            KakaoProvider(),
            NaverProvider(),
            BusanProvider(),
            TourProvider(),
        ]
        if settings.use_mock_places:
            self.providers.insert(0, MockProvider())

    def select_providers(self, request: PlaceRequest) -> list[PlaceProvider]:
        # TODO: category/intent에 따라 필요한 Provider만 고르도록 확장한다.
        return self.providers

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
