import os
from faster_whisper import WhisperModel
from openai import OpenAI
import torch


def create_local_model(config):
    """
    Create a local model using the faster-whisper library.
    """
    print('Creating local model...') if config['misc']['print_to_terminal'] else ''
    local_model_options = config['model_options']['local']
    compute_type = local_model_options['compute_type']
    device = local_model_options['device']
    model_path = local_model_options.get('model_path')

    try:
        if model_path:
            print(f'Loading model from: {model_path}') if config['misc']['print_to_terminal'] else ''
            model = WhisperModel(model_path,
                                 device=device,
                                 compute_type=compute_type,
                                 download_root=None)  # Prevent automatic download
        else:
            model = WhisperModel(local_model_options['model'],
                                 device=device,
                                 compute_type=compute_type)
    except Exception as e:
        print(f'Error initializing WhisperModel: {e}') if config['misc']['print_to_terminal'] else ''
        print('Falling back to CPU.') if config['misc']['print_to_terminal'] else ''
        model = WhisperModel(model_path or local_model_options['model'],
                             device='cpu',
                             compute_type=compute_type,
                             download_root=None if model_path else None)

    print('Local model created.') if config['misc']['print_to_terminal'] else ''
    return model

def transcribe_local(config, temp_audio_file, local_model=None):
    """
    Transcribe an audio file using a local model.
    """
    if not local_model:
        local_model = create_local_model(config)
    model_options = config['model_options']
    response = local_model.transcribe(audio=temp_audio_file,
                                        language=model_options['common']['language'],
                                        initial_prompt=model_options['common']['initial_prompt'],
                                        condition_on_previous_text=model_options['local']['condition_on_previous_text'],
                                        temperature=model_options['common']['temperature'],
                                        vad_filter=model_options['local']['vad_filter'],)
    return ''.join([segment.text for segment in list(response[0])])

def transcribe_api(config, temp_audio_file):
    """
    Transcribe an audio file using the OpenAI API.
    """
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY') or None,
        base_url=config['model_options']['api']['base_url'] or 'https://api.openai.com/v1'
    )
    model_options = config['model_options']
    with open(temp_audio_file, 'rb') as audio_file:
        response = client.audio.transcriptions.create(model=model_options['api']['model'], 
                                                        file=audio_file,
                                                        language=model_options['common']['language'],
                                                        prompt=model_options['common']['initial_prompt'],
                                                        temperature=model_options['common']['temperature'],)
    return response.text

def post_process_transcription(transcription, config=None):
    """
    Apply post-processing to the transcription.
    """
    transcription = transcription.strip()
    if config:
        if config['post_processing']['remove_trailing_period'] and transcription.endswith('.'):
            transcription = transcription[:-1]
        if config['post_processing']['add_trailing_space']:
            transcription += ' '
        if config['post_processing']['remove_capitalization']:
            transcription = transcription.lower()
    
    print('Post-processed transcription:', transcription) if config['misc']['print_to_terminal'] else ''
    return transcription

def transcribe(config, audio_file, local_model=None):
    """
    Transcribe an audio file using the OpenAI API or a local model, depending on config.
    """
    if not audio_file:
        return ''
    
    if config['model_options']['use_api']:
        transcription = transcribe_api(config, audio_file)
    elif not config['model_options']['use_api']:
        transcription = transcribe_local(config, audio_file, local_model)
    else:
        return ''
    
    print('Transcription:', transcription) if config['misc']['print_to_terminal'] else ''
    return post_process_transcription(transcription, config)
