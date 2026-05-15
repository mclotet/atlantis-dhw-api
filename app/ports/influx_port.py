from abc import ABC, abstractmethod

from app.domain.models import DhwStatus


class IDhwInfluxPort(ABC):
    @abstractmethod
    async def get_dhw_status(self) -> DhwStatus: ...
