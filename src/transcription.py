import os
import tempfile
import wave
import numpy as np
import sounddevice as sd
import webrtcvad
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


"""
Record audio from the microphone and transcribe it using the OpenAI API.
Recording stops when the user stops speaking.
"""
def record_and_transcribe(status_queue, stop_recording_flag, config=None):
    sample_rate = 16000
    frame_duration = 30  # 30ms, supported values: 10, 20, 30
    buffer_duration = 300  # 300ms
    silence_duration = config['silence_duration'] if config else 700  # 700ms

    vad = webrtcvad.Vad(3)  # Aggressiveness mode: 3 (highest)
    buffer = []
    recording = []
    num_silent_frames = 0
    num_buffer_frames = buffer_duration // frame_duration
    num_silence_frames = silence_duration // frame_duration
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', blocksize=sample_rate * frame_duration // 1000,
                            callback=lambda indata, frames, time, status: buffer.extend(indata[:, 0])):
            while not stop_recording_flag():
                if len(buffer) < sample_rate * frame_duration // 1000:
                    continue

                frame = buffer[:sample_rate * frame_duration // 1000]
                buffer = buffer[sample_rate * frame_duration // 1000:]

                is_speech = vad.is_speech(np.array(frame).tobytes(), sample_rate)
                if is_speech:
                    recording.extend(frame)
                    num_silent_frames = 0
                else:
                    if len(recording) > 0:
                        num_silent_frames += 1

                    if num_silent_frames >= num_silence_frames:
                        break

        if stop_recording_flag():
            status_queue.put(('cancel', ''))
            return ''
        
        audio_data = np.array(recording, dtype=np.int16)
        print('Recording finished. Size:', audio_data.size)
        
        # Save the recorded audio as a temporary WAV file on disk
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_file:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes (16 bits) per sample
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())

        # Transcribe the temporary audio file using the OpenAI API
        with open(temp_audio_file.name, 'rb') as audio_file:
            status_queue.put(('transcribing', 'Transcribing...'))
            print('Transcribing audio file...')
            response = openai.Audio.transcribe('whisper-1', audio_file)

        # Remove the temporary audio file
        os.remove(temp_audio_file.name)

        result = response.get('text')
        print('Transcription:', result)
        status_queue.put(('idle', ''))
        
        return result.strip() if result else ''
            
    except Exception as e:
        print(f'Error: {e}')
        status_queue.put(('error', 'Error'))

