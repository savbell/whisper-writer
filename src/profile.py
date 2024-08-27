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
    The Profile class encapsulates all the components and settings specific to a particular
    transcription profile, serving as a self-contained unit for managing the transcription process.
    It coordinates the interaction between the TranscriptionManager, PostProcessingManager,
    and OutputManager, handling the flow of audio data and transcribed text through various stages
    of processing. The Profile class also manages its own state transitions, from idle to recording
    to transcribing, and provides methods to determine how it should respond to user inputs based
    on its current state and configuration.
    """
    def __init__(self, name: str, event_bus: EventBus):
        """Initialize the Profile with name, configuration, and necessary components."""
        self.name = name
        self.config = ConfigManager.get_section('profiles', name)
        self.audio_queue = Queue()
        self.output_manager = OutputManager(name, event_bus)
        self.recording_mode = RecordingMode[self.config['recording_options']['recording_mode']
                                            .upper()]
        self.state = ProfileState.IDLE
        self.event_bus = event_bus
        self.is_streaming = self.config['backend'].get('capabilities', {}).get('streaming', False)
        self.post_processor = PostProcessingManager(
            self.config['post_processing']['enabled_scripts'])
        self.transcription_manager = TranscriptionManager(self, event_bus)

        self.event_bus.subscribe("raw_transcription_result", self.handle_raw_transcription)

    def handle_raw_transcription(self, result: Dict, is_final: bool, session_id: str):
        """Process raw transcription results and emit the processed result."""
        processed_result = self.post_processor.process(result['raw_text'])
        complete_result = {
            'raw': result['raw_text'],
            'processed': processed_result,
            'language': result['language']
        }
        self.event_bus.emit("transcription_result", complete_result, is_final, session_id)

    def start_transcription(self, session_id: str):
        """Start the transcription process for this profile."""
        ConfigManager.log_print(f"({self.name}) Recording...")
        self.event_bus.emit("profile_state_change", f"({self.name}) Recording...")
        if self.is_streaming:
            self.state = ProfileState.STREAMING
            self.transcription_manager.start_streaming(self.name, session_id)
        else:
            self.state = ProfileState.RECORDING
            self.transcription_manager.start_processing(self.name, session_id)

    def stop_recording(self):
        """Stop the recording process and transition to transcribing state."""
        if self.state in [ProfileState.RECORDING, ProfileState.STREAMING]:
            self.event_bus.emit("profile_state_change", f"({self.name}) Transcribing...")
            if self.is_streaming:
                self.transcription_manager.stop_streaming()
            self.state = ProfileState.TRANSCRIBING

    def finish_transcription(self):
        """Finish the transcription process and return to idle state."""
        self.state = ProfileState.IDLE
        self.event_bus.emit("profile_state_change", '')
        if not self.is_streaming:
            self.transcription_manager.stop_processing()

    def output(self, text: str):
        """Output the processed text using the output manager."""
        self.output_manager.typewrite(text)

    def should_start_on_press(self) -> bool:
        """Determine if recording should start on key press."""
        return self.state == ProfileState.IDLE

    def should_stop_on_press(self) -> bool:
        """Determine if recording should stop on key press."""
        return self.state == ProfileState.RECORDING and self.recording_mode in [
            RecordingMode.PRESS_TO_TOGGLE,
            RecordingMode.CONTINUOUS,
            RecordingMode.VAD
        ]

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
            self.event_bus.unsubscribe("raw_transcription_result", self.handle_raw_transcription)

        # Reset all attributes to enforce garbage collection
        self.config = None
        self.audio_queue = None
        self.output_manager = None
        self.recording_mode = None
        self.state = None
        self.is_streaming = None
        self.post_processor = None
        self.transcription_manager = None
