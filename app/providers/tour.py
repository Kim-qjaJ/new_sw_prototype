from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class TourProvider(PlaceProvider):
    name = "tour"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.public_data_service_key:
            raise ProviderNotConfigured("PUBLIC_DATA_API_KEY가 설정되지 않았습니다.")
        if not settings.tour_api_url:
            raise ProviderNotConfigured(
                "공공데이터포털 인증키는 설정됐지만 TOUR_API_URL이 아직 연결되지 않았습니다."
            )

        # TourAPI 역시 서비스별 요청 URL/응답 필드를 확인한 뒤 Place로 매핑한다.
        return []
