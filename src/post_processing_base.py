from abc import ABC, abstractmethod

class PostProcessor(ABC):
    @abstractmethod
    def process(self, text: str) -> str:
        pass
