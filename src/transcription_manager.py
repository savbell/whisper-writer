import threading
import time
import queue
from typing import Dict, Any

from config_manager import ConfigManager
from enums import TranscribingState
from event_bus import EventBus
from transcription_backend.transcription_backend_base import TranscriptionBackendBase


class TranscriptionManager:
    def __init__(self, profile, event_bus: EventBus):
        self.profile_name = profile.name
        self.event_bus = event_bus
        self.audio_queue = profile.audio_queue
        self.backend_type = ConfigManager.get_value('backend_type', self.profile_name)
        backend_class = self._get_backend_class()
        self.backend: TranscriptionBackendBase = backend_class()
        self.processing_thread = None
        self.state = TranscribingState.IDLE
        self.current_session_id = None
        self.transcribe_event = threading.Event()
        self.event_bus.subscribe("transcription_error", self._handle_transcription_error)

    def _get_backend_class(self):
        if self.backend_type == 'faster_whisper':
            from transcription_backend.faster_whisper_backend import FasterWhisperBackend
            return FasterWhisperBackend
        elif self.backend_type == 'openai':
            from transcription_backend.openai_backend import OpenAIBackend
            return OpenAIBackend
        elif self.backend_type == 'vosk':
            from transcription_backend.vosk_backend import VoskBackend
            return VoskBackend
        else:
            raise ValueError(f"Unsupported backend type: {self.backend_type}")

    def start(self):
        if not self.backend.is_initialized():
            backend_options = ConfigManager.get_section('backend', self.profile_name)
            self.backend.initialize(backend_options)

        if not self.processing_thread:
            self.processing_thread = threading.Thread(target=self._transcription_thread)
            self.processing_thread.start()

    def get_preferred_streaming_chunk_size(self):
        return self.backend.get_preferred_streaming_chunk_size()

    def stop(self):
        self.state = TranscribingState.IDLE
        self.transcribe_event.set()  # Wake up the thread to exit
        if self.processing_thread:
            self.processing_thread.join()
            self.processing_thread = None

    def start_transcription(self, session_id: str):
        self.current_session_id = session_id
        self.state = TranscribingState.TRANSCRIBING
        self.transcribe_event.set()

    def _transcription_thread(self):
        while True:
            self.transcribe_event.wait()
            self.transcribe_event.clear()

            if self.state == TranscribingState.IDLE:
                break

            self._process_audio()

    def _process_audio(self):
        if not self.backend:
            ConfigManager.log_print("Backend not initialized. Transcription cannot start.")
            return

        is_streaming = ConfigManager.get_value('backend.use_streaming', self.profile_name)

        while self.state == TranscribingState.TRANSCRIBING:
            try:
                audio_data = self.audio_queue.get(timeout=0.2)

                if audio_data is None:  # Sentinel value
                    self._finalize_transcription(is_streaming)
                    break

                result = self._transcribe_chunk(audio_data, is_streaming)
                self._emit_result(result)

            except queue.Empty:
                continue

    def _transcribe_chunk(self, audio_data, is_streaming):
        if is_streaming:
            return self.backend.transcribe_stream(
                audio_data['audio_chunk'],
                audio_data['sample_rate'],
                audio_data['channels'],
                audio_data['language']
            )
        else:
            start_time = time.time()
            result = self.backend.transcribe_complete(
                audio_data['audio_chunk'],
                audio_data['sample_rate'],
                audio_data['channels'],
                audio_data['language']
            )
            end_time = time.time()
            transcription_time = end_time - start_time
            ConfigManager.log_print(f'Transcription completed in {transcription_time:.2f} '
                                    f"seconds.\nRaw transcription: {result['raw_text']}")
            result['is_utterance_end'] = True
            return result

    def _finalize_transcription(self, is_streaming):
        if is_streaming:
            final_result = self.backend.finalize_stream()
            self._emit_result(final_result)

        self.state = TranscribingState.IDLE
        self.current_session_id = None
        self.event_bus.emit("transcription_finished", self.profile_name)

    def _emit_result(self, result: Dict[str, Any]):
        # If there's an error in the result, emit a transcription error event
        if result['error']:
            self.event_bus.emit("transcription_error", result['error'])

        # Emit the raw transcription result
        # This could be a partial result, a complete utterance, or the final result of the stream
        self.event_bus.emit("raw_transcription_result", result, self.current_session_id)

    def _handle_transcription_error(self, message: str):
        ConfigManager.log_print(f"Transcription error: {message}")

    def cleanup(self):
        self.stop()
        if self.backend:
            self.backend.cleanup()
