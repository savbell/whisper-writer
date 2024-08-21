import threading
import traceback
import os
import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
from enum import Enum

from utils import ConfigManager
from post_processing import post_process


class StreamingStatus(Enum):
    NOT_SUPPORTED = 0
    IDLE = 1
    STREAMING = 2
    ALREADY_RUNNING = 3
    FAILED_TO_START = 4

class TranscriptionBackend(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000, channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        pass

    @abstractmethod
    def start_streaming(self, audio_source: Any, callback: Callable[[Dict[str, Any]], None], sample_rate: int = 16000, channels: int = 1, language: str = 'auto'):
        pass

    @abstractmethod
    def stop_streaming(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass

class TranscriptionManager:
    def __init__(self):
        self.config = ConfigManager.get_config_section('model_options')
        self.backend = None
        self.streaming_thread = None
        self.streaming_status = None
        self._initialize_backend()

    def _initialize_backend(self):
        backend_name = self.config.get('backend')
        if backend_name == 'openai':
            self.backend = OpenAIBackend()
        elif backend_name == 'faster_whisper':
            self.backend = FasterWhisperBackend()
        else:
            raise ValueError(f"Unknown backend: {backend_name}")

        try:
            self.backend.initialize()
            self.streaming_status = self.backend.supports_streaming()
        except Exception as e:
            traceback.print_exc()
            print(f"Failed to initialize backend: {e}")
            self.backend = None

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000, channels: int = 1, language: str = 'auto') -> Optional[Dict[str, Any]]:
        if not self.backend:
            return None

        try:
            result = self.backend.transcribe(audio_data, sample_rate, channels, language)
            result['processed_text'] = post_process(result['raw_text'])
            return result
        except Exception as e:
            traceback.print_exc()
            print(f"Transcription failed: {e}")
            return None

    def start_streaming_transcription(self, audio_source: Any, callback: Callable[[Dict[str, Any]], None], sample_rate: int = 16000, channels: int = 1, language: str = 'auto') -> StreamingStatus:
        if not self.backend:
            return StreamingStatus.NOT_SUPPORTED

        if not self.backend.supports_streaming():
            return StreamingStatus.NOT_SUPPORTED

        if self.streaming_thread and self.streaming_thread.is_alive():
            return StreamingStatus.ALREADY_RUNNING

        def streaming_wrapper(audio_source, callback):
            def process_callback(result):
                result['processed_text'] = post_process(result['raw_text'])
                callback(result)

            self.backend.start_streaming(audio_source, process_callback, sample_rate, channels, language)

        try:
            self.streaming_thread = threading.Thread(target=streaming_wrapper, args=(audio_source, callback))
            self.streaming_thread.start()
            self.streaming_status = StreamingStatus.STREAMING
            return StreamingStatus.STREAMING
        except Exception:
            return StreamingStatus.FAILED_TO_START

    def stop_streaming_transcription(self):
        if self.backend and self.backend.supports_streaming():
            self.backend.stop_streaming()
        if self.streaming_thread:
            self.streaming_thread.join()
            self.streaming_thread = None
        self.streaming_status = StreamingStatus.IDLE

    def get_streaming_status(self) -> StreamingStatus:
        return self.streaming_status

    def reload_config(self):
        if self.backend:
            self.backend.cleanup()
        self.config = ConfigManager.get_config_section('model_options')
        self._initialize_backend()

    def cleanup(self):
        if self.get_streaming_status() != StreamingStatus.NOT_SUPPORTED:
            self.stop_streaming_transcription()
        if self.backend:
            self.backend.cleanup()

class OpenAIBackend(TranscriptionBackend):
    def initialize(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("Failed to import OpenAI. Make sure it's installed.")

        self.OpenAI = OpenAI
        self.config = ConfigManager.get_config_section('model_options.backends.openai')
        self.client = self.OpenAI(
            api_key=self.config.get('api_key') or os.getenv(OPENAI_API_KEY),
            base_url=self.config.get('base_url') or 'https://api.openai.com/v1'
        )

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000, channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
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
                'language': language,  # OpenAI doesn't return detected language, so we use the input language
            }
        except Exception as e:
            raise RuntimeError(f"OpenAI transcription failed: {str(e)}")

    def _prepare_audio_data(self, audio_data: np.ndarray, sample_rate: int, channels: int) -> np.ndarray:
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

    def supports_streaming(self) -> StreamingStatus:
        streaming_supported = ConfigManager.get_config_value('model_options.backends.openai.capabilities.streaming')
        return StreamingStatus.IDLE if streaming_supported else StreamingStatus.NOT_SUPPORTED

    def start_streaming(self, audio_source: Any, callback: Callable[[Dict[str, Any]], None], sample_rate: int = 16000, channels: int = 1, language: str = 'auto'):
        raise NotImplementedError("Streaming is not currently supported for OpenAI backend")

    def stop_streaming(self):
        raise NotImplementedError("Streaming is not currently supported for OpenAI backend")

    def cleanup(self):
        self.client = None

class FasterWhisperBackend(TranscriptionBackend):
    def initialize(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError("Failed to import faster_whisper. Make sure it's installed.")

        self.WhisperModel = WhisperModel
        self.config = ConfigManager.get_config_section('model_options.backends.faster_whisper')
        self.model = None
        self._load_model()

    def _load_model(self):
        ConfigManager.console_print('Creating Faster Whisper model...')
        compute_type = self.config.get('compute_type', 'default')
        model_path = self.config.get('model_path', '')
        device = self.config.get('device', 'auto')
        model_name = self.config.get('model', 'base')

        if model_path:
            try:
                ConfigManager.console_print(f'Loading model from: {model_path}')
                self.model = self.WhisperModel(model_path,
                                               device=device,
                                               compute_type=compute_type,
                                               download_root=None)
                ConfigManager.console_print('Model loaded successfully from specified path.')
                return
            except Exception as e:
                print(f'Error loading model from path: {e}')
                raise RuntimeError(f"Failed to load model from specified path: {e}")

        # If model_path is empty, use online models
        try:
            ConfigManager.console_print(f'Attempting to load {model_name} model...')
            self.model = self.WhisperModel(model_name,
                                           device=device,
                                           compute_type=compute_type)
            ConfigManager.console_print(f'{model_name.capitalize()} model loaded successfully.')
        except Exception as e:
            print(f'Error loading {model_name} model: {e}')
            print('Falling back to base model on CPU...')
            try:
                self.model = self.WhisperModel('base',
                                               device='cpu',
                                               compute_type='default')
                ConfigManager.console_print('Base model loaded successfully on CPU.')
            except Exception as e:
                print(f'Failed to load base model on CPU: {e}')
                raise RuntimeError(f"Failed to initialize any Whisper model: {e}")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000, channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.model:
            raise RuntimeError("Model not initialized")

        # Check array type and convert if necessary
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

        segments, info = self.model.transcribe(
            audio=audio_data,
            language=language if language != 'auto' else None,
            initial_prompt=self.config.get('initial_prompt'),
            condition_on_previous_text=self.config.get('condition_on_previous_text', True),
            temperature=self.config.get('temperature', 0.0),
            vad_filter=self.config.get('vad_filter', False),
        )

        transcription = ''.join([segment.text for segment in list(segments)])

        return {
            'raw_text': transcription,
            'language': info.language,
        }

    def supports_streaming(self) -> StreamingStatus:
        streaming_supported = ConfigManager.get_config_value('model_options.backends.faster_whisper.capabilities.streaming')
        return StreamingStatus.IDLE if streaming_supported else StreamingStatus.NOT_SUPPORTED

    def start_streaming(self, audio_source: Any, callback: Callable[[Dict[str, Any]], None], sample_rate: int = 16000, channels: int = 1, language: str = 'auto'):
        raise NotImplementedError("Streaming is not supported for Faster Whisper backend")

    def stop_streaming(self):
        raise NotImplementedError("Streaming is not supported for Faster Whisper backend")

    def cleanup(self):
        self.model = None
