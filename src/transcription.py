import io
import os
import re
import numpy as np
import soundfile as sf
import tiktoken
from faster_whisper import WhisperModel
from openai import OpenAI

from utils import ConfigManager
from cost_tracker import CostTracker

# Initialize the cost tracker
cost_tracker = CostTracker()

# Store detected language globally
detected_language = 'en'

def create_local_model():
    """
    Create a local model using the faster-whisper library.
    """
    ConfigManager.console_print('Creating local model...')
    local_model_options = ConfigManager.get_config_section('model_options')['local']
    compute_type = local_model_options['compute_type']
    model_path = local_model_options.get('model_path')

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
    return model

def transcribe_local(audio_data, local_model=None, word_callback=None):
    """
    Transcribe an audio file using a local model.
    
    Args:
        audio_data: Audio data to transcribe
        local_model: Optional pre-initialized model
        word_callback: Optional callback function for word-by-word updates
    """
    if not local_model:
        local_model = create_local_model()
    model_options = ConfigManager.get_config_section('model_options')

    # Convert int16 to float32
    audio_data_float = audio_data.astype(np.float32) / 32768.0

    response = local_model.transcribe(audio=audio_data_float,
                                      language=model_options['common']['language'],
                                      initial_prompt=model_options['common']['initial_prompt'],
                                      condition_on_previous_text=model_options['local']['condition_on_previous_text'],
                                      temperature=model_options['common']['temperature'],
                                      vad_filter=model_options['local']['vad_filter'],)
    
    # Process segments and emit words
    text = ""
    for segment in response[0]:
        words = segment.text.strip().split()
        for word in words:
            if word_callback:
                word_callback(word)
        text += segment.text
    
    return text

def transcribe_api(audio_data, word_callback=None):
    """
    Transcribe an audio file using the OpenAI API.
    
    Args:
        audio_data: Audio data to transcribe
        word_callback: Optional callback function for word-by-word updates
        
    Note:
        OpenAI has a 25MB file size limit. This function will automatically
        check and warn if the audio file approaches this limit.
    """
    # Check estimated file size (assuming 16-bit audio at 16kHz)
    estimated_size_mb = (len(audio_data) * 2) / (1024 * 1024)  # Convert bytes to MB
    if estimated_size_mb > 23:  # Use 23MB as safety margin
        ConfigManager.console_print(f"Warning: Audio file size ({estimated_size_mb:.1f}MB) is approaching OpenAI's 25MB limit.")
        return "Error: Recording too long. Please try a shorter recording."
    global detected_language
    model_options = ConfigManager.get_config_section('model_options')
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY') or None,
        base_url=model_options['api']['base_url'] or 'https://api.openai.com/v1'
    )

    # Get sample rate from config
    sample_rate = ConfigManager.get_config_section('recording_options').get('sample_rate') or 16000

    # Create a temporary file for the audio
    import tempfile
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
    try:
        # Convert to float32 for soundfile
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Write the audio data to the temporary file
        sf.write(temp_file.name, audio_float, sample_rate, format='mp3')
        temp_file.close()  # Close the file before reopening
        
        # Calculate audio duration
        duration_seconds = len(audio_data) / sample_rate
        
        # Handle language setting
        language = None  # Always let Whisper auto-detect
        ConfigManager.console_print("Using Whisper's automatic language detection")
        
        # Reopen the file in binary read mode for actual transcription
        with open(temp_file.name, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model=model_options['api']['model'],
                file=audio_file,
                prompt=model_options['common']['initial_prompt'],
                temperature=model_options['common']['temperature'],
            )
            
            # Get detected language from response
            global detected_language
            detected_language = getattr(response, 'language', 'en')
            ConfigManager.console_print(f"Whisper detected language: {detected_language}")
            
            # Process response text word by word
            if word_callback:
                words = response.text.strip().split()
                for word in words:
                    word_callback(word)
            
            # Log Whisper API usage
            whisper_cost = cost_tracker.log_whisper_usage(
                duration_seconds=duration_seconds,
                model=model_options['api']['model']
            )
            ConfigManager.console_print(f"Whisper API cost: ${whisper_cost:.4f}")
            
    finally:
        # Make sure the file is closed
        if not temp_file.closed:
            temp_file.close()
        # Clean up the temporary file
        try:
            os.unlink(temp_file.name)
        except PermissionError:
            pass  # Ignore if file is still in use
            
    return response.text

def enhance_transcription(text):
    """
    Use GPT-4 to enhance and correct the transcription.
    """
    global detected_language
    post_processing = ConfigManager.get_config_section('post_processing')
    if not post_processing.get('enhance_with_gpt', True):
        return text

    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY') or None,
        base_url=ConfigManager.get_config_value('model_options', 'api', 'base_url') or 'https://api.openai.com/v1'
    )
    
    try:
        ConfigManager.console_print("Enhancing transcription with GPT...")
        
        # Create language-specific instructions
        # Get the language of the original text
        original_lang = detected_language
        
        # Create language-specific instructions
        lang_instructions = {
            'da': """
                Special Danish instructions:
                - Preserve Danish grammar and word order
                - Keep Danish-specific characters (æ, ø, å)
                - Maintain Danish expressions and idioms
                - Do not translate to English
                - Keep informal/formal tone as in original
                - Preserve Danish interjections (sgu, jo, vel, etc.)
                - Add proper Danish commas according to these rules:
                    * Before subordinate clauses (at, som, der, hvis, når, etc.)
                    * Between main clauses joined by og, eller, men
                    * Before and after parenthetical expressions
                    * Before infinitive markers (at + verb)
                    * After introductory phrases
                - Fix Danish sentence structure while maintaining natural flow
                - Ensure proper spacing around punctuation marks
                - Handle Danish quotation marks correctly („")
            """,
            'en': """
                Special English instructions:
                - Maintain English grammar and style
                - Do not translate to other languages
                - Keep original English expressions and idioms
                - Preserve English sentence structure
                - Use English punctuation rules
            """,
            # Add other languages as needed
        }
        
        system_prompt = f"""You are a transcription enhancement expert. Your task is to:
        1. Fix any obvious speech-to-text errors
        2. Add proper punctuation and capitalization
        3. Maintain the original meaning and intent
        4. Keep the text natural and conversational
        5. Only make changes when there's high confidence they're correct
        6. Preserve technical terms and proper nouns exactly as spoken
        7. IMPORTANT: DO NOT TRANSLATE - keep the text in its original language
        8. For Danish text, follow these comma rules strictly:
           - Place commas before subordinate clauses (at, som, der, hvis, når, etc.)
           - Place commas between main clauses joined by og, eller, men
           - Place commas before and after parenthetical expressions
           - Place commas before infinitive markers (at + verb)
           - Place commas after introductory phrases
        
        {lang_instructions.get(detected_language, "Maintain original language and style.")}"""
        
        user_prompt = f"Please enhance this transcription while maintaining its original language and meaning: {text}"
        
        # Get accurate token counts using tiktoken
        model = post_processing.get('gpt_model', 'gpt-4o-2024-08-06')
        enc = tiktoken.encoding_for_model(model)
        input_tokens = len(enc.encode(system_prompt)) + len(enc.encode(user_prompt))
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=post_processing.get('enhancement_temperature', 0.3)
        )
        
        enhanced_text = response.choices[0].message.content.strip()
        output_tokens = len(enc.encode(enhanced_text))
        
        # Log GPT API usage with accurate token counts
        gpt_cost = cost_tracker.log_gpt_usage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            original_text=text,
            enhanced_text=enhanced_text
        )
        
        ConfigManager.console_print(f"Original: {text}")
        ConfigManager.console_print(f"Enhanced: {enhanced_text}")
        ConfigManager.console_print(f"Token usage - Input: {input_tokens}, Output: {output_tokens}")
        ConfigManager.console_print(f"GPT API cost: ${gpt_cost:.4f}")
        
        return enhanced_text
    except Exception as e:
        ConfigManager.console_print(f"Transcription enhancement failed: {str(e)}")
        return text  # Return original text if enhancement fails

def post_process_transcription(transcription):
    """
    Apply post-processing to the transcription.
    """
    # First enhance the transcription with GPT-4
    transcription = enhance_transcription(transcription)
    
    # Then apply basic formatting rules
    transcription = transcription.strip()
    post_processing = ConfigManager.get_config_section('post_processing')
    if post_processing['remove_trailing_period'] and transcription.endswith('.'):
        transcription = transcription[:-1]
    if post_processing['add_trailing_space']:
        transcription += ' '
    if post_processing['remove_capitalization']:
        transcription = transcription.lower()

    return transcription

def transcribe(audio_data, local_model=None, word_callback=None):
    """
    Transcribe audio data using the OpenAI API or a local model, depending on config.
    
    Args:
        audio_data: Audio data to transcribe
        local_model: Optional pre-initialized model
        word_callback: Optional callback function for word-by-word updates
    """
    if audio_data is None:
        return ''

    # Check recording duration
    sample_rate = ConfigManager.get_config_section('recording_options').get('sample_rate') or 16000
    duration_seconds = len(audio_data) / sample_rate
    max_duration = ConfigManager.get_config_section('recording_options').get('max_duration') or 120

    if max_duration > 0 and duration_seconds > max_duration:
        ConfigManager.console_print(f"Recording exceeded maximum duration of {max_duration} seconds.")
        return ''

    if ConfigManager.get_config_value('model_options', 'use_api'):
        transcription = transcribe_api(audio_data, word_callback)
    else:
        transcription = transcribe_local(audio_data, local_model, word_callback)

    return post_process_transcription(transcription)
