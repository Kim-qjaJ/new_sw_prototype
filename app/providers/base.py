from abc import ABC, abstractmethod

from app.schemas.place import Place


class PlaceProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, location: str | None = None) -> list[Place]:
        """Search provider and return normalized Place objects."""
        raise NotImplementedError
