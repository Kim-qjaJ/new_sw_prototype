import hashlib
import random

from app.providers.base import PlaceProvider
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place

# 실제 API 연결 전 GUI와 추천 점수 흐름을 확인하기 위한 가짜 데이터.
# 이름에 [샘플]을 붙여 실제 장소로 오해하지 않도록 한다.
_SUFFIXES = ["본점", "역점", "2호점", "골목점", "타워점", "시장점", "해변점", "광장점"]


class MockProvider(PlaceProvider):
    name = "mock"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        area = location or "부산"
        seed_text = f"{area}|{request.query}|{request.category}"
        rng = random.Random(int(hashlib.sha256(seed_text.encode()).hexdigest(), 16))

        places: list[Place] = []
        for index in range(8):
            # 일부는 쿼리를 이름에 포함하지 않아 relevance 점수 차이가 생기도록 한다.
            label = request.query if index % 3 != 2 else "동네 공간"
            sources = ["mock"] if rng.random() < 0.6 else ["mock", "mock_cross"]
            places.append(
                Place(
                    id=f"mock-{hashlib.md5(f'{seed_text}|{index}'.encode()).hexdigest()[:10]}",
                    name=f"[샘플] {area} {label} {_SUFFIXES[index]}",
                    category=request.category,
                    subcategory=request.subcategory,
                    address=f"{area} 샘플로 {rng.randint(1, 200)}",
                    distance_m=float(rng.choice([180, 420, 760, 1200, 1900, 2600, 4100, 5200])),
                    indoor=rng.choice([True, False, None]),
                    sources=sources,
                    source_ids={source: f"{source}-{index}" for source in sources},
                    busan_verified=rng.random() < 0.3,
                )
            )
        return places
