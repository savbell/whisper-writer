import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class TranscriptionBackendBase(ABC):
    @abstractmethod
    def is_initialized(self) -> bool:
        pass

    @abstractmethod
    def initialize(self, options: Dict[str, Any]):
        pass

    @abstractmethod
    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        pass

    @abstractmethod
    def cleanup(self):
        pass

    def get_preferred_streaming_chunk_size(self) -> Optional[int]:
        return None

    def transcribe_stream(self, audio_chunk: np.ndarray, sample_rate: int = 16000,
                          channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        return {
            'raw_text': '',
            'language': 'en',
            'error': 'Streaming transcription is not supported by this backend.',
        }
