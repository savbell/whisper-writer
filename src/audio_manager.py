import threading
import numpy as np
import sounddevice as sd
import webrtcvad
from collections import deque

from config_manager import ConfigManager
from event_bus import EventBus
from enums import RecordingMode, AudioManagerState
from profile import Profile


class AudioManager:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.state = AudioManagerState.STOPPED
        self.state_change_event = threading.Event()
        self.thread = None
        self.current_profile = None
        self.current_session_id = None

    def start(self):
        if self.state == AudioManagerState.STOPPED:
            self.state = AudioManagerState.IDLE
            self.thread = threading.Thread(target=self._audio_thread)
            self.thread.start()

    def stop(self):
        if self.state != AudioManagerState.STOPPED:
            self.state = AudioManagerState.STOPPED
            self.state_change_event.set()
            if self.thread:
                self.thread.join(timeout=2)
                if self.thread.is_alive():
                    ConfigManager.log_print("Warning: Audio thread did not terminate gracefully.")

    def start_recording(self, profile: Profile, session_id: str):
        self.current_profile = profile
        self.current_session_id = session_id
        self.state = AudioManagerState.RECORDING
        self.state_change_event.set()

    def stop_recording(self):
        if self.state == AudioManagerState.RECORDING:
            self.state = AudioManagerState.IDLE
            self.state_change_event.set()

    def _audio_thread(self):
        while self.state != AudioManagerState.STOPPED:
            self.state_change_event.wait()
            self.state_change_event.clear()
            if self.state == AudioManagerState.RECORDING:
                self._record_audio()

    def _record_audio(self):
        recording_options = ConfigManager.get_section('recording_options',
                                                      self.current_profile.name)
        sample_rate = recording_options.get('sample_rate', 16000)
        frame_duration_ms = 30
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get('silence_duration', 900)
        silence_frames = int(silence_duration_ms / frame_duration_ms)
        recording_mode = RecordingMode[recording_options.get('recording_mode', 'PRESS_TO_TOGGLE')
                                       .upper()]
        channels = 1

        streaming_chunk_size = int(0.2 * sample_rate)  # 0.2 seconds of audio for streaming
        # Skip running vad for the first 0.15 seconds to avoid mistaking keyboard noise for voice
        initial_frames_to_skip = int(0.15 * sample_rate / frame_size)

        vad = None
        if recording_mode in (RecordingMode.VOICE_ACTIVITY_DETECTION, RecordingMode.CONTINUOUS):
            vad = webrtcvad.Vad(2)

        speech_detected = False
        silent_frame_count = 0
        audio_buffer = deque(maxlen=frame_size)
        recording = []

        sound_device = recording_options.get('sound_device')
        if sound_device == '':
            sound_device = None

        data_ready = threading.Event()

        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.log_print(f"Audio callback status: {status}")
            audio_buffer.extend(indata[:, 0])
            data_ready.set()

        with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='int16',
                            blocksize=frame_size, device=sound_device, callback=audio_callback):
            while self.state == AudioManagerState.RECORDING:
                data_ready.wait()
                data_ready.clear()

                if len(audio_buffer) < frame_size:
                    continue

                frame = np.array(list(audio_buffer), dtype=np.int16)
                audio_buffer.clear()
                recording.extend(frame)

                if initial_frames_to_skip > 0:
                    initial_frames_to_skip -= 1
                    continue

                if vad:
                    if vad.is_speech(frame.tobytes(), sample_rate):
                        silent_frame_count = 0
                        if not speech_detected:
                            ConfigManager.log_print("Speech detected.")
                            speech_detected = True
                    else:
                        silent_frame_count += 1

                    if speech_detected and silent_frame_count > silence_frames:
                        break

                if recording_mode in (RecordingMode.PRESS_TO_TOGGLE, RecordingMode.HOLD_TO_RECORD):
                    if self.state != AudioManagerState.RECORDING:
                        break

                if self.current_profile.is_streaming and len(recording) >= streaming_chunk_size:
                    self._push_audio_chunk(np.array(recording[:streaming_chunk_size],
                                                    dtype=np.int16), sample_rate, channels)
                    recording = recording[streaming_chunk_size:]

        if not self.current_profile.is_streaming:
            audio_data = np.array(recording, dtype=np.int16)
            duration = len(audio_data) / sample_rate

            ConfigManager.log_print(f'Recording finished. Size: {audio_data.size} samples, '
                                    f'Duration: {duration:.2f} seconds')

            min_duration_ms = recording_options.get('min_duration', 100)

            if (duration * 1000) >= min_duration_ms:
                self._push_audio_chunk(audio_data, sample_rate, channels)
            else:
                ConfigManager.log_print('Discarded due to being too short.')
                self.event_bus.emit("audio_discarded", self.current_session_id)

        self.current_profile = None
        self.current_session_id = None
        self.state = AudioManagerState.IDLE

    def _push_audio_chunk(self, audio_data: np.ndarray, sample_rate: int, channels: int):
        self.current_profile.audio_queue.put({
            'session_id': self.current_session_id,
            'sample_rate': sample_rate,
            'channels': channels,
            'language': 'auto',
            'audio_chunk': audio_data
        })

    def cleanup(self):
        self.stop()
        # Reset all attributes to enforce garbage collection
        self.thread = None
        self.current_profile = None
        self.current_session_id = None
