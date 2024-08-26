import os
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject


class TrayIcon(QObject):
    open_settings = pyqtSignal()
    close_app = pyqtSignal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.tray_icon = None
        self.create_tray_icon()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(QIcon(os.path.join('assets', 'ww-logo.png')), self.app)

        tray_menu = QMenu()

        settings_action = QAction('Open Settings', self.app)
        settings_action.triggered.connect(self.open_settings.emit)
        tray_menu.addAction(settings_action)

        exit_action = QAction('Exit', self.app)
        exit_action.triggered.connect(self.close_app.emit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def show(self):
        if self.tray_icon:
            self.tray_icon.show()

    def hide(self):
        if self.tray_icon:
            self.tray_icon.hide()
