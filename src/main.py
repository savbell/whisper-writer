import os
import sys
import time
from audioplayer import AudioPlayer
from pynput.keyboard import Controller
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox

from key_listener import KeyListener
from result_thread import ResultThread
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from utils import load_config_schema, load_config_values
from transcription import create_local_model


class WhisperWriterApp:
    def __init__(self):
        """
        Initialize the application, opening settings window if no configuration file is found.
        """
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(os.path.join('assets', 'ww-logo.png')))
        
        schema = load_config_schema()
        self.config = load_config_values(schema)
        
        self.settings_window = SettingsWindow(schema)
        self.settings_window.settingsClosed.connect(self.on_settings_closed)
        
        if os.path.exists(os.path.join('src', 'config.yaml')):
            self.initialize_components()
        else:
            print('No configuration file found. Opening settings window...')
            self.settings_window.show()

    def initialize_components(self):
        """
        Initialize the components of the application.
        """
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
        
        self.create_tray_icon()
        self.main_window.show()
        
    def create_tray_icon(self):
        """
        Create the system tray icon and its context menu.
        """
        self.tray_icon = QSystemTrayIcon(QIcon(os.path.join('assets', 'ww-logo.png')), self.app)
        
        tray_menu = QMenu()
        
        show_action = QAction('WhisperWriter Main Menu', self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)
        
        settings_action = QAction('Open Settings', self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)
        
        exit_action = QAction('Exit', self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def exit_app(self):
        """
        Exit the application.
        """
        QApplication.quit()

    def on_settings_closed(self):
        """
        If settings is closed without saving on first run, initialize the components with default values.
        """
        if not os.path.exists(os.path.join('src', 'config.yaml')):
            QMessageBox.information(
                self.settings_window, 
                'Using Default Values',
                'Settings closed without saving. Default values are being used.'
            )
            self.initialize_components()

    def activation_key_pressed(self):
        """
        When the activation key is pressed, start the result thread to record audio and transcribe it.
        Or, if the recording mode is press_to_toggle or continuous, stop the recording or thread.
        """
        if self.result_thread and self.result_thread.isRunning():
            if self.config['recording_options']['recording_mode'] == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif self.config['recording_options']['recording_mode'] == 'continuous':
                self.stop_result_thread()
            return
            
        self.start_result_thread()

    def activation_key_released(self):
        """
        When the activation key is released, stop the recording if the recording mode is hold_to_record.
        """
        if self.config['recording_options']['recording_mode'] == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()

    def start_result_thread(self):
        """
        Start the result thread to record audio and transcribe it.
        """
        if self.result_thread and self.result_thread.isRunning():
            return
        
        self.result_thread = ResultThread(self.config, self.local_model)
        if not self.config['misc']['hide_status_window']:
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
            self.status_window.closeSignal.connect(self.stop_result_thread)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()
        
    def stop_result_thread(self):
        """
        Stop the result thread.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def on_transcription_complete(self, result):
        """
        When the transcription is complete, type the result and start listening for the activation key again.
        """
        self.typewrite(result, self.config['post_processing']['writing_key_press_delay'])
        
        if self.config['misc']['noise_on_completion']:
            AudioPlayer(os.path.join('assets', 'beep.wav')).play(block=True)
        
        if self.config['recording_options']['recording_mode'] == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start_listening()
    
    def typewrite(self, text, interval):
        """
        Type the given text with the given interval between each key press.
        """
        for letter in text:
            self.keyboard.press(letter)
            self.keyboard.release(letter)
            time.sleep(interval)

    def run(self):
        """
        Start the application.
        """
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = WhisperWriterApp()
    app.run()
