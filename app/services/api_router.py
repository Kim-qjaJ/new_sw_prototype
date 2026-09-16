import asyncio
import time

from app.providers.busan import BusanProvider
from app.providers.kakao import KakaoProvider
from app.providers.naver import NaverProvider
from app.providers.tour import TourProvider
from app.schemas.place import Place


class APIRouterService:
    def __init__(self) -> None:
        self.providers = [
            KakaoProvider(),
            NaverProvider(),
            BusanProvider(),
            TourProvider(),
        ]

    async def search(self, query: str, location: str | None) -> tuple[list[Place], dict[str, float]]:
        async def timed_search(provider):
            started = time.perf_counter()
            try:
                result = await provider.search(query=query, location=location)
                return provider.name, result, (time.perf_counter() - started) * 1000
            except Exception:
                return provider.name, [], (time.perf_counter() - started) * 1000

        results = await asyncio.gather(
            *(timed_search(provider) for provider in self.providers)
        )

        places: list[Place] = []
        timings: dict[str, float] = {}
        for provider_name, provider_places, elapsed_ms in results:
            places.extend(provider_places)
            timings[f"{provider_name}_ms"] = round(elapsed_ms, 2)

        return places, timings
