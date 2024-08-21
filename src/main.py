import os
import sys
from audioplayer import AudioPlayer
from PyQt5.QtCore import QObject, QProcess, pyqtSignal, QMetaObject, Q_ARG, Qt, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox

from key_listener import KeyListener
from result_thread import ResultThread
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from transcription import TranscriptionManager
from keyboard_simulation import KeyboardSimulator
from utils import ConfigManager


class StatusUpdater(QObject):
    statusSignal = pyqtSignal(str)

class WhisperWriterApp(QObject):
    def __init__(self):
        """
        Initialize the application, opening settings window if no configuration file is found.
        """
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(os.path.join('assets', 'ww-logo.png')))
        self.key_listener = None
        self.keyboard_simulator = None
        self.transcription_manager = None

        ConfigManager.initialize()

        self.settings_window = SettingsWindow()
        self.settings_window.settings_closed.connect(self.on_settings_closed)
        self.settings_window.settings_saved.connect(self.restart_app)

        if ConfigManager.config_file_exists():
            self.initialize_components()
        else:
            print('No valid configuration file found. Opening settings window...')
            self.settings_window.show()

        self.status_updater = StatusUpdater()
        self.status_updater.statusSignal.connect(self.on_status_update)

    def initialize_components(self):
        """
        Initialize the components of the application.
        """
        self.keyboard_simulator = KeyboardSimulator()

        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)

        self.transcription_manager = TranscriptionManager()
        if not self.transcription_manager:
            QMessageBox.critical(None, "Initialization Error", f"Failed to initialize transcription: {str(e)}")

        self.result_thread = None

        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.key_listener.start)
        self.main_window.closeApp.connect(self.exit_app)

        if not ConfigManager.get_config_value('misc.hide_status_window'):
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

    def cleanup(self):
        if self.key_listener:
            self.key_listener.stop()
        if self.keyboard_simulator:
            self.keyboard_simulator.cleanup()
        if self.transcription_manager:
            self.transcription_manager.cleanup()

    def exit_app(self):
        """
        Exit the application.
        """
        self.cleanup()
        QApplication.quit()

    def restart_app(self):
        """Restart the application to apply the new settings."""
        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_settings_closed(self):
        """
        If settings is closed without saving on first run, initialize the components with default values.
        """
        if not ConfigManager.config_file_exists():
            QMessageBox.information(
                self.settings_window,
                'Using Default Values',
                'Settings closed without saving. Default values are being used.'
            )
            ConfigManager.save_config()  # Save default config to file
            self.initialize_components()

    def on_activation(self):
        """
        Called when the activation key combination is pressed.
        """
        if self.result_thread and self.result_thread.is_alive():
            recording_mode = ConfigManager.get_config_value('recording_options.recording_mode')
            if recording_mode == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif recording_mode == 'continuous':
                self.stop_result_thread()
            return

        self.start_result_thread()

    def on_deactivation(self):
        """
        Called when the activation key combination is released.
        """
        if ConfigManager.get_config_value('recording_options.recording_mode') == 'hold_to_record':
            if self.result_thread and self.result_thread.is_alive():
                self.result_thread.stop_recording()

    def start_result_thread(self):
        """
        Start the ResultThread for audio recording and transcription.
        Set up callbacks for status updates and transcription completion.
        """
        if self.result_thread and self.result_thread.is_alive():
            return

        self.result_thread = ResultThread(self.transcription_manager)
        self.result_thread.set_callbacks(self.status_updater.statusSignal.emit, self.on_transcription_complete)
        self.result_thread.start()


    def on_status_update(self, status):
        """
        Handle status updates from the ResultThread.
        Update the status window if it's not hidden.
        """
        if not ConfigManager.get_config_value('misc.hide_status_window'):
            self.status_window.statusSignal.emit(status)

    def stop_result_thread(self):
        """
        Stop the result thread.
        """
        if self.result_thread and self.result_thread.is_alive():
            self.result_thread.stop()

    def on_transcription_complete(self, result):
        """
        Handle the completion of transcription.
        Invoke the result handling method on the main thread.
        """
        QMetaObject.invokeMethod(self, "handle_transcription_result",
                                 Qt.QueuedConnection,
                                 Q_ARG(str, result))

    @pyqtSlot(str)
    def handle_transcription_result(self, result):
        """
        Process the transcription result on the main thread.
        Type the result, play a completion sound if enabled, and prepare for the next recording.
        """
        self.keyboard_simulator.typewrite(result)

        if ConfigManager.get_config_value('misc.noise_on_completion'):
            AudioPlayer(os.path.join('assets', 'beep.wav')).play(block=True)

        if ConfigManager.get_config_value('recording_options.recording_mode') == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start()

    def run(self):
        """
        Start the application.
        """
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = WhisperWriterApp()
    app.run()
