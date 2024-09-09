from abc import ABC, abstractmethod
from typing import Dict


class PostProcessor(ABC):
    @abstractmethod
    def process(self, transcription: Dict) -> Dict:
        pass
