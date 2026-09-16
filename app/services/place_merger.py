from app.schemas.place import Place


class PlaceMerger:
    def merge(self, places: list[Place]) -> list[Place]:
        """Prototype duplicate merger.

        v1 uses normalized name + address as a conservative key.
        TODO: Kakao/Naver 주소 표기 차이와 <b> 태그 때문에 실제 데이터에서는
        이름 유사도 + 좌표 거리 기반으로 바꿔야 한다.
        """
        merged: dict[tuple[str, str], Place] = {}

        for place in places:
            key = (
                place.name.strip().lower(),
                (place.address or "").strip().lower(),
            )
            existing = merged.get(key)
            if existing is None:
                merged[key] = place.model_copy(deep=True)
                continue

            existing.sources = sorted(set(existing.sources + place.sources))
            existing.source_ids.update(place.source_ids)
            existing.busan_verified = existing.busan_verified or place.busan_verified
            # 먼저 들어온 Provider에 없던 값은 다른 Provider 값으로 채운다.
            for field in ("category", "subcategory", "latitude", "longitude", "distance_m", "indoor"):
                if getattr(existing, field) is None and getattr(place, field) is not None:
                    setattr(existing, field, getattr(place, field))

        return list(merged.values())
