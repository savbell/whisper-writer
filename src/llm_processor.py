import os
import json
import requests
from utils import ConfigManager
from keyring_manager import KeyringManager
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
import importlib
import ollama
from groq import Groq

# Check if Ollama is available
HAS_OLLAMA = importlib.util.find_spec("ollama") is not None

class LLMProcessor:
    def __init__(self, api_type=None):
        """Initialize the LLM processor."""
        self.config = ConfigManager.get_config_section('llm_post_processing')
        
        # If api_type is passed, use it; otherwise get from config without assuming a default
        if api_type is None:
            self.api_type = self.config.get('api_type')
            if self.api_type is None:
                ConfigManager.console_print("Warning: No API type specified in config")
                self.api_type = 'claude'  # Only use claude as last resort fallback
        else:
            self.api_type = api_type
        
        ConfigManager.console_print(f"Initializing LLM Processor with API type: {self.api_type}")
        
        # Get API key based on API type
        if self.api_type == 'claude':
            self.api_key = KeyringManager.get_api_key("claude")
            ConfigManager.console_print("Using Claude API")
        elif self.api_type == 'chatgpt':
            self.api_key = KeyringManager.get_api_key("openai_llm")
            ConfigManager.console_print("Using ChatGPT API")
        elif self.api_type == 'gemini':
            self.api_key = KeyringManager.get_api_key("gemini")
            ConfigManager.console_print("Using Gemini API")
        elif self.api_type == 'ollama':
            ConfigManager.console_print("Using local Ollama installation")
        elif self.api_type == 'groq':
            self.api_key = KeyringManager.get_api_key("groq")
            ConfigManager.console_print("Using Groq API")
            
        if not self.api_key and self.api_type != 'ollama':
            ConfigManager.console_print(f"Warning: No API key found for {self.api_type}")
            
    def process_text(self, text: str, system_message: str) -> str:
        """
        Process text through the LLM.
        
        Args:
            text: The text to process
            is_instruction_mode: If True, use instruction system message, otherwise use cleanup message
        """
        if not text:
            return text

        if not self.config['enabled']:
            ConfigManager.console_print("LLM processing is disabled")
            return text
        
        if not system_message:
            ConfigManager.console_print("Warning: No system message provided!")
            # Fetch default from config schema
            if self.is_instruction_mode:
                system_message = ConfigManager.get_schema()['llm_post_processing']['instruction_system_message']['value']
            else:
                system_message = ConfigManager.get_schema()['llm_post_processing']['system_prompt']['value']
            ConfigManager.console_print(f"Using default system message: {system_message}")
        
        api_type = self.config['api_type']
        
        # Determine which model to use based on the system message
        if system_message == ConfigManager.get_config_value("llm_post_processing", "instruction_system_message"):
            model = ConfigManager.get_config_value('llm_post_processing', 'instruction_model')
            mode = "instruction"
            ConfigManager.console_print("Using instruction mode")
        else:
            model = ConfigManager.get_config_value('llm_post_processing', 'cleanup_model')
            mode = "cleanup"
            ConfigManager.console_print("Using cleanup mode")
        
        # Default models if none specified
        default_models = {
            'claude': 'claude-3-5-sonnet-latest',
            'chatgpt': 'gpt-4o-mini',
            'gemini': 'gemini-1.5-flash',
            'groq': 'llama-3.1-8b-instant',
            'ollama': {
                'cleanup': 'airat/karen-the-editor-v2-strict',
                'instruction': 'llama3.2'
            }
        }
        
        if not model:
            if api_type == 'ollama':
                model = default_models['ollama'][mode]
            else:
                model = default_models.get(api_type)
            ConfigManager.console_print(f"No model specified, using default {mode} model for {api_type}: {model}")
        
        ConfigManager.console_print(f"Processing text with {api_type} using {mode} model: {model}")
        ConfigManager.console_print(f"Using system message: {system_message}")
        
        if api_type == 'claude':
            return self._process_claude(text, system_message, model)
        elif api_type == 'chatgpt':
            return self._process_chatgpt(text, system_message, model)
        elif api_type == 'gemini':
            return self._process_gemini(text, system_message, model)
        elif api_type == 'ollama':
            return self._process_ollama(text, system_message, model)  # Pass the model explicitly
        elif api_type == 'groq':
            return self._process_groq(text, system_message, model)
        return text
        
    def _process_claude(self, text: str, system_message: str, model: str) -> str:
        api_key = KeyringManager.get_api_key("claude")
        ConfigManager.console_print(f"Using Claude API key: {'[SET]' if api_key else '[NOT SET]'}")
        ConfigManager.console_print(f"Using Claude model: {model}")
        
        headers = {
            'anthropic-version': '2023-06-01',
            'x-api-key': api_key,
            'content-type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': text}
            ],
            'max_tokens': 4096,
            'system': system_message,
            'temperature': self.config['temperature']
        }
        
        try:
            ConfigManager.console_print(f"Sending request to Claude API with model {model}")
            response = requests.post(
                self.config['endpoint'],
                headers=headers,
                json=data
            )
            
            ConfigManager.console_print(f"Claude API response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                ConfigManager.console_print(f"Claude API response: {response_data}")
                
                if 'content' in response_data and len(response_data['content']) > 0:
                    processed_text = response_data['content'][0]['text']
                    ConfigManager.console_print(f"Processed text from Claude model {model}: {processed_text}")
                    return processed_text
                
                ConfigManager.console_print(f"Unexpected Claude API response structure: {response_data}")
            else:
                ConfigManager.console_print(f"Claude API error with model {model}: {response.status_code} - {response.text}")
            
        except Exception as e:
            ConfigManager.console_print(f"Error in Claude API call with model {model}: {str(e)}")
            return text
        
        return text
        
    def _process_chatgpt(self, text: str, system_message: str, model: str) -> str:
        api_key = KeyringManager.get_api_key("openai_llm")
        ConfigManager.console_print(f"Using ChatGPT API key: {'[SET]' if api_key else '[NOT SET]'}")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': text}
            ],
            'temperature': self.config['temperature']
        }
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data
            )
            
            ConfigManager.console_print(f"ChatGPT API response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    processed_text = response_data['choices'][0]['message']['content']
                    ConfigManager.console_print(f"Processed text from ChatGPT: {processed_text}")
                    return processed_text
                
                ConfigManager.console_print(f"Unexpected ChatGPT API response structure: {response_data}")
            else:
                ConfigManager.console_print(f"ChatGPT API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            ConfigManager.console_print(f"Error in ChatGPT API call: {str(e)}")
        
        return text
        
    def _process_gemini(self, text: str, system_message: str, model: str) -> str:
        api_key = KeyringManager.get_api_key("gemini")
        ConfigManager.console_print(f"Using Gemini API key: {'[SET]' if api_key else '[NOT SET]'}")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'contents': [
                {
                    'role': 'user',
                    'parts': [
                        {'text': system_message},
                        {'text': text}
                    ]
                }
            ],
            'generationConfig': {
                'temperature': self.config['temperature'],
                'topK': 1,
                'topP': 1
            }
        }
        
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            ConfigManager.console_print(f"Using Gemini model: {model}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=data
            )
            
            ConfigManager.console_print(f"Gemini API response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                if ('candidates' in response_data and 
                    len(response_data['candidates']) > 0 and 
                    'content' in response_data['candidates'][0] and
                    'parts' in response_data['candidates'][0]['content']):
                    processed_text = response_data['candidates'][0]['content']['parts'][0]['text']
                    ConfigManager.console_print(f"Processed text from Gemini: {processed_text}")
                    return processed_text
                
                ConfigManager.console_print(f"Unexpected Gemini API response structure: {response_data}")
            else:
                ConfigManager.console_print(f"Gemini API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            ConfigManager.console_print(f"Error in Gemini API call: {str(e)}")
        
        return text
        
    def _process_ollama(self, text: str, system_message: str, model: str) -> str:
        """Process text through local Ollama model using the Python client."""
        if not model:
            ConfigManager.console_print("Error: No model specified")
            return text
            
        if not HAS_OLLAMA:
            ConfigManager.console_print("Ollama not available. Please install the Ollama package or choose a different API.")
            return text
            
        try:
            # Check if Ollama service is running and get available models
            models_response = ollama.list()
            
            ConfigManager.console_print("\n=== Available Ollama Models ===")
            if hasattr(models_response, 'models'):
                available_models = []
                for model_info in models_response.models:
                    model_name = getattr(model_info, 'model', '').replace(':latest', '')
                    details = getattr(model_info, 'details', None)
                    
                    available_models.append(model_name)
                    
                    # Format model details
                    model_details = []
                    if details:
                        if hasattr(details, 'parameter_size'):
                            model_details.append(f"Size: {details.parameter_size}")
                        if hasattr(details, 'family'):
                            model_details.append(f"Family: {details.family}")
                        if hasattr(details, 'quantization_level'):
                            model_details.append(f"Quantization: {details.quantization_level}")
                    
                    ConfigManager.console_print(f"- {model_name}")
                    if model_details:
                        ConfigManager.console_print(f"  ({', '.join(model_details)})")
                
                ConfigManager.console_print("===========================\n")
                
                if model not in available_models:
                    ConfigManager.console_print(f"Warning: Selected model '{model}' not found in available models")
                
        except Exception as e:
            ConfigManager.console_print(f"Error checking Ollama service: {str(e)}")
            return text
        
        try:
            ConfigManager.console_print(f"Using Ollama model: {model}")  # This log should now be consistent
            temperature = self.config.get('temperature', 0.3)
            ConfigManager.console_print(f"Temperature setting: {temperature}")
            
            response = ollama.chat(
                model=model,  # Use the passed model parameter
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                options={
                    "temperature": temperature
                }
            )
            
            if not response or 'message' not in response or 'content' not in response['message']:
                ConfigManager.console_print("Error: Unexpected response format from Ollama")
                return text
            
            processed_text = response['message']['content'].strip()
            ConfigManager.console_print(f"Ollama response received:")
            ConfigManager.console_print(f"- Input length: {len(text)}")
            ConfigManager.console_print(f"- Output length: {len(processed_text)}")
            return processed_text
            
        except ollama.ResponseError as e:
            ConfigManager.console_print(f"Ollama response error: {str(e)}")
            return text
        except Exception as e:
            ConfigManager.console_print(f"Unexpected error in Ollama processing: {str(e)}")
            return text

    def _process_groq(self, text: str, system_message: str, model: str) -> str:
        """Process text through Groq's API."""
        api_key = KeyringManager.get_api_key("groq")
        ConfigManager.console_print(f"Using Groq API key: {'[SET]' if api_key else '[NOT SET]'}")
        
        try:
            client = Groq(api_key=api_key)
            
            ConfigManager.console_print(f"Using Groq model: {model}")
            
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                model=model,
                temperature=self.config['temperature']
            )
            
            if response and hasattr(response.choices[0].message, 'content'):
                processed_text = response.choices[0].message.content.strip()
                ConfigManager.console_print(f"Processed text from Groq: {processed_text}")
                return processed_text
            
            ConfigManager.console_print("No valid response from Groq API")
            
        except Exception as e:
            ConfigManager.console_print(f"Error in Groq API call: {str(e)}")
        
        return text

    def get_available_models(self, api_type):
        """Get available models for the specified API type."""
        ConfigManager.console_print(f"\n=== Fetching models for API type: {api_type} ===")
        
        # Validate API type early
        if api_type not in ['claude', 'chatgpt', 'gemini', 'ollama', 'groq']:
            ConfigManager.console_print(f"Unsupported API type: {api_type}")
            return []
        
        # Get API key early for all non-Ollama types
        if api_type != 'ollama':
            api_key_map = {
                'claude': 'claude',
                'chatgpt': 'openai_llm',
                'gemini': 'gemini',
                'groq': 'groq'
            }
            api_key = KeyringManager.get_api_key(api_key_map[api_type])
            if not api_key:
                ConfigManager.console_print(f"No {api_type} API key found")
                return []
        
        try:
            if api_type == 'groq':
                client = Groq(api_key=api_key)
                
                ConfigManager.console_print("Making request to Groq models endpoint...")
                models_response = client.models.list()
                
                # Extract model IDs from the response
                models = [model.id for model in models_response.data]
                ConfigManager.console_print(f"Found Groq models: {models}")
                return models

            elif api_type == 'claude':
                headers = {
                    'anthropic-version': '2023-06-01',
                    'x-api-key': api_key
                }
                
                ConfigManager.console_print("Making request to Claude models endpoint...")
                response = requests.get('https://api.anthropic.com/v1/models', headers=headers)
                ConfigManager.console_print(f"Claude API response status: {response.status_code}")
                
                if response.status_code == 200:
                    models_data = response.json()
                    models = [model['id'] for model in models_data.get('data', [])]
                    ConfigManager.console_print(f"Found Claude models: {models}")
                    return models
                ConfigManager.console_print(f"Claude API error: {response.status_code} - {response.text}")
                
            elif api_type == 'chatgpt':
                import openai
                openai.api_key = api_key
                
                ConfigManager.console_print("Fetching OpenAI models...")
                model_list_response = openai.Model.list()
                models = [model.id for model in model_list_response.data]
                ConfigManager.console_print(f"Found OpenAI models: {models}")
                return models
                
            elif api_type == 'gemini':
                genai.configure(api_key=api_key)
                models = [m.name for m in genai.list_models() 
                         if 'generateContent' in m.supported_generation_methods]
                ConfigManager.console_print(f"Found Gemini models: {models}")
                return models
                
            elif api_type == 'ollama':
                if not HAS_OLLAMA:
                    ConfigManager.console_print("Ollama not available")
                    return []
                
                response = requests.get('http://localhost:11434/api/models')
                if response.status_code == 200:
                    models_data = response.json()
                    models = [model['name'] for model in models_data.get('models', [])]
                    ConfigManager.console_print(f"Found Ollama models: {models}")
                    return models
                ConfigManager.console_print(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            ConfigManager.console_print(f"Error fetching {api_type} models: {str(e)}")
        
        return []