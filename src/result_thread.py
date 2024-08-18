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
from input_simulation import InputSimulator
from utils import ConfigManager


class ResultThread(QThread):
    """
    A thread class for handling audio recording, transcription, and result processing.

    This class manages the entire process of:
    1. Recording audio from the microphone
    2. Detecting speech and silence
    3. Saving the recorded audio to a file
    4. Transcribing the audio
    5. Emitting the transcription result

    It uses WebRTC VAD (Voice Activity Detection) for efficient speech detection
    and supports different recording modes like continuous recording and
    voice activity detection.

    Signals:
        statusSignal: Emits the current status of the thread (e.g., 'recording', 'transcribing', 'idle')
        resultSignal: Emits the transcription result
    """

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)

    def __init__(self, local_model=None):
        """
        Initialize the ResultThread.

        :param local_model: Local transcription model (if applicable)
        """
        super().__init__()
        self.local_model = local_model
        self.is_recording = False
        self.is_running = True
        self.mutex = QMutex()
        self.input_simulator = InputSimulator()

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
        self.statusSignal.emit('idle')
        self.wait()

    def run(self):
        """Main execution method for the thread."""
        try:
            if not self.is_running:
                return

            self.mutex.lock()
            self.is_recording = True
            self.mutex.unlock()

            self.statusSignal.emit('recording')
            ConfigManager.console_print('Recording...')
            audio_file = self._record_audio()

            if not self.is_running:
                return

            if not audio_file:
                self.statusSignal.emit('idle')
                return

            self.statusSignal.emit('transcribing')
            ConfigManager.console_print('Transcribing...')

            # Time the transcription process
            start_time = time.time()
            result = transcribe(audio_file, self.local_model)
            end_time = time.time()

            transcription_time = end_time - start_time
            ConfigManager.console_print(f'Transcription completed in {transcription_time:.2f} seconds. Post-processed line: {result}')

            if not self.is_running:
                return

            self.statusSignal.emit('idle')
            self.resultSignal.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit('error')
            self.resultSignal.emit('')
        finally:
            self.stop_recording()

    def _record_audio(self):
        """
        Record audio from the microphone and save it to a temporary file.

        :return: Path to the saved audio file
        """
        recording_options = ConfigManager.get_config_section('recording_options')
        sample_rate = recording_options.get('sample_rate') or 16000
        frame_duration_ms = 30  # 30ms frame duration for WebRTC VAD
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get('silence_duration') or 900
        silence_frames = int(silence_duration_ms / frame_duration_ms)
        # 300ms delay before starting VAD to avoid mistaking the sound of key pressing for voice
        initial_delay = 0.3

        vad = webrtcvad.Vad(2)  # VAD aggressiveness (0-3, 3 being the most aggressive)

        audio_buffer = deque(maxlen=frame_size)
        recording = []
        silent_frame_count = 0
        data_ready = Event()
        recording_started = False
        start_time = time.time()

        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}")
            audio_buffer.extend(indata[:, 0])
            data_ready.set()

        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16',
                            blocksize=frame_size, device=recording_options.get('sound_device'),
                            callback=audio_callback):
            while self.is_running and self.is_recording:
                data_ready.wait()
                data_ready.clear()

                if len(audio_buffer) >= frame_size:
                    frame = np.array(list(audio_buffer), dtype=np.int16)
                    audio_buffer.clear()

                    if not recording_started:
                        if time.time() - start_time < initial_delay:
                            continue
                        else:
                            recording_started = True # Initial delay passed; processing will start now

                    should_stop, silent_frame_count = self._process_audio_frame(
                        frame, vad, sample_rate, recording, silent_frame_count, silence_frames
                    )
                    if should_stop:
                        break

        return self._save_audio_to_file(recording, sample_rate)

    def _process_audio_frame(self, frame, vad, sample_rate, recording, silent_frame_count, silence_frames):
        """
        Process a single audio frame.

        :param frame: The audio frame to process
        :param vad: The WebRTC VAD instance
        :param sample_rate: The audio sample rate
        :param recording: The list to store recorded audio
        :param silent_frame_count: The count of consecutive silent frames
        :param silence_frames: The number of silent frames to trigger stop
        :return: Tuple (should_stop, updated_silent_frame_count)
        """
        recording_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
        if recording_mode in ('voice_activity_detection', 'continuous'):
            is_speech = vad.is_speech(frame.tobytes(), sample_rate)
            if is_speech:
                if not recording:
                    ConfigManager.console_print("Speech detected, starting recording...")
                recording.extend(frame)
                silent_frame_count = 0
            elif recording:
                recording.extend(frame)
                silent_frame_count += 1
            else:
                # If no speech detected and not recording, don't increment silent_frame_count
                pass
        else:
            recording.extend(frame)

        should_stop = silent_frame_count >= silence_frames and recording
        return should_stop, silent_frame_count

    def _save_audio_to_file(self, recording, sample_rate):
        """
        Save the recorded audio to a temporary WAV file.

        :param recording: The list of recorded audio frames
        :param sample_rate: The audio sample rate
        :return: Path to the saved audio file
        """
        audio_data = np.array(recording, dtype=np.int16)
        duration = len(audio_data) / sample_rate

        ConfigManager.console_print(f'Recording finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds')

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_file:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes per sample (16-bit audio)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())

        ConfigManager.console_print(f'Audio saved to: {temp_audio_file.name}')
        return temp_audio_file.name
