import sys
import os
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow


class StatusWindow(BaseWindow):
    status_signal = pyqtSignal(str, str)

    def __init__(self, status='Recording...'):
        super().__init__('WhisperWriter Status', 320, 120)
        self.initStatusUI(status)
        self.status_signal.connect(self.updateStatus)

    def initStatusUI(self, status):
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        microphone_path = os.path.join('assets', 'microphone.png')
        pencil_path = os.path.join('assets', 'pencil.png')
        self.microphone_pixmap = QPixmap(microphone_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pencil_pixmap = QPixmap(pencil_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(self.microphone_pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel(status)
        self.status_label.setFont(QFont('Segoe UI', 12))

        status_layout.addStretch(1)
        status_layout.addWidget(self.icon_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)

        self.main_layout.addLayout(status_layout)

    @pyqtSlot(str, str)
    def updateStatus(self, status, text):
        if status == 'recording':
            self.icon_label.setPixmap(self.microphone_pixmap)
        elif status == 'transcribing':
            self.icon_label.setPixmap(self.pencil_pixmap)
        self.status_label.setText(text)

        if status in ('idle', 'error', 'cancel'):
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    status_window = StatusWindow()
    status_window.show()

    # Simulate status updates
    QTimer.singleShot(3000, lambda: status_window.status_signal.emit('transcribing', 'Transcribing...'))
    QTimer.singleShot(6000, lambda: status_window.status_signal.emit('idle', ''))
    
    sys.exit(app.exec_())