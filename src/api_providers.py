"""
API provider handlers for different transcription services.
"""
import io
import os
import base64
import requests
from abc import ABC, abstractmethod
from openai import OpenAI
import soundfile as sf

from utils import ConfigManager


PROVIDER_MODELS = {
    'openai': ['whisper-1'],
    'deepinfra': [
        'openai/whisper-large-v3-turbo',
        'openai/whisper-large-v3',
        'mistralai/Voxtral-Small-24B-2507',
        'mistralai/Voxtral-Mini-3B-2507',
    ],
    'openrouter': [
        'openai/whisper-large-v3-turbo',
        'openai/whisper-large-v3',
        'mistralai/Voxtral-Small-24B-2507',
        'mistralai/Voxtral-Mini-3B-2507',
    ]
}


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""
    
    @abstractmethod
    def transcribe(self, audio_data, model: str, language: str = None, 
                   prompt: str = None, temperature: float = 0.0) -> str:
        """Transcribe audio data and return text."""
        pass


class OpenAIProvider(TranscriptionProvider):
    """OpenAI API provider using the official SDK."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY'),
            base_url=base_url
        )
    
    def transcribe(self, audio_data, model: str, language: str = None,
                   prompt: str = None, temperature: float = 0.0) -> str:
        byte_io = io.BytesIO()
        sample_rate = ConfigManager.get_config_section('recording_options').get('sample_rate') or 16000
        sf.write(byte_io, audio_data, sample_rate, format='wav')
        byte_io.seek(0)
        
        response = self.client.audio.transcriptions.create(
            model=model,
            file=('audio.wav', byte_io, 'audio/wav'),
            language=language,
            prompt=prompt,
            temperature=temperature,
        )
        return response.text


class DeepInfraProvider(TranscriptionProvider):
    """DeepInfra API provider using direct HTTP requests."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepinfra.com/v1/inference"):
        self.api_key = api_key
        self.base_url = base_url
    
    def transcribe(self, audio_data, model: str, language: str = None,
                   prompt: str = None, temperature: float = 0.0) -> str:
        byte_io = io.BytesIO()
        sample_rate = ConfigManager.get_config_section('recording_options').get('sample_rate') or 16000
        sf.write(byte_io, audio_data, sample_rate, format='wav')
        byte_io.seek(0)
        
        if not model.startswith('openai/'):
            model = f'openai/{model}'
        
        url = f"{self.base_url}/{model}"
        
        headers = {
            "Authorization": f"bearer {self.api_key}"
        }
        
        files = {
            "audio": ("audio.wav", byte_io, "audio/wav")
        }
        
        data = {}
        if language:
            data['language'] = language
        if prompt:
            data['initial_prompt'] = prompt
        if temperature != 0.0:
            data['temperature'] = str(temperature)
        
        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepInfra API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result.get('text', '')


class OpenRouterProvider(TranscriptionProvider):
    """OpenRouter API provider using chat completions with audio input."""
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
    
    def transcribe(self, audio_data, model: str, language: str = None,
                   prompt: str = None, temperature: float = 0.0) -> str:
        byte_io = io.BytesIO()
        sample_rate = ConfigManager.get_config_section('recording_options').get('sample_rate') or 16000
        sf.write(byte_io, audio_data, sample_rate, format='wav')
        byte_io.seek(0)
        
        audio_base64 = base64.b64encode(byte_io.read()).decode('utf-8')
        
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        user_content = []
        if prompt:
            user_content.append({
                "type": "text",
                "text": prompt
            })
        user_content.append({
            "type": "input_audio",
            "input_audio": {
                "data": audio_base64,
                "format": "wav"
            }
        })
        
        system_message = "Transcribe the audio accurately. "
        if language:
            system_message += f"The audio language is {language}. "
        system_message += "Only output the transcription text, nothing else."
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result.get('choices', [{}])[0].get('message', {}).get('content', '')


def get_api_key_for_provider(provider_name: str, api_options: dict) -> str:
    """Get the appropriate API key for a provider, checking env vars first.
    
    Priority order:
    1. Provider-specific env var (OPENAI_API_KEY, DEEPINFRA_API_KEY, OPENROUTER_API_KEY)
    2. Provider-specific config key (openai_api_key, deepinfra_api_key, openrouter_api_key)
    3. Legacy api_key config field (backwards compatibility)
    4. Legacy OPENAI_API_KEY env var (backwards compatibility for all providers)
    """
    env_var_map = {
        'openai': 'OPENAI_API_KEY',
        'deepinfra': 'DEEPINFRA_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY'
    }
    config_key_map = {
        'openai': 'openai_api_key',
        'deepinfra': 'deepinfra_api_key',
        'openrouter': 'openrouter_api_key'
    }
    
    # 1. Check provider-specific env var
    env_var = env_var_map.get(provider_name)
    api_key = os.getenv(env_var) if env_var else None
    
    # 2. Check provider-specific config key
    if not api_key:
        config_key = config_key_map.get(provider_name)
        if config_key:
            api_key = api_options.get(config_key)
    
    # 3. Check legacy api_key field (backwards compatibility)
    if not api_key:
        api_key = api_options.get('api_key')
    
    # 4. Check legacy OPENAI_API_KEY env var (for any provider)
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
    
    return api_key


def get_provider(provider_name: str, api_options: dict = None, base_url: str = None) -> TranscriptionProvider:
    """Factory function to get the appropriate provider."""
    if api_options is None:
        api_options = {}
    api_key = get_api_key_for_provider(provider_name, api_options)
    if provider_name == 'deepinfra':
        return DeepInfraProvider(api_key=api_key, base_url=base_url or "https://api.deepinfra.com/v1/inference")
    elif provider_name == 'openrouter':
        return OpenRouterProvider(api_key=api_key, base_url=base_url or "https://openrouter.ai/api/v1")
    else:
        return OpenAIProvider(api_key=api_key, base_url=base_url)