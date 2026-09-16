from typing import Literal

from pydantic import BaseModel, Field, model_validator

IntentType = Literal[
    "recommend_place",
    "search_place",
    "get_event",
    "get_route",
    "unsupported",
]

PlaceCategory = Literal[
    "restaurant",
    "cafe",
    "tourism",
    "culture",
    "activity",
    "public_facility",
    "education",
    "other",
]


class PlaceRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    category: PlaceCategory | None = None
    subcategory: str | None = None
    indoor: bool | None = None


class UserIntent(BaseModel):
    intent: IntentType
    location: str | None = None
    requests: list[PlaceRequest] = Field(default_factory=list)
    companion: Literal["alone", "friend", "family"] | None = None

    @model_validator(mode="after")
    def check_requests(self) -> "UserIntent":
        # 장소와 무관한 문장(인사 등)만 requests 없이 허용한다.
        if self.intent != "unsupported" and not self.requests:
            raise ValueError("requests must contain at least one item")
        return self
