from app.schemas.place import Place


class PlaceMerger:
    def merge(self, places: list[Place]) -> list[Place]:
        """Prototype duplicate merger.

        v1 uses normalized name + address as a conservative key.
        Later this can combine name similarity, address and coordinate distance.
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

        return list(merged.values())
