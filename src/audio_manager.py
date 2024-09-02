import threading
import numpy as np
import sounddevice as sd
import webrtcvad
from collections import deque, namedtuple
from queue import Queue, Empty

from config_manager import ConfigManager
from event_bus import EventBus
from enums import RecordingMode, AudioManagerState
from profile import Profile

RecordingContext = namedtuple('RecordingContext', ['profile', 'session_id'])


class AudioManager:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.state = AudioManagerState.STOPPED
        self.recording_queue = Queue()
        self.thread = None

    def start(self):
        if self.state == AudioManagerState.STOPPED:
            self.state = AudioManagerState.IDLE
            self.thread = threading.Thread(target=self._audio_thread)
            self.thread.start()

    def stop(self):
        if self.state != AudioManagerState.STOPPED:
            self.state = AudioManagerState.STOPPED
            self.recording_queue.put(None)  # Sentinel value to stop the thread
            if self.thread:
                self.thread.join(timeout=2)
                if self.thread.is_alive():
                    ConfigManager.log_print("Warning: Audio thread did not terminate gracefully.")

    def start_recording(self, profile: Profile, session_id: str):
        self.recording_queue.put(RecordingContext(profile, session_id))

    def stop_recording(self):
        self.recording_queue.put(None)  # Sentinel value to stop current recording

    def is_recording(self):
        return self.state == AudioManagerState.RECORDING

    def _audio_thread(self):
        while self.state != AudioManagerState.STOPPED:
            try:
                context = self.recording_queue.get(timeout=0.5)
                if context is None:
                    continue  # Skip this iteration, effectively stopping the current recording
                self.state = AudioManagerState.RECORDING
                self._record_audio(context)
                self.state = AudioManagerState.IDLE
            except Empty:
                continue

    def _record_audio(self, context: RecordingContext):
        recording_options = ConfigManager.get_section('recording_options',
                                                      context.profile.name)
        sample_rate = recording_options.get('sample_rate', 16000)
        frame_duration_ms = 30
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get('silence_duration', 900)
        silence_frames = int(silence_duration_ms / frame_duration_ms)
        recording_mode = RecordingMode[recording_options.get('recording_mode', 'PRESS_TO_TOGGLE')
                                       .upper()]
        channels = 1

        # Use the backend-suggested chunk size
        streaming_chunk_size = context.profile.streaming_chunk_size

        # If streaming_chunk_size is None or 0, fall back to a default value
        if not streaming_chunk_size:
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
            while self.state != AudioManagerState.STOPPED and self.recording_queue.empty():
                data_ready.wait(timeout=0.2)
                data_ready.clear()

                if len(audio_buffer) < frame_size:
                    continue

                frame = np.array(list(audio_buffer), dtype=np.int16)
                audio_buffer.clear()
                recording.extend(frame)

                if context.profile.is_streaming and len(recording) >= streaming_chunk_size:
                    arr = np.array(recording[:streaming_chunk_size], dtype=np.int16)
                    self._push_audio_chunk(context, arr, sample_rate, channels)
                    recording = recording[streaming_chunk_size:]

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

        if not context.profile.is_streaming:
            audio_data = np.array(recording, dtype=np.int16)
            duration = len(audio_data) / sample_rate

            ConfigManager.log_print(f'Recording finished. Size: {audio_data.size} samples, '
                                    f'Duration: {duration:.2f} seconds')

            min_duration_ms = recording_options.get('min_duration', 200)

            if vad and not speech_detected:
                ConfigManager.log_print('Discarded because no speech has been detected.')
                self.event_bus.emit("audio_discarded", context.session_id)
            elif (duration * 1000) >= min_duration_ms:
                self._push_audio_chunk(context, audio_data, sample_rate, channels)
            else:
                ConfigManager.log_print('Discarded due to being too short.')
                self.event_bus.emit("audio_discarded", context.session_id)

        context.profile.audio_queue.put(None)  # Push sentinel value

        if vad and self.state != AudioManagerState.STOPPED:
            self.event_bus.emit("recording_stopped", context.session_id)

    def _push_audio_chunk(self, context: RecordingContext, audio_data: np.ndarray,
                          sample_rate: int, channels: int):
        context.profile.audio_queue.put({
            'session_id': context.session_id,
            'sample_rate': sample_rate,
            'channels': channels,
            'language': 'auto',
            'audio_chunk': audio_data
        })

    def cleanup(self):
        self.stop()
        # Reset all attributes to enforce garbage collection
        self.thread = None
        self.recording_queue = None
