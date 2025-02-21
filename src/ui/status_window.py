import sys
import os
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout, QVBoxLayout

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow
from utils import ConfigManager

class StatusWindow(BaseWindow):
    statusSignal = pyqtSignal(str, bool)
    closeSignal = pyqtSignal()

    def __init__(self):
        """
        Initialize the status window.
        """
        super().__init__('WhisperWriter Status', 450, 100)
        self.initStatusUI()
        self.statusSignal.connect(self.updateStatus)
        
        # Add timer for pulsing effect
        self.warning_timer = QTimer()
        self.warning_timer.timeout.connect(self.updateWarningPulse)
        self.pulse_step = 0
        self.pulse_direction = 1

    def initStatusUI(self):
        """
        Initialize the status user interface.
        """
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)

        # Main status display (icon + status)
        top_layout = QHBoxLayout()
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        microphone_path = os.path.join('assets', 'microphone.png')
        pencil_path = os.path.join('assets', 'pencil.png')
        self.microphone_pixmap = QPixmap(microphone_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pencil_pixmap = QPixmap(pencil_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(self.microphone_pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel('Recording...')
        self.status_label.setFont(QFont('Segoe UI', 12))
        
        # Shortcuts label
        self.shortcuts_label = QLabel()
        self.shortcuts_label.setFont(QFont('Segoe UI', 9))
        self.shortcuts_label.setStyleSheet("color: gray;")
        self.shortcuts_label.setAlignment(Qt.AlignCenter)
        self.shortcuts_label.hide()  # Hidden by default

        top_layout.addStretch(1)
        top_layout.addWidget(self.icon_label)
        top_layout.addWidget(self.status_label)
        top_layout.addStretch(1)

        status_layout.addLayout(top_layout)
        status_layout.addWidget(self.shortcuts_label)

        self.main_layout.addLayout(status_layout)
        
    def show(self):
        """
        Position the window in the bottom center of the screen and show it.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        window_width = self.width()
        window_height = self.height()

        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 120

        self.move(x, y)
        super().show()
        
    def closeEvent(self, event):
        """
        Emit the close signal when the window is closed.
        """
        self.closeSignal.emit()
        super().closeEvent(event)

    def format_key_combo(self, key_combo: str) -> str:
        """Convert key combination to symbolic representation."""
        # Return empty string if key_combo is None
        if not key_combo:
            return ''

        key_map = {
            'ctrl': 'CTRL',
            'shift': 'SHIFT',
            'alt': 'ALT',
            'space': 'SPACE',
            'win': 'WIN',
            '+': '',  # Remove the plus signs between keys
        }
        
        parts = key_combo.lower().split('+')
        return ''.join(key_map.get(part, part.upper()) for part in parts)

    def updateWarningPulse(self):
        """Update the warning background color for pulsing effect"""
        if not self.isVisible():
            self.warning_timer.stop()
            return
            
        # Pulse between 20% and 100% saturation and vary lightness for dramatic effect
        self.pulse_step += self.pulse_direction
        if self.pulse_step > 80 or self.pulse_step < 0:  # Much wider range
            self.pulse_direction *= -1
            self.pulse_step += self.pulse_direction
            
        # Calculate color based on pulse step
        saturation = 20 + self.pulse_step  # Much wider range from 20% to 100%
        lightness = 100 - (self.pulse_step / 2)  # Vary lightness from 60% to 100%
        
        # print(f"[DEBUG] Pulse - Step: {self.pulse_step}, Saturation: {saturation}%, Lightness: {lightness}%")
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: hsla(48, {saturation}%, {lightness}%, 1.0);
                border: 1px solid #FFE5A3;
                border-radius: 5px;
            }}
            QLabel {{
                background-color: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
            }}
        """)

    @pyqtSlot(str, bool)
    def updateStatus(self, status, use_llm=False):
        """
        Update the status window based on the given status.
        """
        if status == 'recording':
            self.icon_label.setPixmap(self.microphone_pixmap)
            
            # Check for continuous mode and remote API usage
            continuous_mode = ConfigManager.get_config_value('recording_options', 'recording_mode') == 'continuous'
            using_api = ConfigManager.get_config_value('model_options', 'use_api')
            allow_continuous_api = ConfigManager.get_config_value('recording_options', 'allow_continuous_api')
            
            # Only check LLM settings if LLM mode is active
            using_remote_api = using_api
            if use_llm:
                llm_type = ConfigManager.get_config_value('llm_post_processing', 'api_type')
                using_remote_api = using_remote_api or (llm_type != 'ollama')
            
            # If continuous mode and remote API are being used but not allowed, force stop
            if continuous_mode and using_remote_api and not allow_continuous_api:
                print("[DEBUG] Continuous mode with remote API not allowed. Stopping recording.")
                self.closeSignal.emit()  # This will trigger stop_result_thread in main.py
                return
            
            if continuous_mode and using_remote_api:
                print("[DEBUG] Setting warning status for continuous remote API usage")
                self.status_label.setText('⚠️ Continuous Recording (Remote API) ⚠️')
                self.status_label.setStyleSheet("")
                self.pulse_step = 0
                self.pulse_direction = 1
                self.warning_timer.start(15)
            else:
                print("[DEBUG] Setting normal recording status")
                self.status_label.setText('Recording...')
                self.status_label.setStyleSheet("")  # Reset label color
                self.setStyleSheet("")  # Reset window style
                self.warning_timer.stop()  # Stop pulsing effect
            
            # Get shortcut keys and convert to symbols
            activation_key = self.format_key_combo(ConfigManager.get_config_value('recording_options', 'activation_key'))
            cleanup_key = self.format_key_combo(ConfigManager.get_config_value('recording_options', 'llm_cleanup_key'))
            instruction_key = self.format_key_combo(ConfigManager.get_config_value('recording_options', 'llm_instruction_key'))
            
            # Format shortcuts with emojis and symbolic keys
            shortcuts_text = f"⏹️ {activation_key} | 🧹 {cleanup_key} | 💭 {instruction_key}"
            self.shortcuts_label.setText(shortcuts_text)
            # self.shortcuts_label.show()
            self.show()
            
        elif status == 'transcribing':
            self.icon_label.setPixmap(self.pencil_pixmap)
            self.status_label.setText('Transcribing...')
            self.shortcuts_label.hide()
            
        elif status == 'processing_llm_cleanup':
            self.icon_label.setPixmap(self.pencil_pixmap)
            api_type = ConfigManager.get_config_value('llm_post_processing', 'api_type') or 'LLM'
            self.status_label.setText(f'Cleaning up text with {api_type.upper()}...')
            self.shortcuts_label.hide()
            
        elif status == 'processing_llm_instruction':
            self.icon_label.setPixmap(self.pencil_pixmap)
            api_type = ConfigManager.get_config_value('llm_post_processing', 'api_type') or 'LLM'
            self.status_label.setText(f'Processing instruction with {api_type.upper()}...')
            self.shortcuts_label.hide()

        if status in ('idle', 'error', 'cancel'):
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    status_window = StatusWindow()
    status_window.show()

    # Simulate status updates
    QTimer.singleShot(3000, lambda: status_window.statusSignal.emit('transcribing', False))
    QTimer.singleShot(6000, lambda: status_window.statusSignal.emit('idle', False))
    
    sys.exit(app.exec_())
