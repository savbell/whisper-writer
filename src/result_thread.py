import time
import traceback
import numpy as np
import sounddevice as sd
import tempfile
import wave
import webrtcvad
from PyQt5.QtCore import QThread, QMutex, pyqtSignal

from transcription import transcribe


class ResultThread(QThread):
    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)

    def __init__(self, config, local_model=None):
        """
        Initialize the result thread.
        """
        super().__init__()
        self.config = config
        self.recording_mode = config['recording_options']['recording_mode']
        self.local_model = local_model
        self.is_recording = False
        self.is_running = True
        self.recording = []
        self.mutex = QMutex()

    def stop_recording(self):
        """
        Toggle recording off.
        """
        self.mutex.lock()
        self.is_recording = False
        self.mutex.unlock()

    def stop(self):
        """
        Stop the result thread.
        """
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.statusSignal.emit('idle')
        self.wait()

    def run(self):
        """
        Run the thread to record audio, transcribe it, and emit the result.
        """
        try:
            while self.is_running:
                if not self.is_running:
                    break
                
                self.is_recording = True
                self.statusSignal.emit('recording')
                print('Recording...') if self.config['misc']['print_to_terminal'] else ''
                audio_file = self.record()
            
                if not self.is_running:
                    break
                
                self.statusSignal.emit('transcribing')
                print('Transcribing...') if self.config['misc']['print_to_terminal'] else ''
                
                result = transcribe(self.config, audio_file, self.local_model)
                
                if not self.is_running:
                    break
                
                self.statusSignal.emit('idle')
                self.resultSignal.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit('error')
            self.resultSignal.emit('')
        finally:
            self.stop_recording()
    
    def record(self):
        """
        Record audio from the microphone (sound_device). Recording stops when the activation_key is pressed (press_to_toggle),
        released (hold_to_record), or after silence_duration (continuous or voice_activity_detection).
        """
        sound_device = self.config['recording_options']['sound_device'] or None
        sample_rate = self.config['recording_options']['sample_rate'] or 16000
        frame_duration = 30  # 30ms, supported values: 10, 20, 30
        buffer_duration = 300  # 300ms
        silence_duration = self.config['recording_options']['silence_duration'] or 900
        recording_mode = self.config['recording_options']['recording_mode'] or 'voice_activity_detection'

        vad = webrtcvad.Vad(2)  # Aggressiveness mode
        buffer = []
        self.recording = []
        num_silent_frames = 0
        num_buffer_frames = buffer_duration // frame_duration
        num_silence_frames = silence_duration // frame_duration
        
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', blocksize=sample_rate * frame_duration // 1000,
                            device=sound_device, callback=lambda indata, frames, time, status: buffer.extend(indata[:, 0])):
            # Short delay to allow the buffer to fill
            time.sleep(0.5)
        
            while self.is_running:
                self.mutex.lock()
                current_recording_state = self.is_recording
                self.mutex.unlock()
                
                if not current_recording_state:
                    break
                
                if len(buffer) < sample_rate * frame_duration // 1000:
                    continue

                frame = buffer[:sample_rate * frame_duration // 1000]
                buffer = buffer[sample_rate * frame_duration // 1000:]
                
                if recording_mode in ('voice_activity_detection', 'continuous'):
                    is_speech = vad.is_speech(np.array(frame).tobytes(), sample_rate)
                    if is_speech:
                        self.recording.extend(frame)
                        num_silent_frames = 0
                    else:
                        if len(self.recording) > 0:
                            num_silent_frames += 1
                        if num_silent_frames >= num_silence_frames:
                            self.mutex.lock()
                            self.is_recording = False
                            self.mutex.unlock()
                            break
                else:
                    self.recording.extend(frame)
        
        audio_data = np.array(self.recording, dtype=np.int16)
        print('Recording finished. Size:', audio_data.size) if self.config['misc']['print_to_terminal'] else ''
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_file:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes (16 bits) per sample
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
                
        print(temp_audio_file.name) if self.config['misc']['print_to_terminal'] else ''
        return temp_audio_file.name