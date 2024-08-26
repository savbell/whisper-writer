import uuid
from queue import Queue
from typing import Dict

from audio_manager import AudioManager
from input_manager import InputManager
from enums import RecordingMode, ProfileState
from profile import Profile
from config_manager import ConfigManager


class ApplicationController:
    def __init__(self, ui_manager, event_bus):
        self.ui_manager = ui_manager
        self.event_bus = event_bus
        self.audio_queue = Queue()
        self.listening = False
        self.audio_manager = None
        self.input_manager = None

        self.active_profiles: Dict[str, Profile] = {}
        self.session_profile_map: Dict[str, str] = {}

        self.load_active_profiles()
        self.setup_connections()

    def load_active_profiles(self):
        active_profiles = ConfigManager.get_profiles(active_only=True)
        for profile in active_profiles:
            profile_name = profile['name']
            profile_obj = Profile(profile_name, self.event_bus)
            self.active_profiles[profile_name] = profile_obj

    def setup_connections(self):
        self.event_bus.subscribe("start_listening", self.handle_start_listening)
        self.event_bus.subscribe("shortcut_triggered", self.handle_shortcut)
        self.event_bus.subscribe("transcription_result", self.handle_transcription_result)
        self.event_bus.subscribe("config_changed", self.handle_config_change)
        self.event_bus.subscribe("close_app", self.close_application)
        self.event_bus.subscribe("audio_discarded", self.handle_audio_discarded)

    def handle_shortcut(self, profile_name: str, event_type: str):
        profile = self.active_profiles.get(profile_name)
        if profile:
            if event_type == "press":
                if profile.should_start_on_press():
                    self.start_recording(profile)
                elif profile.should_stop_on_press():
                    self.stop_recording(profile)
            elif event_type == "release":
                if profile.should_stop_on_release():
                    self.stop_recording(profile)

    def start_recording(self, profile: Profile):
        if profile.state == ProfileState.IDLE:
            session_id = str(uuid.uuid4())
            self.session_profile_map[session_id] = profile.name
            self.audio_manager.start_recording(profile, session_id)
            profile.start_transcription(session_id)

    def stop_recording(self, profile: Profile):
        if profile.state in [ProfileState.RECORDING, ProfileState.STREAMING]:
            self.audio_manager.stop_recording()
            profile.stop_recording()

    def finish_transcription(self, session_id: str):
        if session_id in self.session_profile_map:
            profile_name = self.session_profile_map[session_id]
            del self.session_profile_map[session_id]
            profile = self.active_profiles[profile_name]
            profile.finish_transcription()

    def handle_transcription_result(self, result: Dict, is_final: bool, session_id: str):
        if session_id in self.session_profile_map:
            profile_name = self.session_profile_map[session_id]
            profile = self.active_profiles[profile_name]
            profile.output(result['processed'])

            if is_final:
                if (profile.recording_mode == RecordingMode.CONTINUOUS and
                        profile.state != ProfileState.TRANSCRIBING):
                    self.finish_transcription(session_id)
                    self.start_recording(profile)
                elif not profile.is_streaming:
                    self.finish_transcription(session_id)
            elif profile.is_streaming:
                # Handle partial results for streaming mode if needed
                pass

    def handle_audio_discarded(self, session_id: str):
        if session_id in self.session_profile_map:
            profile_name = self.session_profile_map[session_id]
            profile = self.active_profiles[profile_name]
            self.finish_transcription(session_id)

            if profile.recording_mode == RecordingMode.CONTINUOUS:
                # Restart recording for continuous mode
                self.start_recording(profile)

    def handle_start_listening(self):
        self.listening = True
        self.start_core_components()
        self.event_bus.emit("core_components_started")

    def handle_config_change(self):
        self.cleanup()
        self.load_active_profiles()
        if self.listening:
            self.start_core_components()

    def run(self):
        self.ui_manager.show_main_window()
        exit_code = self.ui_manager.run_event_loop()  # Run QT event loop
        self.cleanup()
        return exit_code

    def start_core_components(self):
        self.input_manager = InputManager(self.event_bus)
        self.audio_manager = AudioManager(self.event_bus)
        self.input_manager.start()
        self.audio_manager.start()
        for profile in self.active_profiles.values():
            profile.transcription_manager.start()

    def close_application(self):
        self.event_bus.emit("quit_application")

    def cleanup(self):
        # Stop and cleanup audio-related components
        if self.audio_manager:
            self.audio_manager.stop_recording()
            self.audio_manager.cleanup()
            self.audio_manager = None

        # Stop and cleanup all active profiles
        for profile in self.active_profiles.values():
            profile.cleanup()

        # Clear the active profiles and session profile map
        self.active_profiles.clear()
        self.session_profile_map.clear()

        # Stop and cleanup input manager
        if self.input_manager:
            self.input_manager.cleanup()
            self.input_manager = None
