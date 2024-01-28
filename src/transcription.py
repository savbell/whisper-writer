import traceback
import numpy as np
import openai
import os
import sounddevice as sd
import tempfile
import wave
import webrtcvad
from dotenv import load_dotenv
from faster_whisper import WhisperModel
import keyboard
import torch


"""
Create a local model using the faster_whisper library.
"""
def create_local_model(config):
    if torch.cuda.is_available() and config['local_model_options']['device'] != 'cpu':
        try:
            model = WhisperModel(config['local_model_options']['model'],
                                 device=config['local_model_options']['device'],
                                 compute_type=config['local_model_options']['compute_type'])
        except Exception as e:
            print(f'Error initializing WhisperModel with CUDA: {e}') if config['print_to_terminal'] else ''
            print('Falling back to CPU.') if config['print_to_terminal'] else ''
            model = WhisperModel(config['local_model_options']['model'], 
                                 device='cpu',
                                 compute_type=config['local_model_options']['compute_type'])
    else:
        print('CUDA not available, using CPU.') if config['print_to_terminal'] else ''
        model = WhisperModel(config['local_model_options']['model'], 
                             device='cpu',
                             compute_type=config['local_model_options']['compute_type'])
    
    return model

"""
Transcribe an audio file using a local model.
"""
def transcribe_local(config, temp_audio_file, local_model=None):
    if not local_model:
        print('Creating local model...') if config['print_to_terminal'] else ''
        local_model = create_local_model(config)
        print('Local model created.') if config['print_to_terminal'] else ''
    model_options = config['local_model_options']
    response = local_model.transcribe(audio=temp_audio_file,
                                        language=model_options['language'],
                                        initial_prompt=model_options['initial_prompt'],
                                        condition_on_previous_text=model_options['condition_on_previous_text'],
                                        temperature=model_options['temperature'],
                                        vad_filter=model_options['vad_filter'],)
    return ''.join([segment.text for segment in list(response[0])])

"""
Transcribe an audio file using the OpenAI API.
"""
def transcribe_api(config, temp_audio_file):
    if load_dotenv():
        openai.api_key = os.getenv('OPENAI_API_KEY')
    api_options = config['api_options']
    with open(temp_audio_file, 'rb') as audio_file:
        response = openai.Audio.transcribe(model=api_options['model'], 
                                            file=audio_file,
                                            language=api_options['language'],
                                            prompt=api_options['initial_prompt'],
                                            temperature=api_options['temperature'],)
    return response.get('text')

"""
Record audio from the microphone (sound_device).
If push_to_talk is True, the user must hold down the activation_key to record. Otherwise, recording will stop when the user stops speaking.
"""
def record(status_queue, cancel_flag, config):
    sound_device = config['sound_device'] if config else None
    sample_rate = config['sample_rate'] if config else 16000  # 16kHz, supported values: 8kHz, 16kHz, 32kHz, 48kHz, 96kHz
    frame_duration = 30  # 30ms, supported values: 10, 20, 30
    buffer_duration = 300  # 300ms
    silence_duration = config['silence_duration'] if config else 900  # 900ms

    recording_mode = config['recording_mode']
    activation_key = config['activation_key']

    vad = webrtcvad.Vad(3)  # Aggressiveness mode: 3 (highest)
    buffer = []
    recording = []
    num_silent_frames = 0
    num_buffer_frames = buffer_duration // frame_duration
    num_silence_frames = silence_duration // frame_duration
    try:
        print('Recording...') if config['print_to_terminal'] else ''
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', blocksize=sample_rate * frame_duration // 1000,
                            device=sound_device, callback=lambda indata, frames, time, status: buffer.extend(indata[:, 0])):
            while not cancel_flag():
                if len(buffer) < sample_rate * frame_duration // 1000:
                    continue

                frame = buffer[:sample_rate * frame_duration // 1000]
                buffer = buffer[sample_rate * frame_duration // 1000:]
                
                if not cancel_flag():
                    if recording_mode == 'press_to_toggle':
                        if len(recording) > 0 and keyboard.is_pressed(activation_key):
                            break
                        else:
                            recording.extend(frame)
                    if recording_mode == 'hold_to_record':
                        if keyboard.is_pressed(activation_key):
                            recording.extend(frame)
                        else:
                            break
                    elif recording_mode == 'voice_activity_detection':
                        is_speech = vad.is_speech(np.array(frame).tobytes(), sample_rate)
                        if is_speech:
                            recording.extend(frame)
                            num_silent_frames = 0
                        else:
                            if len(recording) > 0:
                                num_silent_frames += 1
                            if num_silent_frames >= num_silence_frames:
                                break

        if cancel_flag():
            status_queue.put(('cancel', ''))
            return ''
        
        audio_data = np.array(recording, dtype=np.int16)
        print('Recording finished. Size:', audio_data.size) if config['print_to_terminal'] else ''
        
        # Save the recorded audio as a temporary WAV file on disk
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio_file:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes (16 bits) per sample
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
                
        return temp_audio_file.name
    
    except Exception as e:
        traceback.print_exc()
        status_queue.put(('error', 'Error'))
        return ''  

"""
Apply post-processing to the transcription.
"""
def post_process_transcription(transcription, config=None):
    transcription = transcription.strip()
    if config:
        if config['remove_trailing_period'] and transcription.endswith('.'):
            transcription = transcription[:-1]
        if config['add_trailing_space']:
            transcription += ' '
        if config['remove_capitalization']:
            transcription = transcription.lower()
    
    print('Post-processed transcription:', transcription) if config['print_to_terminal'] else ''
    return transcription

"""
Transcribe an audio file using the OpenAI API or a local model, depending on config.
"""
def transcribe(status_queue, cancel_flag, config, audio_file, local_model=None):
    if not audio_file:
        return ''
    
    status_queue.put(('transcribing', 'Transcribing...'))
    print('Transcribing audio file...') if config['print_to_terminal'] else ''
    
    # If configured, transcribe the temporary audio file using the OpenAI API
    if config['use_api']:
        transcription = transcribe_api(config, audio_file)
        
    # Otherwise, transcribe the temporary audio file using a local model
    elif not config['use_api']:
        transcription = transcribe_local(config, audio_file, local_model)
        
    else:
        return ''
    
    print('Transcription:', transcription) if config['print_to_terminal'] else ''
    return post_process_transcription(transcription, config)

"""
Record audio from the microphone and transcribe it using the OpenAI API or a local model, depending on config.
"""
def record_and_transcribe(status_queue, cancel_flag, config, local_model=None):
    audio_file = record(status_queue, cancel_flag, config)
    if cancel_flag():
        return ''
    result = transcribe(status_queue, cancel_flag, config, audio_file, local_model)
    return result
