import io
import os
import numpy as np
import soundfile as sf
import importlib.util
import wave
import json
import requests
from tqdm import tqdm
from openai import OpenAI
from groq import Groq

from utils import ConfigManager
from keyring_manager import KeyringManager
from text_processor import TextProcessor

VOSK_MODEL_URLS = {
    'vosk-model-small-en-us-0.15': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
    'vosk-model-en-us-0.22': 'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip'
}

# Check if GPU packages are available
HAS_FASTER_WHISPER = importlib.util.find_spec("faster_whisper") is not None
HAS_TORCH = importlib.util.find_spec("torch") is not None

# Add check for Vosk availability
HAS_VOSK = importlib.util.find_spec("vosk") is not None

def is_vosk_model(model_name: str) -> bool:
    """Check if the model name is a Vosk model"""
    return model_name in VOSK_MODEL_URLS

def get_model_path(model_name: str) -> str:
    """Get the path where the model should be stored"""
    base_path = os.path.join(os.path.expanduser('~'), '.whisperwriter', 'models')
    if is_vosk_model(model_name):
        return os.path.join(base_path, 'vosk', model_name)
    return os.path.join(base_path, 'whisper', model_name)

def download_vosk_model(model_name: str) -> bool:
    """Download a Vosk model if not present"""
    if model_name not in VOSK_MODEL_URLS:
        ConfigManager.console_print(f"Error: Unknown Vosk model {model_name}")
        return False
        
    model_path = get_model_path(model_name)
    url = VOSK_MODEL_URLS[model_name]
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    try:
        ConfigManager.console_print(f"Downloading Vosk model {model_name}...")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        zip_path = model_path + '.zip'
        with open(zip_path, 'wb') as f, tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                pbar.update(size)
                
        ConfigManager.console_print("Extracting model...")
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get the name of the directory inside the zip
            root_dir = zip_ref.namelist()[0].split('/')[0]
            zip_ref.extractall(os.path.dirname(model_path))
            
            # If the extracted directory name doesn't match our expected path, rename it
            extracted_path = os.path.join(os.path.dirname(model_path), root_dir)
            if extracted_path != model_path:
                if os.path.exists(model_path):
                    import shutil
                    shutil.rmtree(model_path)
                os.rename(extracted_path, model_path)
            
        os.remove(zip_path)
        ConfigManager.console_print(f"Vosk model {model_name} downloaded and extracted successfully")
        return True
        
    except Exception as e:
        ConfigManager.console_print(f"Error downloading Vosk model: {str(e)}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return False

def get_optimal_device():
    """
    Determine the best available device for Whisper inference.
    Returns device string: 'mps', 'cuda', 'rocm', or 'cpu'
    """
    if not HAS_TORCH:
        ConfigManager.console_print("Torch not available, defaulting to API mode")
        return None
        
    import torch
    ConfigManager.console_print(f"PyTorch version: {torch.__version__}")
    ConfigManager.console_print(f"PyTorch CUDA version: {torch.version.cuda if hasattr(torch.version, 'cuda') else 'Not available'}")
    
    # Check CUDA availability with detailed logging
    if torch.cuda.is_available():
        cuda_device_count = torch.cuda.device_count()
        cuda_device_name = torch.cuda.get_device_name(0) if cuda_device_count > 0 else "Unknown"
        ConfigManager.console_print(f"CUDA is available. Found {cuda_device_count} device(s)")
        ConfigManager.console_print(f"CUDA device name: {cuda_device_name}")
        ConfigManager.console_print(f"CUDA capability: {torch.cuda.get_device_capability()}")
        ConfigManager.console_print(f"CUDA arch list: {torch.cuda.get_arch_list() if hasattr(torch.cuda, 'get_arch_list') else 'Not available'}")
    else:
        ConfigManager.console_print("CUDA is not available. Checking why...")
        if not hasattr(torch, 'cuda'):
            ConfigManager.console_print("PyTorch was not built with CUDA support")
        else:
            ConfigManager.console_print("PyTorch has CUDA support but no CUDA devices were found")
    
    # Device selection logic
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        ConfigManager.console_print("Using Apple Silicon GPU (MPS)")
        return "mps"
    elif torch.cuda.is_available():
        ConfigManager.console_print("Using NVIDIA GPU (CUDA)")
        return "cuda"
    elif hasattr(torch, 'hip') and torch.hip.is_available():
        ConfigManager.console_print("Using AMD GPU (ROCm)")
        return "rocm"
    else:
        ConfigManager.console_print("Using CPU")
        return "cpu"

def create_local_model():
    """Create a local model using Whisper."""
    if not HAS_FASTER_WHISPER and not HAS_VOSK:
        ConfigManager.console_print("Neither Faster Whisper nor Vosk available, defaulting to API mode")
        return None
        
    local_model_options = ConfigManager.get_config_section('model_options')['local']
    model_name = local_model_options['model']
    
    if is_vosk_model(model_name):
        if not HAS_VOSK:
            ConfigManager.console_print("Vosk not available, defaulting to API mode")
            return None
            
        # Import Vosk components only when needed
        from vosk import Model, SetLogLevel
        
        SetLogLevel(-1)  # Reduce Vosk logging noise
        model_path = get_model_path(model_name)
        
        if not os.path.exists(model_path):
            if not download_vosk_model(model_name):
                return None
                
        try:
            model = Model(model_path)
            ConfigManager.console_print('Vosk model created.')
            return ('vosk', model)
        except Exception as e:
            ConfigManager.console_print(f'Error initializing Vosk model: {e}')
            return None
    else:
        if not HAS_FASTER_WHISPER:
            ConfigManager.console_print("Faster Whisper not available, defaulting to API mode")
            return None
            
        # Import Whisper components only when needed
        from faster_whisper import WhisperModel
        
        ConfigManager.console_print('Creating local model...')
        compute_type = local_model_options['compute_type']
        model_path = local_model_options.get('model_path')

        if compute_type == 'int8':
            device = 'cpu'
            ConfigManager.console_print('Using int8 quantization, forcing CPU usage.')
        else:
            device = local_model_options.get('device', 'auto')
            if device == 'auto':
                device = get_optimal_device()

        try:
            if model_path:
                ConfigManager.console_print(f'Loading Whisper model from: {model_path}')
                model = WhisperModel(model_path,
                                   device=device,
                                   compute_type=compute_type,
                                   download_root=None)
            else:
                model = WhisperModel(local_model_options['model'],
                                   device=device,
                                   compute_type=compute_type)
            ConfigManager.console_print('Whisper model created.')
            return ('whisper', model)
        except Exception as e:
            ConfigManager.console_print(f'Error initializing WhisperModel: {e}')
            ConfigManager.console_print('Falling back to CPU.')
            model = WhisperModel(model_path or local_model_options['model'],
                               device='cpu',
                               compute_type=compute_type,
                               download_root=None if model_path else None)
            return ('whisper', model)

def transcribe_local(audio_data, local_model=None):
    """Transcribe audio using a local model (Whisper or Vosk)."""
    if not local_model:
        local_model = create_local_model()
    if not local_model:
        return ''
        
    model_type, model = local_model
    model_options = ConfigManager.get_config_section('model_options')
    
    if model_type == 'vosk':
        if not HAS_VOSK:
            ConfigManager.console_print("Vosk not available")
            return ''
            
        # Import Vosk components only when needed
        from vosk import KaldiRecognizer
        
        # Convert audio data to WAV format for Vosk
        byte_io = io.BytesIO()
        sample_rate = ConfigManager.get_config_section('recording_options').get('sample_rate', 16000)
        ConfigManager.console_print(f"Converting audio for Vosk (sample rate: {sample_rate}Hz)")
        sf.write(byte_io, audio_data, sample_rate, format='wav')
        byte_io.seek(0)
        
        try:
            # Process with Vosk
            wf = wave.open(byte_io, "rb")
            recognizer = KaldiRecognizer(model, wf.getframerate())
            recognizer.SetWords(True)  # Enable word timing info
            
            transcription = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if 'text' in result and result['text'].strip():
                        transcription.append(result['text'])
                    
            # Get final bits of audio
            final_result = json.loads(recognizer.FinalResult())
            if 'text' in final_result and final_result['text'].strip():
                transcription.append(final_result['text'])
                
            return ' '.join(transcription)
            
        except Exception as e:
            ConfigManager.console_print(f"Error transcribing with Vosk: {str(e)}")
            return ''
    else:
        # Existing Whisper transcription logic
        audio_data_float = audio_data.astype(np.float32) / 32768.0
        response = model.transcribe(
            audio=audio_data_float,
            language=model_options['common']['language'],
            initial_prompt=model_options['common']['initial_prompt'],
            condition_on_previous_text=model_options['local']['condition_on_previous_text'],
            temperature=model_options['common']['temperature'],
            vad_filter=model_options['local']['vad_filter'],
        )
        return ''.join([segment.text for segment in list(response[0])])

def transcribe_api(audio_data):
    """Transcribe audio using an API service (OpenAI, Deepgram, or Groq)."""
    api_options = ConfigManager.get_config_section('model_options')['api']
    provider = api_options['provider']
    model = api_options['model']
    
    ConfigManager.console_print(f"\n=== Using {provider.upper()} API Service ===")
    ConfigManager.console_print(f"Selected model: {model}")
    
    if provider == 'openai':
        return transcribe_with_openai(audio_data, api_options)
    elif provider == 'deepgram':
        return transcribe_with_deepgram(audio_data, api_options)
    elif provider == 'groq':
        return transcribe_with_groq(audio_data, api_options)
    else:
        ConfigManager.console_print(f"Unknown API provider: {provider}")
        return ''

def transcribe_with_openai(audio_data, api_options):
    """Transcribe audio using OpenAI's Whisper API."""
    try:
        api_key = KeyringManager.get_api_key("openai_transcription")
        if not api_key:
            ConfigManager.console_print("OpenAI API key not found in keyring")
            return ''
            
        # Use base_url from config, or fallback to OpenAI's API
        base_url = api_options.get('base_url') or 'https://api.openai.com/v1'
        ConfigManager.console_print(f"Using OpenAI endpoint: {base_url}")
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Convert audio to WAV file
        byte_io = io.BytesIO()
        sf.write(byte_io, audio_data, 16000, format='wav')
        byte_io.seek(0)
        
        files = {
            'file': ('audio.wav', byte_io, 'audio/wav'),
            'model': (None, 'whisper-1'),
        }
        
        ConfigManager.console_print("Sending request to OpenAI API...")
        response = requests.post(
            f"{base_url}/audio/transcriptions",
            headers=headers,
            files=files
        )
        
        if response.status_code == 200:
            result = response.json()['text']
            ConfigManager.console_print("OpenAI API request successful")
            ConfigManager.console_print(f"Transcription: {result}")
            return result
        else:
            ConfigManager.console_print(f"OpenAI API error: {response.text}")
            return ''
            
    except Exception as e:
        ConfigManager.console_print(f"Error transcribing with OpenAI: {str(e)}")
        return ''

def transcribe_with_deepgram(audio_data, api_options):
    """Transcribe audio using Deepgram's API."""
    try:
        api_key = KeyringManager.get_api_key("deepgram_transcription")
        if not api_key:
            ConfigManager.console_print("Deepgram API key not found in keyring")
            return ''
            
        # Convert audio to WAV format
        byte_io = io.BytesIO()
        sf.write(byte_io, audio_data, 16000, format='wav')
        audio_data = byte_io.getvalue()
        
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/wav"
        }
        
        # Set up Deepgram-specific parameters
        model = api_options['model']
        
        params = {
            "model": model,  # Use the full model name (nova-2 or nova-3)
            "smart_format": "true",
            "punctuate": "true",
        }
        
        # Always use Deepgram's API URL
        DEEPGRAM_BASE_URL = "https://api.deepgram.com/v1/listen"
        ConfigManager.console_print(f"Using Deepgram endpoint: {DEEPGRAM_BASE_URL}")
        ConfigManager.console_print(f"Model parameters: {params}")
        
        ConfigManager.console_print("Sending request to Deepgram API...")
        response = requests.post(
            DEEPGRAM_BASE_URL,
            headers=headers,
            params=params,
            data=audio_data
        )
        
        if response.status_code == 200:
            result = response.json()
            transcription = result['results']['channels'][0]['alternatives'][0]['transcript']
            ConfigManager.console_print("Deepgram API request successful")
            ConfigManager.console_print(f"Transcription: {transcription}")
            return transcription
        else:
            ConfigManager.console_print(f"Deepgram API error: {response.text}")
            return ''
            
    except Exception as e:
        ConfigManager.console_print(f"Error transcribing with Deepgram: {str(e)}")
        return ''

def transcribe_with_groq(audio_data, api_options):
    """Transcribe audio using Groq's Whisper API."""
    try:
        api_key = KeyringManager.get_api_key("groq_transcription")
        if not api_key:
            ConfigManager.console_print("Groq API key not found in keyring")
            return ''
            
        # Convert audio to WAV format
        byte_io = io.BytesIO()
        sf.write(byte_io, audio_data, 16000, format='wav')
        byte_io.seek(0)
        
        client = Groq(api_key=api_key)
        
        model = api_options['model']
        language = ConfigManager.get_config_value('model_options', 'common', 'language')
        initial_prompt = ConfigManager.get_config_value('model_options', 'common', 'initial_prompt')
        temperature = ConfigManager.get_config_value('model_options', 'common', 'temperature')
        
        ConfigManager.console_print("Sending request to Groq API...")
        response = client.audio.transcriptions.create(
            file=('audio.wav', byte_io.read()),
            model=model,
            prompt=initial_prompt,
            response_format="json",
            language=language or "en",
            temperature=temperature
        )
        
        if response and hasattr(response, 'text'):
            ConfigManager.console_print("Groq API request successful")
            ConfigManager.console_print(f"Transcription: {response.text}")
            return response.text
        else:
            ConfigManager.console_print("No transcription received from Groq API")
            return ''
            
    except Exception as e:
        ConfigManager.console_print(f"Error transcribing with Groq: {str(e)}")
        return ''

def post_process_transcription(transcription):
    """
    Apply post-processing to the transcription.
    """
    transcription = transcription.strip()
    post_processing = ConfigManager.get_config_section('post_processing')
    
    # Load and apply find/replace rules
    rules_file = ConfigManager.get_config_value('post_processing', 'find_replace_file')
    print(f"Find/replace file path: {rules_file}")  # Debug print
    if rules_file:
        print(f"Loading rules from: {rules_file}")
        if os.path.exists(rules_file):  # Debug print
            print(f"File exists at: {rules_file}")
        else:
            print(f"File not found at: {rules_file}")
        rules = TextProcessor.load_find_replace_rules(rules_file)
        print(f"Loaded rules: {rules}")  # Debug print
        transcription = TextProcessor.apply_find_replace_rules(transcription, rules)
    
    # Apply other post-processing options
    if post_processing['remove_trailing_period'] and transcription.endswith('.'):
        transcription = transcription[:-1]
    if post_processing['add_trailing_space']:
        transcription += ' '
    if post_processing['remove_capitalization']:
        transcription = transcription.lower()

    return transcription

def transcribe(audio_data, local_model=None):
    """
    Transcribe audio using either local model or API based on availability
    """
    if HAS_FASTER_WHISPER:
        if audio_data is None:
            return ''

        if ConfigManager.get_config_value('model_options', 'use_api'):
            ConfigManager.console_print("Using OpenAI Whisper API for transcription")
            transcription = transcribe_api(audio_data)
        else:
            if not local_model:
                local_model = create_local_model()
            model_name = ConfigManager.get_config_value('model_options', 'local', 'model')
            device = ConfigManager.get_config_value('model_options', 'local', 'device')
            ConfigManager.console_print(f"Using local Whisper model: {model_name} on {device}")
            transcription = transcribe_local(audio_data, local_model)
    else:
        ConfigManager.console_print("Using OpenAI Whisper API for transcription (faster-whisper not available)")
        transcription = transcribe_api(audio_data)

    return post_process_transcription(transcription)

