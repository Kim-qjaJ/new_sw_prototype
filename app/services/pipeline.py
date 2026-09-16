import asyncio
import time

from app.config import settings
from app.schemas.api import RecommendResponse, RequestResult
from app.schemas.intent import UserIntent
from app.services.api_router import APIRouterService
from app.services.place_merger import PlaceMerger
from app.services.recommendation import RecommendationService

UNSUPPORTED_NOTICE = (
    "장소 추천이나 검색 요청으로 이해하지 못했습니다. "
    "지역과 가고 싶은 장소를 함께 적어 주세요. 예: 서면에서 조용한 카페 추천해줘"
)


class RecommendationPipeline:
    """Intent 이후의 검색 → 통합 → 점수 계산 흐름을 담당한다."""

    def __init__(self) -> None:
        self.api_router = APIRouterService()
        self.merger = PlaceMerger()
        self.recommender = RecommendationService()

    async def run(self, intent: UserIntent, limit: int, message: str | None = None) -> RecommendResponse:
        started = time.perf_counter()

        if intent.intent == "unsupported":
            return RecommendResponse(
                message=message,
                intent=intent,
                results=[],
                notice=UNSUPPORTED_NOTICE,
                mock_data=settings.use_mock_places,
                timing_ms={"pipeline_ms": round((time.perf_counter() - started) * 1000, 2)},
            )

        # requests[]의 각 장소 요구를 병렬로 검색한다.
        search_started = time.perf_counter()
        searches = await asyncio.gather(
            *(self.api_router.search(request=req, location=intent.location) for req in intent.requests)
        )
        search_ms = (time.perf_counter() - search_started) * 1000

        results: list[RequestResult] = []
        merge_ms = 0.0
        ranking_ms = 0.0
        for req, (places, statuses) in zip(intent.requests, searches):
            step = time.perf_counter()
            merged = self.merger.merge(places)
            merge_ms += (time.perf_counter() - step) * 1000

            step = time.perf_counter()
            ranked = self.recommender.rank(intent=intent, request=req, places=merged, limit=limit)
            ranking_ms += (time.perf_counter() - step) * 1000

            results.append(RequestResult(request=req, places=ranked, providers=statuses))

        notice = None
        if all(not result.places for result in results):
            notice = "연결된 장소 데이터가 없어 추천 결과가 비어 있습니다. Provider 상태를 확인하세요."

        return RecommendResponse(
            message=message,
            intent=intent,
            results=results,
            notice=notice,
            mock_data=settings.use_mock_places,
            timing_ms={
                "search_ms": round(search_ms, 2),
                "merge_ms": round(merge_ms, 2),
                "ranking_ms": round(ranking_ms, 2),
                "pipeline_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
