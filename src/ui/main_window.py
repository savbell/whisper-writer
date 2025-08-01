import os
import sys
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QPushButton, QHBoxLayout, QVBoxLayout,
                          QLabel, QWidget, QFrame, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow
from ui.styles import COLORS, SPACING, BUTTON_STYLE, CARD_STYLE
from ui.token_metrics import TokenMetricsPanel

class ActionCard(QFrame):
    def __init__(self, title, description, icon_path=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(CARD_STYLE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(300)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING['md'])
        layout.setContentsMargins(SPACING['lg'], SPACING['lg'],
                                SPACING['lg'], SPACING['lg'])
        
        # Header with icon and title
        header = QHBoxLayout()
        if icon_path:
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(24, 24))
            header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text']['primary']};
        """)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS['text']['secondary']};")
        layout.addWidget(desc_label)

class MainWindow(BaseWindow):
    openSettings = pyqtSignal()
    startListening = pyqtSignal()
    closeApp = pyqtSignal()

    def __init__(self):
        """
        Initialize the main window with modern UI.
        """
        super().__init__('WhisperWit', 800, 900)
        self.metrics_panel = None  # Initialize metrics panel reference
        self.initMainUI()
        
    def initMainUI(self):
        """
        Initialize the modern main user interface.
        """
        # Main container with dark theme
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']['primary']};
            }}
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: {SPACING['xs']}px;
                padding: {SPACING['sm']}px {SPACING['md']}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
            }}
            QLabel {{
                color: {COLORS['text']['primary']};
            }}
        """)
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(SPACING['lg'])
        main_layout.setContentsMargins(SPACING['lg'], SPACING['lg'], 
                                     SPACING['lg'], SPACING['lg'])
        
        # Header section
        header = QHBoxLayout()
        title = QLabel("WhisperWit")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text']['primary']};
        """)
        header.addWidget(title)
        
        settings_btn = QPushButton('Settings')
        settings_btn.setStyleSheet(BUTTON_STYLE)
        settings_btn.clicked.connect(self.openSettings.emit)
        header.addWidget(settings_btn)
        
        main_layout.addLayout(header)
        
        # Word display panel
        from .word_display import WordDisplay
        self.word_display = WordDisplay()
        main_layout.addWidget(self.word_display)
        
        # Token metrics panel
        self.metrics_panel = TokenMetricsPanel()
        main_layout.addWidget(self.metrics_panel)
        
        # Action cards in vertical layout with more space
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(SPACING['xl'])
        cards_layout.setContentsMargins(SPACING['xl'], SPACING['xl'],
                                      SPACING['xl'], SPACING['xl'])
        
        # Make cards expand horizontally
        for i in range(cards_layout.count()):
            widget = cards_layout.itemAt(i).widget()
            if widget:
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Record card
        record_card = ActionCard(
            "Start Recording",
            "Press to start recording your speech for transcription.",
            os.path.join('assets', 'microphone.png')
        )
        record_btn = QPushButton('Start')
        record_btn.setStyleSheet(BUTTON_STYLE)
        record_btn.clicked.connect(self.startPressed)
        record_card.layout().addWidget(record_btn)
        cards_layout.addWidget(record_card)
        
        # Settings card
        settings_card = ActionCard(
            "Configure",
            "Adjust transcription settings and API preferences.",
            os.path.join('assets', 'pencil.png')
        )
        settings_card_btn = QPushButton('Open Settings')
        settings_card_btn.setStyleSheet(BUTTON_STYLE)
        settings_card_btn.clicked.connect(self.openSettings.emit)
        settings_card.layout().addWidget(settings_card_btn)
        cards_layout.addWidget(settings_card)
        
        main_layout.addLayout(cards_layout)
        main_layout.addStretch()
        
        # Set the container as the central widget
        self.setCentralWidget(container)

    def update_metrics(self, whisper_duration, gpt_tokens, total_cost, whisper_cost=None, gpt_cost=None):
        """Update the token usage metrics display."""
        self.metrics_panel.update_metrics(whisper_duration, gpt_tokens, total_cost, whisper_cost, gpt_cost)

    def add_word(self, word: str):
        """Add a new word to the live display."""
        if not word:  # Empty string means clear
            self.word_display.clear()
        else:
            self.word_display.add_word(word)

    def closeEvent(self, event):
        """Close the application when the main window is closed."""
        self.closeApp.emit()

    def startPressed(self):
        """Start recording when the start button is pressed."""
        self.startListening.emit()
        self.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
