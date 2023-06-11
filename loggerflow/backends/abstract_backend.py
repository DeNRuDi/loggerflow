from abc import ABC, abstractmethod


class AbstractBackend(ABC):

    @abstractmethod
    def write_flow(self, text: str, authors: list = None, project_name: str = None):
        pass
