import math
import xml.etree.ElementTree as ET

import httpx

from app.config import settings
from app.providers.base import PlaceProvider, ProviderNotConfigured
from app.schemas.intent import PlaceRequest
from app.schemas.place import Place


class BusanProvider(PlaceProvider):
    """부산광역시 공공데이터 장소 Provider.

    현재는 공공데이터포털의 '부산광역시_전시공간 목록 서비스'를 연결한다.
    """

    name = "busan"
    EXHIBIT_PLACE_URL = (
        "https://apis.data.go.kr/6260000/"
        "BusanCultureExhibitPlaceService/getBusanCultureExhibitPlace"
    )
    KAKAO_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
    MAX_RESULTS = 30
    NEARBY_RADIUS_M = 10_000

    async def search(self, request: PlaceRequest, location: str | None = None) -> list[Place]:
        if not settings.public_data_service_key:
            raise ProviderNotConfigured("PUBLIC_DATA_API_KEY가 설정되지 않았습니다.")

        async with httpx.AsyncClient(timeout=settings.provider_timeout_seconds) as client:
            response = await client.get(
                self.EXHIBIT_PLACE_URL,
                params={
                    "ServiceKey": settings.public_data_service_key,
                    "pageNo": 1,
                    # 현재 데이터가 500여 건이므로 한 번에 받아 로컬에서 위치순으로 정렬한다.
                    "numOfRows": 999,
                },
            )
            response.raise_for_status()
            items = self._parse_items(response)

            anchor = await self._resolve_anchor(client, location)

        places: list[Place] = []
        for item in items:
            name = str(item.get("placeNm") or "").strip()
            if not name:
                continue

            latitude = self._to_float(item.get("lttd"))
            longitude = self._to_float(item.get("lngt"))
            distance_m = None
            if anchor and latitude is not None and longitude is not None:
                distance_m = self._distance_m(anchor[0], anchor[1], latitude, longitude)

            source_id = str(item.get("placeId") or name)
            places.append(
                Place(
                    id=source_id,
                    name=name,
                    category=request.category or "culture",
                    subcategory=request.subcategory,
                    address=str(item.get("addr") or "").strip() or None,
                    latitude=latitude,
                    longitude=longitude,
                    distance_m=distance_m,
                    indoor=None,
                    sources=[self.name],
                    source_ids={self.name: source_id},
                    busan_verified=True,
                )
            )

        if anchor:
            # '서면 근처'처럼 기준 위치가 있으면 실제 좌표 거리로 가까운 시설부터 사용한다.
            nearby = [
                place
                for place in places
                if place.distance_m is not None and place.distance_m <= self.NEARBY_RADIUS_M
            ]
            if nearby:
                places = nearby
            places.sort(
                key=lambda place: (
                    place.distance_m is None,
                    place.distance_m if place.distance_m is not None else float("inf"),
                    place.name,
                )
            )
        else:
            places = self._filter_by_district(places, location)
            places.sort(key=lambda place: place.name)

        return places[: self.MAX_RESULTS]

    async def _resolve_anchor(
        self,
        client: httpx.AsyncClient,
        location: str | None,
    ) -> tuple[float, float] | None:
        """Kakao Local로 사용자 지역 표현을 부산 내 기준 좌표로 바꾼다.

        부산 공공데이터 자체에는 '서면' 같은 생활권 검색 기능이 없으므로
        Kakao 키가 있을 때만 보조적으로 기준 좌표를 얻는다.
        """

        if not location or not settings.kakao_rest_api_key:
            return None

        query = location.strip()
        if "부산" not in query:
            query = f"부산 {query}"

        try:
            response = await client.get(
                self.KAKAO_SEARCH_URL,
                headers={"Authorization": f"KakaoAK {settings.kakao_rest_api_key.strip()}"},
                params={"query": query, "size": 1},
            )
            response.raise_for_status()
            documents = response.json().get("documents", [])
            if not documents:
                return None

            first = documents[0]
            latitude = self._to_float(first.get("y"))
            longitude = self._to_float(first.get("x"))
            if latitude is None or longitude is None:
                return None
            return latitude, longitude
        except (httpx.HTTPError, ValueError, TypeError):
            # 부산 공공데이터 호출 자체는 계속 사용하고, 위치 필터만 생략한다.
            return None

    @staticmethod
    def _parse_items(response: httpx.Response) -> list[dict]:
        """JSON/XML 어느 형식으로 응답해도 전시공간 항목을 추출한다."""

        try:
            payload = response.json()
        except ValueError:
            return BusanProvider._parse_xml_items(response.text)

        result_code = BusanProvider._find_json_value(payload, "resultCode")
        result_message = BusanProvider._find_json_value(payload, "resultMsg")
        if result_code not in (None, "", "00"):
            raise RuntimeError(f"Busan OpenAPI error {result_code}: {result_message or 'unknown'}")

        items: list[dict] = []

        def walk(node):
            if isinstance(node, dict):
                if "placeNm" in node or "placeId" in node:
                    items.append(node)
                    return
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)
        return items

    @staticmethod
    def _parse_xml_items(text: str) -> list[dict]:
        root = ET.fromstring(text)

        def local_name(tag: str) -> str:
            return tag.rsplit("}", 1)[-1]

        result_code = None
        result_message = None
        items: list[dict] = []

        for element in root.iter():
            name = local_name(element.tag)
            if name == "resultCode" and result_code is None:
                result_code = (element.text or "").strip()
            elif name == "resultMsg" and result_message is None:
                result_message = (element.text or "").strip()

            children = list(element)
            child_names = {local_name(child.tag) for child in children}
            if "placeNm" in child_names or "placeId" in child_names:
                item = {
                    local_name(child.tag): (child.text or "").strip()
                    for child in children
                }
                items.append(item)

        if result_code not in (None, "", "00"):
            raise RuntimeError(f"Busan OpenAPI error {result_code}: {result_message or 'unknown'}")

        return items

    @staticmethod
    def _find_json_value(node, key: str):
        if isinstance(node, dict):
            if key in node:
                return str(node[key]).strip() if node[key] is not None else None
            for value in node.values():
                found = BusanProvider._find_json_value(value, key)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for value in node:
                found = BusanProvider._find_json_value(value, key)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _filter_by_district(places: list[Place], location: str | None) -> list[Place]:
        if not location:
            return places

        districts = (
            "중구",
            "서구",
            "동구",
            "영도구",
            "부산진구",
            "동래구",
            "남구",
            "북구",
            "해운대구",
            "사하구",
            "금정구",
            "강서구",
            "연제구",
            "수영구",
            "사상구",
            "기장군",
        )
        district = next((name for name in districts if name in location), None)
        if not district:
            return places

        filtered = [place for place in places if district in (place.address or "")]
        return filtered or places

    @staticmethod
    def _to_float(value) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6_371_000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        return round(radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)
