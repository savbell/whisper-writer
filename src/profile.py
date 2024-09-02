from queue import Queue
from typing import Dict

from output_manager import OutputManager
from transcription_manager import TranscriptionManager
from enums import ProfileState, RecordingMode
from event_bus import EventBus
from post_processing import PostProcessingManager
from config_manager import ConfigManager


class Profile:
    """
    Encapsulates the configuration, state, and behavior of a specific transcription profile.

    Manages the lifecycle of transcription sessions, including recording, processing,
    and output of transcribed text. Coordinates interactions between TranscriptionManager,
    PostProcessingManager, and OutputManager. Handles both streaming and non-streaming
    transcription modes, and manages its own state transitions based on user input and
    transcription events.
    """
    def __init__(self, name: str, event_bus: EventBus):
        """Initialize the Profile with name, configuration, and necessary components."""
        self.name = name
        self.config = ConfigManager.get_section('profiles', name)
        self.event_bus = event_bus
        self.audio_queue = Queue()
        self.output_manager = OutputManager(name, event_bus)
        self.recording_mode = RecordingMode[self.config['recording_options']['recording_mode']
                                            .upper()]
        self.state = ProfileState.IDLE
        self.post_processor = PostProcessingManager(
                                self.config['post_processing']['enabled_scripts'])
        self.transcription_manager = TranscriptionManager(self, event_bus)
        self.is_streaming = self.config['backend'].get('use_streaming', False)
        self.streaming_chunk_size = self.transcription_manager.get_preferred_streaming_chunk_size()
        self.result_handler = (StreamingResultHandler(self.output_manager)
                               if self.is_streaming else None)
        self.current_session_id = None

        self.event_bus.subscribe("raw_transcription_result", self.handle_raw_transcription)
        self.event_bus.subscribe("transcription_finished", self.handle_transcription_finished)

    def start_transcription(self, session_id: str):
        """Start the transcription process for this profile."""
        self.current_session_id = session_id
        self.state = ProfileState.RECORDING
        self.event_bus.emit("profile_state_change", f"({self.name}) "
                            f"{'Streaming' if self.is_streaming else 'Recording'}...")
        self.transcription_manager.start_transcription(session_id)

    def stop_recording(self):
        """Stop the recording process and transition to transcribing state."""
        if self.state == ProfileState.RECORDING:
            self.event_bus.emit("profile_state_change", f"({self.name}) Transcribing...")
            self.state = ProfileState.TRANSCRIBING

    def is_recording(self) -> bool:
        return self.state == ProfileState.RECORDING

    def is_idle(self) -> bool:
        return self.state == ProfileState.IDLE

    def finish_transcription(self):
        """Finish the transcription process and return to idle state."""
        previous_state = self.state
        self.state = ProfileState.IDLE
        self.event_bus.emit("profile_state_change", '')

        # Make sure to reset sid BEFORE calling ApplicationController via event
        old_sid = self.current_session_id
        self.current_session_id = None
        # Only emit transcription_complete if we were actually transcribing
        if previous_state in [ProfileState.TRANSCRIBING, ProfileState.RECORDING]:
            self.event_bus.emit("transcription_complete", old_sid)

    def handle_raw_transcription(self, result: Dict, session_id: str):
        """Process raw transcription results and emit the processed result."""
        if session_id != self.current_session_id:
            return

        processed_result = self.post_processor.process(result)

        if self.is_streaming:
            self.result_handler.handle_result(processed_result)
        else:
            self.output(processed_result['processed'])

    def handle_transcription_finished(self, profile_name: str):
        if profile_name == self.name:
            self.finish_transcription()

    def output(self, text: str):
        """Output the processed text using the output manager."""
        if text:
            self.output_manager.typewrite(text)

    def should_start_on_press(self) -> bool:
        """Determine if recording should start on key press."""
        return self.state == ProfileState.IDLE

    def should_stop_on_press(self) -> bool:
        """Determine if recording should stop on key press."""
        return (self.state == ProfileState.RECORDING and
                self.recording_mode in [
                    RecordingMode.PRESS_TO_TOGGLE,
                    RecordingMode.CONTINUOUS,
                    RecordingMode.VOICE_ACTIVITY_DETECTION
                ])

    def should_stop_on_release(self) -> bool:
        """Determine if recording should stop on key release."""
        return (self.state == ProfileState.RECORDING and
                self.recording_mode == RecordingMode.HOLD_TO_RECORD)

    def cleanup(self):
        """Clean up resources and reset attributes for garbage collection."""
        self.finish_transcription()
        if self.transcription_manager:
            self.transcription_manager.cleanup()
        if self.output_manager:
            self.output_manager.cleanup()
        if self.event_bus:
            self.event_bus.unsubscribe("raw_transcription_result",
                                       self.handle_raw_transcription)
            self.event_bus.unsubscribe("transcription_finished",
                                       self.handle_transcription_finished)

        # Reset all attributes to enforce garbage collection
        self.config = None
        self.audio_queue = None
        self.output_manager = None
        self.recording_mode = None
        self.state = None
        self.is_streaming = None
        self.post_processor = None
        self.transcription_manager = None
        self.result_handler = None


class StreamingResultHandler:
    def __init__(self, output_manager):
        self.output_manager = output_manager
        self.buffer = ""

    def handle_result(self, result: Dict):
        new_text = result['processed']

        if not new_text:
            return

        common_prefix_length = self._get_common_prefix_length(self.buffer, new_text)
        backspace_count = len(self.buffer) - common_prefix_length
        text_to_output = new_text[common_prefix_length:]

        if backspace_count > 0:
            self.output_manager.backspace(backspace_count)

        if text_to_output:
            self.output_manager.typewrite(text_to_output)

        self.buffer = new_text

        if result.get('is_utterance_end', False):
            self.buffer = ""

    def _get_common_prefix_length(self, s1: str, s2: str) -> int:
        for i, (c1, c2) in enumerate(zip(s1, s2)):
            if c1 != c2:
                return i
        return min(len(s1), len(s2))
