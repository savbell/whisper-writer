import os
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QClipboard
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QWidget, QApplication

from .base_window import BaseWindow


class TranscriptionResultDialog(BaseWindow):
    """
    A notification-style dialog that shows transcription results at the bottom right.
    Auto-disappears after 5 seconds unless clicked to persist.
    """
    
    def __init__(self):
        super().__init__("Transcription", 320, 120)
        self.is_persistent = False
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self.auto_hide)
        self.initResultUI()

    def initResultUI(self):
        """
        Initialize the notification-style transcription result dialog UI.
        """
        # Override the base window positioning to bottom right
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 8, 12, 8)
        content_layout.setSpacing(6)

        # Header with icon and message
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon (you can replace with an actual icon file if available)
        icon_label = QLabel("🎤")
        icon_label.setFont(QFont('Segoe UI', 12))
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        
        title_label = QLabel("Transcription Complete")
        title_label.setFont(QFont('Segoe UI', 9, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin: 0;")
        
        self.subtitle_label = QLabel("Click to copy and keep open")
        self.subtitle_label.setFont(QFont('Segoe UI', 8))
        self.subtitle_label.setStyleSheet("color: #7f8c8d; margin: 0;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(self.subtitle_label)
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        # Preview text (truncated)
        self.preview_label = QLabel()
        self.preview_label.setFont(QFont('Segoe UI', 9))
        self.preview_label.setStyleSheet("""
            color: #34495e; 
            background-color: #f8f9fa; 
            padding: 4px 8px; 
            border-radius: 4px;
            border: 1px solid #e9ecef;
        """)
        self.preview_label.setWordWrap(True)
        self.preview_label.setMaximumHeight(40)
        
        content_layout.addLayout(header_layout)
        content_layout.addWidget(self.preview_label)

        # Add content to main layout
        self.main_layout.addWidget(content_widget)
        
        # Store the transcription text
        self.transcription_text = ""

    def show_transcription_result(self, text):
        """
        Show the notification with the transcription result.
        
        Args:
            text (str): The transcribed text to display.
        """
        self.transcription_text = text
        
        # Create preview text (truncated)
        preview_text = text.strip()
        if len(preview_text) > 80:
            preview_text = preview_text[:77] + "..."
        self.preview_label.setText(preview_text)
        
        # Reset persistent state
        self.is_persistent = False
        self.subtitle_label.setText("Click to copy and keep open")
        
        # Position at bottom right
        self.position_bottom_right()
        
        # Show the dialog
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Start auto-hide timer (5 seconds)
        self.auto_hide_timer.start(5000)

    def position_bottom_right(self):
        """
        Position the dialog at the bottom right of the screen.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        window_width = self.width()
        window_height = self.height()
        
        # Position with some margin from edges
        margin = 20
        x = screen_width - window_width - margin
        y = screen_height - window_height - margin - 60  # Extra margin for taskbar
        
        self.move(x, y)

    def mousePressEvent(self, event):
        """
        Handle mouse clicks to copy text and make dialog persistent.
        """
        if event.button() == Qt.LeftButton and not self.is_persistent:
            self.make_persistent()
            self.copy_to_clipboard()
        else:
            # Allow dragging if persistent
            super().mousePressEvent(event)

    def make_persistent(self):
        """
        Make the dialog persistent (stop auto-hide timer).
        """
        self.is_persistent = True
        self.auto_hide_timer.stop()
        self.subtitle_label.setText("✓ Copied to clipboard")
        
        # Add a close button when persistent
        if not hasattr(self, 'close_button_added'):
            self.add_close_button()
            self.close_button_added = True

    def add_close_button(self):
        """
        Add a close button when the dialog becomes persistent.
        """
        # Get the main content layout
        content_widget = self.main_layout.itemAt(0).widget()
        content_layout = content_widget.layout()
        
        # Add close button
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 4, 0, 0)
        
        close_button = QPushButton("✕ Close")
        close_button.setFont(QFont('Segoe UI', 8))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        close_button.clicked.connect(self.close)
        
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        content_layout.addLayout(button_layout)
        
        # Resize to accommodate the button
        self.setFixedSize(320, 150)
        self.position_bottom_right()

    def copy_to_clipboard(self):
        """
        Copy the transcription result to the clipboard.
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(self.transcription_text)

    def auto_hide(self):
        """
        Auto-hide the dialog after timeout.
        """
        if not self.is_persistent:
            self.close()

    def closeEvent(self, event):
        """
        Clean up when closing.
        """
        self.auto_hide_timer.stop()
        super().closeEvent(event) 