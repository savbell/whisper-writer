import sys
import os
import math
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor, QPen, QPainterPath
from PyQt5.QtWidgets import (QApplication, QLabel, QHBoxLayout, QWidget, 
                            QGraphicsOpacityEffect, QVBoxLayout)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow
from ui.styles import COLORS, SPACING

class AudioWaveform(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 40)
        self.bars = 5
        self.bar_spacing = 8
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.animation_step = 0
        self.is_animating = False
        self.setVisible(False)  # Start hidden
        
    def start_animation(self):
        self.is_animating = True
        self.setVisible(True)
        self.timer.start(16)  # ~60 FPS for smoother animation
        
    def stop_animation(self):
        self.is_animating = False
        self.timer.stop()
        self.animation_step = 0
        self.setVisible(False)
        self.update()
        
    def update_animation(self):
        if not self.is_animating:
            return
        self.animation_step = (self.animation_step + 4) % 360  # Faster animation
        self.update()
        
    def paintEvent(self, event):
        if not self.is_animating:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        bar_width = 4
        
        # Set up the pen
        pen = QPen(QColor(COLORS['accent']))
        pen.setWidth(bar_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw animated bars with glow effect
        x_start = (width - (self.bars * (bar_width + self.bar_spacing))) / 2
        
        # Draw glow
        glow_pen = QPen(QColor(COLORS['accent']))
        glow_pen.setWidth(bar_width + 2)
        glow_pen.setCapStyle(Qt.RoundCap)
        painter.setOpacity(0.3)
        painter.setPen(glow_pen)
        
        for i in range(self.bars):
            x = x_start + i * (bar_width + self.bar_spacing)
            # Create wave-like animation with phase offset
            phase = math.radians(self.animation_step + (i * 45))
            height_factor = (math.sin(phase) + 1) / 2  # Convert to 0-1 range
            bar_height = height * 0.7 * (0.4 + (0.6 * height_factor))  # Min 40% height
            y_start = (height - bar_height) / 2
            
            # Draw glow
            painter.drawLine(int(x + bar_width/2), int(y_start),
                           int(x + bar_width/2), int(y_start + bar_height))
        
        # Draw main bars
        painter.setOpacity(1.0)
        painter.setPen(pen)
        
        for i in range(self.bars):
            x = x_start + i * (bar_width + self.bar_spacing)
            phase = math.radians(self.animation_step + (i * 45))
            height_factor = (math.sin(phase) + 1) / 2
            bar_height = height * 0.7 * (0.4 + (0.6 * height_factor))
            y_start = (height - bar_height) / 2
            
            painter.drawLine(int(x + bar_width/2), int(y_start),
                           int(x + bar_width/2), int(y_start + bar_height))

class StatusWindow(BaseWindow):
    statusSignal = pyqtSignal(str)
    closeSignal = pyqtSignal()

    def __init__(self):
        """
        Initialize the status window.
        """
        super().__init__('WhisperWit Status', 280, 80)
        self.initStatusUI()
        self.statusSignal.connect(self.updateStatus)
        
        # Add fade effect
        self.fade_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.fade_effect)
        self.fade_effect.setOpacity(0.95)

    def initStatusUI(self):
        """
        Initialize the status user interface.
        """
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container with rounded corners and background
        container = QWidget()
        container.setObjectName("statusContainer")
        container.setStyleSheet(f"""
            QWidget#statusContainer {{
                background-color: {COLORS['surface']};
                border-radius: {SPACING['md']}px;
                border: 1px solid {COLORS['accent']};
            }}
            QLabel {{
                color: {COLORS['text']['primary']};
                font-family: 'Segoe UI', sans-serif;
            }}
        """)
        
        status_layout = QVBoxLayout(container)
        status_layout.setSpacing(SPACING['xs'])
        status_layout.setContentsMargins(SPACING['lg'], SPACING['md'],
                                       SPACING['lg'], SPACING['md'])
        
        # Status text and icon
        text_layout = QHBoxLayout()
        text_layout.setSpacing(SPACING['sm'])
        
        self.status_label = QLabel('Recording...')
        self.status_label.setFont(QFont('Segoe UI', 11))
        self.status_label.setStyleSheet(f"color: {COLORS['text']['primary']};")
        
        # Audio waveform
        self.waveform = AudioWaveform()
        
        text_layout.addWidget(self.status_label)
        text_layout.addWidget(self.waveform)
        text_layout.addStretch()
        
        status_layout.addLayout(text_layout)
        
        # Add container to main layout
        self.main_layout.addWidget(container)
        
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
        y = screen_height - window_height - 100

        self.move(x, y)
        super().show()
        
    def closeEvent(self, event):
        """
        Emit the close signal when the window is closed.
        """
        self.waveform.stop_animation()
        self.closeSignal.emit()
        super().closeEvent(event)

    @pyqtSlot(str)
    def updateStatus(self, status):
        """
        Update the status window based on the given status.
        """
        if status == 'recording':
            self.status_label.setText('Recording...')
            self.waveform.start_animation()
            self.show()
        elif status == 'transcribing':
            self.status_label.setText('Transcribing...')
            self.waveform.stop_animation()

        if status in ('idle', 'error', 'cancel'):
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    status_window = StatusWindow()
    status_window.show()

    # Simulate status updates
    QTimer.singleShot(3000, lambda: status_window.statusSignal.emit('transcribing'))
    QTimer.singleShot(6000, lambda: status_window.statusSignal.emit('idle'))
    
    sys.exit(app.exec_())
