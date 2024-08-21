import threading
import time
import traceback
import numpy as np
import sounddevice as sd
import webrtcvad
from collections import deque

from utils import ConfigManager


class ResultThread(threading.Thread):
    """
    A thread class for handling audio recording, transcription, and result processing.

    This class manages the entire process of:
    1. Recording audio from the microphone
    2. Detecting speech and silence
    3. Saving the recorded audio as numpy array
    4. Transcribing the audio
    5. Emitting the transcription result
    """

    def __init__(self, transcription_manager):
        """
        Initialize the ResultThread.

        :param transcription_manager: TranscriptionManager instance
        """
        super().__init__()
        self.transcription_manager = transcription_manager
        self.is_recording = False
        self.is_running = True
        self.sample_rate = None
        self.lock = threading.Lock()
        self.status_callback = None
        self.result_callback = None

    def set_callbacks(self, status_callback, result_callback):
        self.status_callback = status_callback
        self.result_callback = result_callback

    def stop_recording(self):
        """Stop the current recording session."""
        with self.lock:
            self.is_recording = False

    def stop(self):
        """Stop the entire thread execution."""
        with self.lock:
            self.is_running = False
        self.emit_status('idle')
        self.join()

    def emit_status(self, status):
        if self.status_callback:
            self.status_callback(status)

    def emit_result(self, result):
        if self.result_callback:
            self.result_callback(result)

    def run(self):
        """Main execution method for the thread."""
        try:
            if not self.is_running:
                return

            with self.lock:
                self.is_recording = True

            self.emit_status('recording')
            ConfigManager.console_print('Recording...')
            audio_data = self._record_audio()

            if not self.is_running:
                return

            if audio_data is None:
                self.emit_status('idle')
                return

            self.emit_status('transcribing')
            ConfigManager.console_print('Transcribing...')

            start_time = time.time()
            transcription_result = self.transcription_manager.transcribe(audio_data, sample_rate=self.sample_rate)
            end_time = time.time()

            if transcription_result is None:
                self.emit_status('error')
                return

            transcription_time = end_time - start_time
            ConfigManager.console_print(f'Transcription completed in {transcription_time:.2f} seconds. Post-processed line:{transcription_result["processed_text"]}')

            self.emit_status('idle')
            self.emit_result(transcription_result["processed_text"])

        except Exception as e:
            traceback.print_exc()
            self.emit_status('error')
            self.emit_result('')
        finally:
            self.stop_recording()

    def _record_audio(self):
        """
        Record audio from the microphone and save it to a temporary file.

        :return: numpy array of audio data, or None if the recording is too short
        """
        recording_options = ConfigManager.get_config_section('recording_options')
        self.sample_rate = recording_options.get('sample_rate') or 16000
        frame_duration_ms = 30  # 30ms frame duration for WebRTC VAD
        frame_size = int(self.sample_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get('silence_duration') or 900
        silence_frames = int(silence_duration_ms / frame_duration_ms)

        # 150ms delay before starting VAD to avoid mistaking the sound of key pressing for voice
        initial_frames_to_skip = int(0.15 * self.sample_rate / frame_size)

        # Create VAD only for recording modes that use it
        recording_mode = recording_options.get('recording_mode') or 'continuous'
        vad = None
        if recording_mode in ('voice_activity_detection', 'continuous'):
            vad = webrtcvad.Vad(2)  # VAD aggressiveness: 0 to 3, 3 being the most aggressive
            speech_detected = False
            silent_frame_count = 0

        audio_buffer = deque(maxlen=frame_size)
        recording = []

        sound_device = recording_options.get('sound_device')
        if sound_device == '':
            sound_device = None  # Use default device if empty string

        data_ready = threading.Event()

        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}")
            audio_buffer.extend(indata[:, 0])
            data_ready.set()

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16',
                            blocksize=frame_size, device=sound_device, callback=audio_callback):
            while self.is_running and self.is_recording:
                data_ready.wait()
                data_ready.clear()

                if len(audio_buffer) < frame_size:
                    continue

                # Save frame
                frame = np.array(list(audio_buffer), dtype=np.int16)
                audio_buffer.clear()
                recording.extend(frame)

                # Avoid trying to detect voice in initial frames
                if initial_frames_to_skip > 0:
                    initial_frames_to_skip -= 1
                    continue

                if vad:
                    if vad.is_speech(frame.tobytes(), self.sample_rate):
                        silent_frame_count = 0
                        if not speech_detected:
                            ConfigManager.console_print("Speech detected.")
                            speech_detected = True
                    else:
                        silent_frame_count += 1

                    if speech_detected and silent_frame_count > silence_frames:
                        break

        audio_data = np.array(recording, dtype=np.int16)
        duration = len(audio_data) / self.sample_rate

        ConfigManager.console_print(f'Recording finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds')

        min_duration_ms = recording_options.get('min_duration') or 100

        if (duration * 1000) < min_duration_ms:
            ConfigManager.console_print(f'Discarded due to being too short.')
            return None

        return audio_data
