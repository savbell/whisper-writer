import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any


class TranscriptionBackendBase(ABC):
    @abstractmethod
    def initialize(self, options: Dict[str, Any]):
        pass

    @abstractmethod
    def transcribe_stream(self, audio_chunk: np.ndarray, sample_rate: int = 16000,
                          channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        pass

    @abstractmethod
    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        pass

    @abstractmethod
    def cleanup(self):
        pass
