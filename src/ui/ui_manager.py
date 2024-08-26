from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from ui.tray_icon import TrayIcon


class UIManager:
    def __init__(self, app, event_bus):
        self.event_bus = event_bus
        self.app = app
        self.app.setQuitOnLastWindowClosed(False)
        self.is_closing = False

        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()
        self.status_window = StatusWindow()
        self.tray_icon = TrayIcon(self.app)

        self.setup_connections()

    def setup_connections(self):
        self.main_window.open_settings.connect(self.settings_window.show)
        self.main_window.start_listening.connect(lambda: self.event_bus.emit("start_listening"))
        self.main_window.close_app.connect(self.initiate_close)
        self.tray_icon.open_settings.connect(self.settings_window.show)
        self.tray_icon.close_app.connect(self.initiate_close)
        self.event_bus.subscribe("quit_application", self.quit_application)
        self.event_bus.subscribe("profile_state_change", self.handle_profile_state_change)

    def show_main_window(self):
        self.main_window.show()
        self.tray_icon.show()

    def handle_profile_state_change(self, message):
        if message:
            self.show_status(message)
        else:
            self.hide_status()

    def show_status(self, message):
        self.status_window.show_message(message)

    def hide_status(self):
        self.status_window.hide()

    def initiate_close(self):
        if not self.is_closing:
            self.is_closing = True
            self.event_bus.emit("close_app")

    def quit_application(self):
        QApplication.instance().quit()

    def run_event_loop(self):
        return self.app.exec_()
