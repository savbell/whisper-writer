import os
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from key_listener import KeyListener
from result_thread import ResultThread
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from utils import load_config_schema, load_config_values


def main():    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join('assets', 'ww-logo.png')))
    
    schema = load_config_schema()
    config = load_config_values(schema)
    
    settings_window = SettingsWindow(schema)
    
    key_listener = KeyListener(config)
    result_thread = ResultThread(config)
    
    key_listener.activationKeyPressed.connect(result_thread.activation_key_pressed)
    key_listener.activationKeyReleased.connect(result_thread.activation_key_released) 
    
    main_window = MainWindow()
    main_window.openSettings.connect(settings_window.show)
    main_window.startListening.connect(key_listener.start_listening)
    
    if not config['misc']['hide_status_window']:
        status_window = StatusWindow()
        result_thread.statusSignal.connect(status_window.updateStatus)
    
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    print('Starting WhisperWriter...')
    main()
