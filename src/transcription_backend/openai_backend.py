import numpy as np
import os
import io
from typing import Dict, Any

from transcription_backend.transcription_backend_base import TranscriptionBackendBase
from config_manager import ConfigManager


class OpenAIBackend(TranscriptionBackendBase):
    def __init__(self):
        self.OpenAI = None
        self.config = None
        self.client = None
        self._initialized = False

    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, options: Dict[str, Any]):
        try:
            from openai import OpenAI
            import soundfile as sf
        except ImportError:
            ConfigManager.log_print("Failed to import OpenAI or soundfile. Make sure they're installed.")
            return

        self.OpenAI = OpenAI
        self.config = options
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        base_url = self.config.get('base_url') or 'https://api.openai.com/v1'

        if not api_key:
            ConfigManager.log_print(f"OpenAI API key not found. Please set it in the configuration or as an environment variable.")
            return

        self.client = self.OpenAI(api_key=api_key, base_url=base_url)
        ConfigManager.log_print("OpenAI client initialized successfully.")
        self._initialized = True

    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.client:
            return {'raw_text': '', 'language': language, 'error': "OpenAI client not initialized"}

        try:
            import soundfile as sf
        except ImportError:
            return {'raw_text': '', 'language': language, 'error': "soundfile library not found"}

        # Prepare audio data
        try:
            audio_data = self._prepare_audio_data(audio_data, sample_rate, channels)
        except Exception as e:
            return {'raw_text': '', 'language': language, 'error': f"Error preparing audio data: {str(e)}"}

        # Convert numpy array to WAV file
        byte_io = io.BytesIO()
        sf.write(byte_io, audio_data, 16000, format='wav')
        byte_io.seek(0)

        try:
            response = self.client.audio.transcriptions.create(
                model=self.config.get('model', 'whisper-1'),
                file=('audio.wav', byte_io, 'audio/wav'),
                language=language if language != 'auto' else None,
                prompt=self.config.get('initial_prompt'),
                temperature=self.config.get('temperature', 0.0),
            )
            return {
                'raw_text': response.text,
                'language': language,  # OpenAI doesn't return detected language
                'error': '',
            }
        except Exception as e:
            return {
                'raw_text': '',
                'language': language,
                'error': f"OpenAI transcription failed: {str(e)}",
            }

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

    def cleanup(self):
        self.client = None
        self._initialized = False
