import traceback
import numpy as np
import sounddevice as sd
import tempfile
import wave
import webrtcvad
import time
from PyQt5.QtCore import QThread, pyqtSignal, QMutex

class ResultThread(QThread):
    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.recording_mode = config['recording_options']['recording_mode']
        self.is_recording = False
        self.mutex = QMutex()

    def activation_key_pressed(self):
        print("Activation key pressed")
        self.mutex.lock()
        try:
            if self.recording_mode == 'press_to_toggle' and self.is_recording:
                self.is_recording = False
            elif not self.is_recording:
                self.is_recording = True
                self.start()
        finally:
            self.mutex.unlock()

    def activation_key_released(self):
        print("Activation key released")
        self.mutex.lock()
        try:
            if self.recording_mode == 'hold_to_record' and self.is_recording:
                self.is_recording = False
        finally:
            self.mutex.unlock()

    def run(self):
        try:
            self.statusSignal.emit('recording')
            print('Recording...') if self.config['misc']['print_to_terminal'] else ''
            audio_file = self.record()
        
            self.statusSignal.emit('transcribing')
            print('Transcribing...') if self.config['misc']['print_to_terminal'] else ''
            time.sleep(2)  # Simulate transcription duration
            
            self.resultSignal.emit(audio_file)
            self.statusSignal.emit('idle')
        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit('error')
            self.resultSignal.emit('')
        
    def record(self):
        sound_device = self.config['recording_options']['sound_device'] or None
        sample_rate = self.config['recording_options']['sample_rate'] or 16000
        frame_duration = 30  # 30ms, supported values: 10, 20, 30
        buffer_duration = 300  # 300ms
        silence_duration = self.config['recording_options']['silence_duration'] or 900
        recording_mode = self.config['recording_options']['recording_mode'] or 'voice_activity_detection'

        vad = webrtcvad.Vad(3)  # Aggressiveness mode: 3 (highest)
        buffer = []
        recording = []
        num_silent_frames = 0
        num_buffer_frames = buffer_duration // frame_duration
        num_silence_frames = silence_duration // frame_duration
        
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', blocksize=sample_rate * frame_duration // 1000,
                            device=sound_device, callback=lambda indata, frames, time, status: buffer.extend(indata[:, 0])):
            while True:
                self.mutex.lock()
                current_recording_state = self.is_recording
                self.mutex.unlock()
                
                if not current_recording_state:
                    break
                
                if len(buffer) < sample_rate * frame_duration // 1000:
                    continue

                frame = buffer[:sample_rate * frame_duration // 1000]
                buffer = buffer[sample_rate * frame_duration // 1000:]
                
                if recording_mode == 'voice_activity_detection':
                    is_speech = vad.is_speech(np.array(frame).tobytes(), sample_rate)
                    if is_speech:
                        recording.extend(frame)
                        num_silent_frames = 0
                    else:
                        if len(recording) > 0:
                            num_silent_frames += 1
                        if num_silent_frames >= num_silence_frames:
                            self.mutex.lock()
                            self.is_recording = False
                            self.mutex.unlock()
                            break
                else:
                    recording.extend(frame)
        
        audio_data = np.array(recording, dtype=np.int16)
        print('Recording finished. Size:', audio_data.size) if self.config['misc']['print_to_terminal'] else ''
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_file:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes (16 bits) per sample
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
                
        print(temp_audio_file.name) if self.config['misc']['print_to_terminal'] else ''
        return temp_audio_file.name
