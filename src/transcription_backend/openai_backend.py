import numpy as np
import os
import io
from typing import Dict, Any

from transcription_backend.transcription_backend_base import TranscriptionBackendBase
from config_manager import ConfigManager


class OpenAIBackend(TranscriptionBackendBase):
    def initialize(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("Failed to import OpenAI. Make sure it's installed.")

        self.OpenAI = OpenAI
        self.config = ConfigManager.get_config_section('model_options.backends.openai')
        self.client = self.OpenAI(
            api_key=self.config.get('api_key') or os.getenv('OPENAI_API_KEY'),
            base_url=self.config.get('base_url') or 'https://api.openai.com/v1'
        )

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000, channels: int = 1,
                   language: str = 'auto') -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Check and convert audio data if needed
        audio_data = self._prepare_audio_data(audio_data, sample_rate, channels)

        # Convert numpy array to bytes
        byte_io = io.BytesIO(audio_data.tobytes())

        try:
            response = self.client.audio.transcriptions.create(
                model=self.config.get('model'),
                file=("audio.wav", byte_io, "audio/wav"),
                language=language if language != 'auto' else None,
                prompt=self.config.get('initial_prompt'),
                temperature=self.config.get('temperature', 0.0),
            )
            return {
                'raw_text': response.text,
                'language': language,  # OpenAI doesn't return detected language,
                                       # so we use the input language
            }
        except Exception as e:
            raise RuntimeError(f"OpenAI transcription failed: {str(e)}")

    def _prepare_audio_data(self, audio_data: np.ndarray, sample_rate: int,
                            channels: int) -> np.ndarray:
        # OpenAI expects 16kHz mono audio
        if sample_rate != 16000 or channels != 1:
            try:
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
                if channels > 1:
                    audio_data = librosa.to_mono(audio_data.T)
            except ImportError:
                raise RuntimeError("librosa is required for audio resampling. Please install it.")

        # Ensure the audio data is in float32 format and normalized
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        if audio_data.max() > 1.0 or audio_data.min() < -1.0:
            audio_data = np.clip(audio_data, -1.0, 1.0)

        return audio_data
    #
    # def start_streaming(self, audio_source: Any, callback: Callable[[Dict[str, Any]], None],
    #                     sample_rate: int = 16000, channels: int = 1, language: str = 'auto'):
    #     raise NotImplementedError("Streaming is not currently supported for OpenAI backend")
    #
    # def stop_streaming(self):
    #     raise NotImplementedError("Streaming is not currently supported for OpenAI backend")

    def cleanup(self):
        self.client = None
