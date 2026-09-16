from pydantic import BaseModel, Field


class Place(BaseModel):
    id: str
    name: str
    category: str | None = None
    subcategory: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_m: float | None = None
    indoor: bool | None = None

    sources: list[str] = Field(default_factory=list)
    source_ids: dict[str, str] = Field(default_factory=dict)

    is_available: bool | None = None
    busan_verified: bool = False
    popularity_signal: float | None = None

    score: float = 0.0
    score_breakdown: dict[str, float] = Field(default_factory=dict)
