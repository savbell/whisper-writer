import io
import os
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel, BatchedInferencePipeline
from openai import OpenAI

from utils import ConfigManager

def create_local_model():
    """
    Create a local model using the faster-whisper library.
    """
    ConfigManager.console_print('Creating local model...')
    local_model_options = ConfigManager.get_config_section('model_options')['local']
    compute_type = local_model_options['compute_type']
    model_path = local_model_options.get('model_path')
    batch_size = local_model_options.get('batch_size', 1)

    if compute_type == 'int8':
        device = 'cpu'
        ConfigManager.console_print('Using int8 quantization, forcing CPU usage.')
    else:
        device = local_model_options['device']

    try:
        if model_path:
            ConfigManager.console_print(f'Loading model from: {model_path}')
            model = WhisperModel(model_path,
                                 device=device,
                                 compute_type=compute_type,
                                 download_root=None)  # Prevent automatic download
        else:
            model = WhisperModel(local_model_options['model'],
                                 device=device,
                                 compute_type=compute_type)
    except Exception as e:
        ConfigManager.console_print(f'Error initializing WhisperModel: {e}')
        ConfigManager.console_print('Falling back to CPU.')
        model = WhisperModel(model_path or local_model_options['model'],
                             device='cpu',
                             compute_type=compute_type,
                             download_root=None if model_path else None)

    ConfigManager.console_print('Local model created.')
    
    # Create batched pipeline if batch_size > 1 for better performance
    if batch_size > 1:
        ConfigManager.console_print(f'Using batched inference with batch_size={batch_size}')
        return BatchedInferencePipeline(model=model, batch_size=batch_size)
    
    return model

def transcribe_local(audio_data, local_model=None):
    """
    Transcribe an audio file using a local model.
    """
    if not local_model:
        local_model = create_local_model()
    model_options = ConfigManager.get_config_section('model_options')

    # Convert int16 to float32
    audio_data_float = audio_data.astype(np.float32) / 32768.0

    try:
        # Check if using batched pipeline or regular model
        if isinstance(local_model, BatchedInferencePipeline):
            response = local_model.transcribe(audio=audio_data_float,
                                            language=model_options['common']['language'],
                                            initial_prompt=model_options['common']['initial_prompt'],
                                            condition_on_previous_text=model_options['local']['condition_on_previous_text'],
                                            temperature=model_options['common']['temperature'],
                                            vad_filter=model_options['local']['vad_filter'])
        else:
            response = local_model.transcribe(audio=audio_data_float,
                                            language=model_options['common']['language'],
                                            initial_prompt=model_options['common']['initial_prompt'],
                                            condition_on_previous_text=model_options['local']['condition_on_previous_text'],
                                            temperature=model_options['common']['temperature'],
                                            vad_filter=model_options['local']['vad_filter'])
    except Exception as e:
        ConfigManager.console_print(f'Error during transcription: {e}')
        # Fallback to basic transcription without extra parameters
        response = local_model.transcribe(audio=audio_data_float)
    
    return ''.join([segment.text for segment in list(response[0])])

def transcribe_api(audio_data):
    """
    Transcribe an audio file using the OpenAI API.
    """
    model_options = ConfigManager.get_config_section('model_options')
    
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY') or None,
            base_url=model_options['api']['base_url'] or 'https://api.openai.com/v1'
        )

        # Convert numpy array to WAV file
        byte_io = io.BytesIO()
        sample_rate = ConfigManager.get_config_section('recording_options').get('sample_rate') or 16000
        sf.write(byte_io, audio_data, sample_rate, format='wav')
        byte_io.seek(0)

        response = client.audio.transcriptions.create(
            model=model_options['api']['model'],
            file=('audio.wav', byte_io, 'audio/wav'),
            language=model_options['common']['language'],
            prompt=model_options['common']['initial_prompt'],
            temperature=model_options['common']['temperature'],
        )
        return response.text
    except Exception as e:
        ConfigManager.console_print(f'Error during API transcription: {e}')
        # Return empty string on API failure
        return ''

def post_process_transcription(transcription):
    """
    Post-process the transcription based on the user's settings.
    """
    post_processing_options = ConfigManager.get_config_section('post_processing')

    if post_processing_options['remove_trailing_period'] and transcription.endswith('.'):
        transcription = transcription[:-1]

    if post_processing_options['remove_capitalization']:
        transcription = transcription.lower()

    if post_processing_options['add_trailing_space']:
        transcription += ' '

    return transcription


def transcribe(audio_data, local_model=None):
    """
    Transcribe audio date using the OpenAI API or a local model, depending on config.
    """
    if audio_data is None:
        return ''

    if ConfigManager.get_config_value('model_options', 'use_api'):
        transcription = transcribe_api(audio_data)
    else:
        transcription = transcribe_local(audio_data, local_model)

    return post_process_transcription(transcription)

