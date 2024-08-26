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
        self.backend: TranscriptionBackendBase = None
        self.processing_thread = None
        self.state = TranscribingState.IDLE
        self.current_session_id = None
        self.transcribe_event = threading.Event()

    def start(self):
        if not self.backend:
            self.backend = self._initialize_backend()

        if not self.processing_thread:
            self.processing_thread = threading.Thread(target=self._processing_thread)
            self.processing_thread.start()

    def _initialize_backend(self):
        backend_options = ConfigManager.get_section('backend', self.profile_name)
        backend_class = self._get_backend_class()
        backend = backend_class()
        backend.initialize(backend_options)
        return backend

    def _get_backend_class(self):
        if self.backend_type == 'faster_whisper':
            from transcription_backend.faster_whisper_backend import FasterWhisperBackend
            return FasterWhisperBackend
        elif self.backend_type == 'openai':
            from transcription_backend.openai_backend import OpenAIBackend
            return OpenAIBackend
        else:
            raise ValueError(f"Unsupported backend type: {self.backend_type}")

    def stop(self):
        self.state = TranscribingState.IDLE
        self.transcribe_event.set()  # Wake up the thread to exit
        if self.processing_thread:
            self.processing_thread.join()
            self.processing_thread = None

    def start_streaming(self, profile_name: str, session_id: str):
        self.current_session_id = session_id
        self.state = TranscribingState.STREAMING
        self.transcribe_event.set()

    def start_processing(self, profile_name: str, session_id: str):
        self.current_session_id = session_id
        self.state = TranscribingState.PROCESSING
        self.transcribe_event.set()

    def stop_streaming(self):
        self.state = TranscribingState.IDLE
        self.current_session_id = None

    def stop_processing(self):
        self.state = TranscribingState.IDLE
        self.current_session_id = None

    def _processing_thread(self):
        while True:
            self.transcribe_event.wait()
            self.transcribe_event.clear()

            if self.state == TranscribingState.IDLE:
                break  # Exit the thread if we're in IDLE state

            if self.state == TranscribingState.STREAMING:
                self._process_streaming()
            elif self.state == TranscribingState.PROCESSING:
                self._process_complete()

    def _process_streaming(self):
        if not self.backend:
            ConfigManager.log_print("Backend not initialized. Streaming cannot start.")
            return

        while self.state == TranscribingState.STREAMING:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                if audio_data['session_id'] == self.current_session_id:
                    result = self.backend.transcribe_stream(
                        audio_data['audio_chunk'],
                        audio_data['sample_rate'],
                        audio_data['channels'],
                        audio_data['language']
                    )
                    self._emit_result(result, is_final=False)
            except queue.Empty:
                continue

    def _process_complete(self):
        if not self.backend:
            ConfigManager.log_print("Backend not initialized. Processing cannot start.")
            return

        while self.state == TranscribingState.PROCESSING:
            try:
                audio_data = self.audio_queue.get(timeout=0.5)
                if audio_data['session_id'] == self.current_session_id:
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
                                            f'seconds.')

                    self._emit_result(result, is_final=True)
                    break
            except queue.Empty:
                continue

    def _emit_result(self, result: Dict[str, Any], is_final: bool):
        self.event_bus.emit("raw_transcription_result", result, is_final, self.current_session_id)

    def cleanup(self):
        self.stop()
        if self.backend:
            self.backend.cleanup()
