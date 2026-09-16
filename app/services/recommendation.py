from app.schemas.intent import PlaceRequest, UserIntent
from app.schemas.place import Place

# GUI에서 막대 길이를 그릴 수 있도록 항목별 최대 점수를 함께 공개한다.
SCORE_MAX = {
    "relevance": 30.0,
    "distance": 25.0,
    "user_condition": 15.0,
    "weather": 10.0,
    "cross_provider": 10.0,
    "busan_data": 10.0,
}


class RecommendationService:
    """Explainable prototype scoring model.

    The weights are experimental and should be adjusted after API integration tests.
    """

    def rank(
        self,
        intent: UserIntent,
        request: PlaceRequest,
        places: list[Place],
        limit: int = 5,
    ) -> list[Place]:
        ranked: list[Place] = []

        for original in places:
            place = original.model_copy(deep=True)
            breakdown: dict[str, float] = {}

            # Search/category relevance: max 30
            relevance = 0.0
            if request.query.lower() in place.name.lower():
                relevance += 15.0
            if request.category and request.category == place.category:
                relevance += 15.0
            breakdown["relevance"] = min(relevance, SCORE_MAX["relevance"])

            # Distance: max 25 (simple prototype buckets)
            if place.distance_m is not None:
                if place.distance_m <= 500:
                    breakdown["distance"] = 25.0
                elif place.distance_m <= 1500:
                    breakdown["distance"] = 20.0
                elif place.distance_m <= 3000:
                    breakdown["distance"] = 12.0
                else:
                    breakdown["distance"] = 5.0
            else:
                breakdown["distance"] = 0.0

            # Explicit indoor condition: max 15
            if request.indoor is None:
                breakdown["user_condition"] = 7.5
            elif place.indoor == request.indoor:
                breakdown["user_condition"] = 15.0
            else:
                breakdown["user_condition"] = 0.0

            # Weather suitability is reserved until weather/place metadata is connected.
            breakdown["weather"] = 0.0

            # Cross-provider confirmation: max 10
            breakdown["cross_provider"] = 10.0 if len(set(place.sources)) >= 2 else 5.0

            # Busan-specific source confirmation: max 10
            breakdown["busan_data"] = 10.0 if place.busan_verified else 0.0

            place.score_breakdown = breakdown
            place.score = round(sum(breakdown.values()), 2)
            ranked.append(place)

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:limit]
