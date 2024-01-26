import json
import os
import queue
import threading
import time
import keyboard
from pynput.keyboard import Controller
from transcription import create_local_model, record_and_transcribe
from status_window import StatusWindow

class ResultThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ResultThread, self).__init__(*args, **kwargs)
        self.result = None
        self.stop_transcription = False

    def run(self):
        self.result = self._target(*self._args, cancel_flag=lambda: self.stop_transcription, **self._kwargs)

    def stop(self):
        self.stop_transcription = True

def load_config_with_defaults():
    default_config = {
        'use_api': False,
        'api_options': {
            'model': 'whisper-1',
            'language': None,
            'temperature': 0.0,
            'initial_prompt': None
        },
        'local_model_options': {
            'model': 'base',
            'device': 'auto',
            'compute_type': 'auto',
            'language': None,
            'temperature': 0.0,
            'initial_prompt': None,
            'condition_on_previous_text': True,
            'vad_filter': False,
        },
        'activation_key': 'ctrl+shift+space',
        'sound_device': None,
        'sample_rate': 16000,
        'silence_duration': 900,
        'writing_key_press_delay': 0.008,
        'remove_trailing_period': True,
        'add_trailing_space': False,
        'remove_capitalization': False,
        'print_to_terminal': True,
        'push_to_talk': False,
        'hide_status_window': False
    }

    config_path = os.path.join('src', 'config.json')
    if os.path.isfile(config_path):
        with open(config_path, 'r') as config_file:
            user_config = json.load(config_file)
            for key, value in user_config.items():
                if key in default_config and value is not None:
                    default_config[key] = value

    return default_config

def clear_status_queue():
    while not status_queue.empty():
        try:
            status_queue.get_nowait()
        except queue.Empty:
            break

def on_shortcut():
    global status_queue, local_model
    clear_status_queue()

    status_queue.put(('recording', 'Recording...'))
    recording_thread = ResultThread(target=record_and_transcribe, 
                                    args=(status_queue,),
                                    kwargs={'config': config,
                                            'local_model': local_model if local_model and not config['use_api'] else None},)
    
    if not config['hide_status_window']:
        status_window = StatusWindow(status_queue)
        status_window.recording_thread = recording_thread
        status_window.start()
    
    recording_thread.start()
    recording_thread.join()
    
    if not config['hide_status_window']:
        if status_window.is_alive():
            status_queue.put(('cancel', ''))

    transcribed_text = recording_thread.result

    if transcribed_text:
        typewrite(transcribed_text, interval=config['writing_key_press_delay'])

def format_keystrokes(key_string):
    return '+'.join(word.capitalize() for word in key_string.split('+'))

def typewrite(text, interval):
    for letter in text:
        pyinput_keyboard.press(letter)
        pyinput_keyboard.release(letter)
        time.sleep(interval)


# Main script

config = load_config_with_defaults()
method = 'OpenAI\'s API' if config['use_api'] else 'a local model'
status_queue = queue.Queue()

keyboard.add_hotkey(config['activation_key'], on_shortcut)
pyinput_keyboard = Controller()

print(f'Script activated. Whisper is set to run using {method}. To change this, modify the "use_api" value in the src\\config.json file.')
local_model = None
if not config['use_api']:
    print('Creating local model...')
    local_model = create_local_model(config)
    print('Local model created.')

print(f'Press {format_keystrokes(config["activation_key"])} to start recording and transcribing. Press Ctrl+C on the terminal window to quit.')
try:
    keyboard.wait()  # Keep the script running to listen for the shortcut
except KeyboardInterrupt:
    print('\nExiting the script...')
    os.system('exit')
