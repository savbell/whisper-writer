import numpy as np
from typing import Dict, Any
import json

from transcription_backend.transcription_backend_base import TranscriptionBackendBase
from config_manager import ConfigManager


class VoskBackend(TranscriptionBackendBase):
    def __init__(self):
        self.vosk = None
        self.model = None
        self.recognizer = None
        self.config = None
        self._initialized = False

    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, options: Dict[str, Any]):
        self.config = options
        try:
            import vosk
            self.vosk = vosk
        except ImportError:
            raise RuntimeError("Failed to import vosk. Make sure it's installed.")

        try:
            model_path = self.config.get('model_path', "model")
            self.model = self.vosk.Model(model_path)
            sample_rate = self.config.get('sample_rate', 16000)
            self.recognizer = self.vosk.KaldiRecognizer(self.model, sample_rate)
            ConfigManager.log_print("Vosk model initialized successfully.")
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vosk model: {e}")

    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.recognizer:
            return {'raw_text': '', 'language': 'en', 'error': 'Recognizer not initialized'}

        # Ensure audio_data is in the correct format (16-bit PCM)
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)

        try:
            self.recognizer.AcceptWaveform(audio_data.tobytes())
            result = json.loads(self.recognizer.FinalResult())

            return {
                'raw_text': result.get('text', ''),
                'language': 'en',
                'error': '',
            }
        except Exception as e:
            return {
                'raw_text': '',
                'language': 'en',
                'error': f'Unexpected error during transcription: {e}'
            }

    def transcribe_stream(self, audio_chunk: np.ndarray, sample_rate: int = 16000,
                          channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.recognizer:
            return {'raw_text': '', 'language': 'en', 'error': 'Recognizer not initialized'}

        # Ensure audio_chunk is in the correct format (16-bit PCM)
        if audio_chunk.dtype != np.int16:
            audio_chunk = (audio_chunk * 32767).astype(np.int16)

        try:
            is_utterance_end = self.recognizer.AcceptWaveform(audio_chunk.tobytes())
            if is_utterance_end:
                result = json.loads(self.recognizer.Result())
            else:
                result = json.loads(self.recognizer.PartialResult())

            return {
                'raw_text': (result.get('partial', '')
                             if not is_utterance_end
                             else result.get('text', '')),
                'language': 'en',
                'error': '',
                'is_utterance_end': is_utterance_end
            }
        except Exception as e:
            return {
                'raw_text': '',
                'language': 'en',
                'error': f'Unexpected error during streaming transcription: {e}',
                'is_utterance_end': True
            }

    def finalize_stream(self) -> Dict[str, Any]:
        if not self.recognizer:
            return {'raw_text': '', 'language': 'en', 'error': 'Recognizer not initialized'}

        try:
            final_result = json.loads(self.recognizer.FinalResult())
            return {
                'raw_text': final_result.get('text', ''),
                'language': 'en',
                'error': '',
                'is_utterance_end': True
            }
        except Exception as e:
            return {
                'raw_text': '',
                'language': 'en',
                'error': f'Unexpected error during stream finalization: {e}',
                'is_utterance_end': True
            }

    def get_preferred_streaming_chunk_size(self):
        return 4096

    def cleanup(self):
        self.recognizer = None
        self.model = None
        self.vosk = None
        self._initialized = False
