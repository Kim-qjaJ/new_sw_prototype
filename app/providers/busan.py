from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class BusanProvider(PlaceProvider):
    name = "busan"

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.public_data_service_key:
            raise ProviderNotConfigured("PUBLIC_DATA_API_KEY가 설정되지 않았습니다.")
        if not settings.busan_api_url:
            raise ProviderNotConfigured(
                "공공데이터포털 인증키는 설정됐지만 BUSAN_API_URL이 아직 연결되지 않았습니다."
            )

        # 공공데이터 API마다 요청 파라미터와 응답 필드가 달라서
        # 실제 사용할 부산 API 링크를 확인한 뒤 여기서 Place로 매핑한다.
        return []
