import time
import traceback
import numpy as np
import sounddevice as sd
import tempfile
import wave
import webrtcvad
from PyQt5.QtCore import QThread, QMutex, pyqtSignal
from collections import deque
from threading import Event

from transcription import transcribe
from utils import ConfigManager
from media_controller import MediaController


class ResultThread(QThread):
    """
    A thread class for handling audio recording, transcription, and result processing.

    This class manages the entire process of:
    1. Recording audio from the microphone
    2. Detecting speech and silence
    3. Saving the recorded audio as numpy array
    4. Transcribing the audio
    5. Emitting the transcription result

    Signals:
        statusSignal: Emits the current status of the thread (e.g., 'recording', 'transcribing', 'idle')
        resultSignal: Emits the transcription result
    """

    statusSignal = pyqtSignal(str, bool)
    resultSignal = pyqtSignal(str)

    def __init__(self, local_model=None, use_llm=False):
        """
        Initialize the ResultThread.

        :param local_model: Local transcription model (if applicable)
        :param use_llm: Boolean indicating whether to use LLM mode
        """
        super().__init__()
        self.local_model = local_model
        self.use_llm = use_llm
        self.is_recording = False
        self.is_running = True
        self.sample_rate = None
        self.mutex = QMutex()
        self.stop_event = Event()
        self.media_controller = MediaController()
        self.last_audio_time = time.time()
        self.is_transcribing = False  # New flag to track transcription state

    def stop_recording(self):
        """Stop the current recording session."""
        self.mutex.lock()
        self.is_recording = False
        self.mutex.unlock()

    def stop(self):
        """Stop the entire thread execution."""
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.statusSignal.emit('idle', False)
        self.wait()

    def run(self):
        """Main execution method for the thread."""
        try:
            if not self.is_running:
                return

            # Only control media if the setting is enabled
            if ConfigManager.get_config_value('misc', 'pause_media_during_recording'):
                self.media_controller.pause_media()
                self.media_controller.was_playing = True

            self.mutex.lock()
            self.is_recording = True
            self.mutex.unlock()

            self.statusSignal.emit('recording', self.use_llm)
            ConfigManager.console_print('Recording...')
            audio_data = self._record_audio()

            if not self.is_running:
                return

            if audio_data is None or len(audio_data) == 0:
                self.statusSignal.emit('idle', self.use_llm)
                return

            self.is_transcribing = True  # Set transcribing flag
            self.statusSignal.emit('transcribing', self.use_llm)
            ConfigManager.console_print('Transcribing...')

            # Time the transcription process
            start_time = time.time()
            result = transcribe(audio_data, self.local_model)
            end_time = time.time()

            transcription_time = end_time - start_time
            ConfigManager.console_print(f'Transcription completed in {transcription_time:.2f} seconds. Post-processed line: {result}')

            if not self.is_running:
                return

            self.statusSignal.emit('idle', self.use_llm)
            self.resultSignal.emit(result)

            # Reset transcribing flag and update last_audio_time after successful transcription
            self.is_transcribing = False
            self.last_audio_time = time.time()

            # Only resume media if the setting is enabled
            if ConfigManager.get_config_value('misc', 'pause_media_during_recording'):
                self.media_controller.resume_media()

        except Exception as e:
            ConfigManager.console_print(f"Error in ResultThread: {str(e)}")
            traceback.print_exc()
            self.statusSignal.emit('error', self.use_llm)
            self.resultSignal.emit('')
        finally:
            self.is_transcribing = False  # Ensure flag is reset

    def _record_audio(self):
        """
        Record audio from the microphone and save it to a temporary file.

        :return: numpy array of audio data, or None if the recording is too short
        """
        recording_options = ConfigManager.get_config_section('recording_options')
        self.sample_rate = recording_options.get('sample_rate') or 16000
        frame_duration_ms = 30
        frame_size = int(self.sample_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get('silence_duration') or 900
        silence_frames = int(silence_duration_ms / frame_duration_ms)
        continuous_timeout = ConfigManager.get_config_value('recording_options', 'continuous_timeout')
        recording_mode = recording_options.get('recording_mode') or 'continuous'

        initial_frames_to_skip = int(0.15 * self.sample_rate / frame_size)

        vad = None
        if recording_mode in ('voice_activity_detection', 'continuous'):
            vad = webrtcvad.Vad(2)
            speech_detected = False
            silent_frame_count = 0

        audio_buffer = deque(maxlen=frame_size)
        recording = []
        last_speech_time = time.time()  # Track when we last heard speech
        data_ready = Event()

        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}")
            audio_buffer.extend(indata[:, 0])
            data_ready.set()

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16',
                            blocksize=frame_size, device=recording_options.get('sound_device'),
                            callback=audio_callback):
            while self.is_running and self.is_recording:
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

                # Check for speech in the current frame
                if recording_mode == 'voice_activity_detection' or recording_mode == 'continuous':
                    if vad and vad.is_speech(frame.tobytes(), self.sample_rate):
                        last_speech_time = time.time()  # Update the last speech time
                        if recording_mode == 'continuous':
                            silent_frame_count = 0
                        if not speech_detected:
                            ConfigManager.console_print("Speech detected.")
                            speech_detected = True
                    else:
                        if recording_mode == 'continuous':  
                            silent_frame_count += 1

                # Check for continuous mode silence timeout
                if (recording_mode == 'continuous' and 
                    continuous_timeout > 0 and 
                    time.time() - last_speech_time > continuous_timeout):
                    ConfigManager.console_print(f"[DEBUG] No audio detected for {continuous_timeout} seconds. Stopping continuous recording.")
                    self.is_running = False  # Stop the entire thread
                    self.is_recording = False  # Stop recording
                    self.statusSignal.emit('idle', False)  # Update status window
                    return None  # Return None to skip transcription

                # Check for normal silence detection
                if recording_mode == 'voice_activity_detection' or recording_mode == 'continuous':
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