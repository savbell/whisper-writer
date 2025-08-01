import time
import traceback
import numpy as np
import sounddevice as sd
import tempfile
import wave
from PyQt5.QtCore import QThread, QMutex, pyqtSignal
from collections import deque
from threading import Event

from transcription import transcribe
from utils import ConfigManager
from cost_tracker import CostTracker

# Initialize cost tracker
cost_tracker = CostTracker()

# Try to import webrtcvad, but don't fail if it's not available
try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    WEBRTCVAD_AVAILABLE = False
    ConfigManager.console_print("webrtcvad not available, falling back to continuous recording mode")

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

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    wordSignal = pyqtSignal(str)  # Signal for word-by-word updates
    metricsUpdated = pyqtSignal(float, int, float, float, float)  # duration, tokens, total_cost, whisper_cost, gpt_cost

    def __init__(self, local_model=None, main_window=None):
        """
        Initialize the ResultThread.

        :param local_model: Local transcription model (if applicable)
        :param main_window: Reference to main window for updating metrics
        """
        super().__init__()
        self.local_model = local_model
        self.main_window = main_window
        self.is_recording = False
        self.is_running = True
        self.sample_rate = None
        self.mutex = QMutex()

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
            audio_data = self._record_audio()

            if not self.is_running:
                return

            if audio_data is None:
                self.statusSignal.emit('idle')
                return

            self.statusSignal.emit('transcribing')
            ConfigManager.console_print('Transcribing...')

            # Get initial metrics
            initial_summary = cost_tracker.get_usage_summary()
            initial_whisper_duration = initial_summary['whisper_usage']['total_duration_seconds'] if initial_summary else 0
            initial_gpt_tokens = (initial_summary['gpt_usage']['total_input_tokens'] + 
                                initial_summary['gpt_usage']['total_output_tokens']) if initial_summary else 0
            initial_cost = initial_summary['total_cost'] if initial_summary else 0

            # Time the transcription process
            # Clear word display
            self.wordSignal.emit("")  # Signal to clear display
            
            # Transcribe with word callback
            start_time = time.time()
            result = transcribe(audio_data, self.local_model,
                              lambda word: self.wordSignal.emit(word))
            end_time = time.time()

            # Get updated metrics
            current_summary = cost_tracker.get_usage_summary()
            if current_summary:
                # Calculate differences
                whisper_duration = current_summary['whisper_usage']['total_duration_seconds'] - initial_whisper_duration
                gpt_tokens = ((current_summary['gpt_usage']['total_input_tokens'] +
                              current_summary['gpt_usage']['total_output_tokens']) - initial_gpt_tokens)
                total_cost = current_summary['total_cost'] - initial_cost
                
                # Get per-request costs from last entries
                whisper_cost = current_summary['last_whisper_entry']['cost'] if current_summary['last_whisper_entry'] else None
                gpt_cost = current_summary['last_gpt_entry']['total_cost'] if current_summary['last_gpt_entry'] else None
                
                # Log the costs for debugging
                if whisper_cost:
                    ConfigManager.console_print(f"Last Whisper request cost: ${whisper_cost:.4f}")
                if gpt_cost:
                    ConfigManager.console_print(f"Last GPT request cost: ${gpt_cost:.4f}")
                
                # Emit metrics update with per-request costs
                self.metricsUpdated.emit(whisper_duration, gpt_tokens, total_cost, whisper_cost, gpt_cost)

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

        :return: numpy array of audio data, or None if the recording is too short
        """
        recording_options = ConfigManager.get_config_section('recording_options')
        self.sample_rate = recording_options.get('sample_rate') or 16000
        frame_duration_ms = 30  # 30ms frame duration for WebRTC VAD
        frame_size = int(self.sample_rate * (frame_duration_ms / 1000.0))
        # Increased silence duration to give more time for slower microphones
        silence_duration_ms = recording_options.get('silence_duration') or 1200
        silence_frames = int(silence_duration_ms / frame_duration_ms)

        # 300ms delay before starting VAD to avoid mistaking the sound of key pressing for voice
        # and give microphone time to properly initialize
        initial_frames_to_skip = int(0.3 * self.sample_rate / frame_size)

        # Create VAD only for recording modes that use it and if webrtcvad is available
        recording_mode = recording_options.get('recording_mode') or 'continuous'
        vad = None
        if WEBRTCVAD_AVAILABLE and recording_mode in ('voice_activity_detection', 'continuous'):
            try:
                vad = webrtcvad.Vad(1)  # Reduced VAD aggressiveness for better handling of quiet speech
                speech_detected = False
                silent_frame_count = 0
                speech_frame_count = 0  # Track consecutive speech frames
                min_speech_frames = 3    # Minimum consecutive speech frames to confirm speech
            except Exception as e:
                ConfigManager.console_print(f"Error initializing VAD: {str(e)}")
                vad = None

        audio_buffer = deque(maxlen=frame_size)
        recording = []

        data_ready = Event()

        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}")
            audio_buffer.extend(indata[:, 0])
            data_ready.set()

        # Get default input device
        try:
            default_device = sd.query_devices(kind='input')
            device_id = default_device['index']
        except Exception as e:
            ConfigManager.console_print(f"Error getting default device: {str(e)}")
            device_id = None

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16',
                           blocksize=frame_size, device=device_id,
                           callback=audio_callback):
            while self.is_running and self.is_recording:
                # Use a short timeout to check stop condition more frequently
                if not data_ready.wait(timeout=0.01):  # 10ms timeout
                    continue
                data_ready.clear()

                if not self.is_recording:  # Check again after wait
                    break

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

                if not self.is_recording:  # Quick exit if recording stopped
                    break

                if vad:
                    try:
                        is_speech = vad.is_speech(frame.tobytes(), self.sample_rate)
                        
                        if is_speech:
                            speech_frame_count += 1
                            silent_frame_count = 0
                            
                            # Only set speech_detected after enough consecutive speech frames
                            if speech_frame_count >= min_speech_frames and not speech_detected:
                                ConfigManager.console_print("Speech detected.")
                                speech_detected = True
                        else:
                            speech_frame_count = 0
                            if speech_detected:
                                silent_frame_count += 1

                        # Stop recording if either stop condition is met
                        if (speech_detected and silent_frame_count > silence_frames) or not self.is_recording:
                            break
                    except Exception as e:
                        ConfigManager.console_print(f"Error in VAD processing: {str(e)}")
                        # If VAD fails, continue recording without it
                        vad = None

        audio_data = np.array(recording, dtype=np.int16)
        duration = len(audio_data) / self.sample_rate

        ConfigManager.console_print(f'Recording finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds')

        min_duration_ms = recording_options.get('min_duration') or 100

        if (duration * 1000) < min_duration_ms:
            ConfigManager.console_print(f'Discarded due to being too short.')
            return None

        return audio_data
