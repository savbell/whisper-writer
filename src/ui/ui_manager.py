from PyQt5.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from ui.tray_icon import TrayIcon
from config_manager import ConfigManager


class UIManager:
    """
    The UIManager class is responsible for managing all user interface components of
    the application. It handles the creation and interaction of various windows (main, settings,
    status) and the system tray icon. This class serves as the central point for UI-related
    operations and events.
    """
    def __init__(self, app, event_bus):
        """Initialize the UIManager with the QApplication instance and event bus."""
        self.event_bus = event_bus
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)
        self.is_closing = False
        self.show_status_window = False

        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()
        self.status_window = StatusWindow()
        self.tray_icon = TrayIcon(self.app)

        self.setup_connections()

    def setup_connections(self):
        """Establish connections between UI components and their corresponding actions."""
        self.main_window.open_settings.connect(self.settings_window.show)
        self.main_window.start_listening.connect(lambda: self.event_bus.emit("start_listening"))
        self.main_window.close_app.connect(self.initiate_close)
        self.tray_icon.open_settings.connect(self.settings_window.show)
        self.tray_icon.close_app.connect(self.initiate_close)
        self.event_bus.subscribe("quit_application", self.quit_application)
        self.event_bus.subscribe("profile_state_change", self.handle_profile_state_change)
        self.event_bus.subscribe("transcription_error", self.show_error_message)

    def show_main_window(self):
        """Display the main application window and show the system tray icon."""
        self.main_window.show()
        self.tray_icon.show()

    def handle_profile_state_change(self, message):
        """Handle changes in profile states, updating the status window if necessary."""
        ConfigManager.log_print(message)
        if self.show_status_window:
            if message:
                self.show_status(message)
            else:
                self.hide_status()

    def show_status(self, message):
        """Display a status message in the status window."""
        self.status_window.show_message(message)

    def show_error_message(self, message):
        """Display an error message in a QMessageBox."""
        QMessageBox.critical(None, "Transcription Error", message)

    def hide_status(self):
        """Hide the status window."""
        self.status_window.hide()

    def initiate_close(self):
        """Initiate the application closing process, ensuring it only happens once."""
        if not self.is_closing:
            self.is_closing = True
            self.event_bus.emit("close_app")

    def quit_application(self):
        """Quit the QApplication instance, effectively closing the application."""
        QApplication.instance().quit()

    def run_event_loop(self):
        """Start and run the Qt event loop, returning the exit code when finished."""
        return self.app.exec_()
