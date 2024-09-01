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
        self.backend: TranscriptionBackendBase = backend_class()  # Instantiate the class
        self.processing_thread = None
        # Initialize the state to IDLE. This state indicates that no transcription
        # is currently happening.
        self.state = TranscribingState.IDLE
        self.current_session_id = None
        # Event used to signal the processing thread when there's work to do or when to exit
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
            self.processing_thread = threading.Thread(target=self._processing_thread)
            self.processing_thread.start()

    def get_preferred_streaming_chunk_size(self):
        return self.backend.get_preferred_streaming_chunk_size()

    def stop(self):
        self.state = TranscribingState.IDLE
        self.transcribe_event.set()  # Wake up the thread to exit
        if self.processing_thread:
            self.processing_thread.join()
            self.processing_thread = None

    def start_streaming(self, profile_name: str, session_id: str):
        # Set the current session ID for tracking which audio stream we're processing
        self.current_session_id = session_id
        # Change state to STREAMING, indicating that we're now actively transcribing incoming audio
        self.state = TranscribingState.STREAMING
        # Signal the processing thread to start working
        self.transcribe_event.set()

    def start_processing(self, profile_name: str, session_id: str):
        self.current_session_id = session_id
        self.state = TranscribingState.PROCESSING
        self.transcribe_event.set()

    def stop_streaming(self):
        # Change state to DRAINING, indicating that we should process remaining audio in the queue
        # but not accept new audio chunks
        self.state = TranscribingState.DRAINING

    def stop_processing(self):
        self.state = TranscribingState.IDLE
        self.current_session_id = None

    def _processing_thread(self):
        while True:
            self.transcribe_event.wait()
            self.transcribe_event.clear()
            if self.state == TranscribingState.IDLE:
                break

            if self.state == TranscribingState.PROCESSING:
                self._process_complete()
            # Handle streaming transcription (including draining)
            elif self.state in (TranscribingState.STREAMING, TranscribingState.DRAINING):
                self._process_streaming()

    def _process_streaming(self):
        if not self.backend:
            ConfigManager.log_print("Backend not initialized. Streaming cannot start.")
            return

        # Continue processing while we're either actively streaming or draining the queue
        while self.state in (TranscribingState.STREAMING, TranscribingState.DRAINING):
            try:
                # Try to get an audio chunk from the queue
                audio_data = self.audio_queue.get(timeout=0.2)
                if audio_data['session_id'] == self.current_session_id:
                    # Process the audio chunk and get the transcription result
                    result = self.backend.transcribe_stream(
                        audio_data['audio_chunk'],
                        audio_data['sample_rate'],
                        audio_data['channels'],
                        audio_data['language']
                    )
                    # Emit the result (could be partial or complete utterance)
                    self._emit_result(result)
            except queue.Empty:
                # If the queue is empty and we're in DRAINING state, it's time to finalize
                if self.state == TranscribingState.DRAINING and self.audio_queue.empty():
                    self._finalize_streaming()
                    break

    def _finalize_streaming(self):
        # Get the final result from the backend (might include any buffered audio)
        final_result = self.backend.finalize_stream()
        # Emit the final result
        self._emit_result(final_result)
        # Reset the state to IDLE and clear the session ID
        self.state = TranscribingState.IDLE
        self.current_session_id = None
        self.event_bus.emit("streaming_finished", self.profile_name)

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
                                            f"seconds.\nRaw transcription: {result['raw_text']}")
                    result['is_utterance_end'] = True
                    self._emit_result(result)
                    break
            except queue.Empty:
                continue

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
