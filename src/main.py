import os
import sys
import time
from audioplayer import AudioPlayer
from pynput.keyboard import Controller
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from key_listener import KeyListener
from result_thread import ResultThread
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from utils import load_config_schema, load_config_values
from transcription import create_local_model


class WhisperWriterApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(os.path.join('assets', 'ww-logo.png')))
        
        schema = load_config_schema()
        self.config = load_config_values(schema)
        
        self.settings_window = SettingsWindow(schema)
        
        self.key_listener = KeyListener(self.config)
        self.key_listener.activationKeyPressed.connect(self.activation_key_pressed)
        self.key_listener.activationKeyReleased.connect(self.activation_key_released) 
        
        self.local_model = create_local_model(self.config) if not self.config['model_options']['use_api'] else None
        
        self.result_thread = None
        self.keyboard = Controller()
        
        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.key_listener.start_listening)
        
        if not self.config['misc']['hide_status_window']:
            self.status_window = StatusWindow()
        
        self.main_window.show()

    def activation_key_pressed(self):
        if self.result_thread and self.result_thread.isRunning():
            if self.config['recording_options']['recording_mode'] == 'press_to_toggle':
                self.result_thread.stop_recording()
            return

        self.result_thread = ResultThread(self.config, self.local_model)
        if not self.config['misc']['hide_status_window']:
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()

    def activation_key_released(self):
        if self.config['recording_options']['recording_mode'] == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()

    def on_transcription_complete(self, result):
        self.typewrite(result, self.config['post_processing']['writing_key_press_delay'])
        
        if self.config['misc']['noise_on_completion']:
            AudioPlayer(os.path.join('assets', 'beep.wav')).play(block=True)
        
        self.key_listener.start_listening()
        
    def typewrite(self, text, interval):
        for letter in text:
            self.keyboard.press(letter)
            self.keyboard.release(letter)
            time.sleep(interval)

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = WhisperWriterApp()
    app.run()
