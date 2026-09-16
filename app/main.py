import time

from fastapi import FastAPI
from pydantic import BaseModel

from app.schemas.intent import UserIntent
from app.services.api_router import APIRouterService
from app.services.place_merger import PlaceMerger
from app.services.recommendation import RecommendationService

app = FastAPI(title="Busan Mate Prototype", version="0.1.0")

api_router_service = APIRouterService()
place_merger = PlaceMerger()
recommendation_service = RecommendationService()


class RecommendRequest(BaseModel):
    intent: UserIntent
    limit: int = 5


@app.get("/")
async def root():
    return {
        "service": "Busan Mate Prototype",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/recommend")
async def recommend(request: RecommendRequest):
    started = time.perf_counter()
    first_request = request.intent.requests[0]

    places, provider_timings = await api_router_service.search(
        query=first_request.query,
        location=request.intent.location,
    )

    merge_started = time.perf_counter()
    merged = place_merger.merge(places)
    merge_ms = (time.perf_counter() - merge_started) * 1000

    ranking_started = time.perf_counter()
    ranked = recommendation_service.rank(
        intent=request.intent,
        places=merged,
        limit=request.limit,
    )
    ranking_ms = (time.perf_counter() - ranking_started) * 1000

    total_ms = (time.perf_counter() - started) * 1000

    return {
        "places": ranked,
        "timing_ms": {
            **provider_timings,
            "merge_ms": round(merge_ms, 2),
            "ranking_ms": round(ranking_ms, 2),
            "total_ms": round(total_ms, 2),
        },
    }
