from abc import ABC, abstractmethod


class AbstractBackend(ABC):

    @abstractmethod
    def write_flow(self, text: str, project_name: str, *args, **kwargs):
        pass

    @abstractmethod
    async def async_write_flow(self, text: str, project_name: str, *args, **kwargs):
        pass
