from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, 
                                    QFrame, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from .styles import COLORS, SPACING

class WordLabel(QLabel):
    """A label for displaying a single word with animation capabilities."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']['primary']};
                background-color: transparent;
                padding: {SPACING['xs']}px {SPACING['sm']}px;
                border-radius: {SPACING['xs']}px;
                font-size: 16px;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)
        
    def highlight(self):
        """Highlight the word with animation."""
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']['primary']};
                background-color: {COLORS['accent']};
                padding: {SPACING['xs']}px {SPACING['sm']}px;
                border-radius: {SPACING['xs']}px;
                font-size: 16px;
            }}
        """)
        QTimer.singleShot(500, self.unhighlight)
        
    def unhighlight(self):
        """Remove the highlight."""
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']['primary']};
                background-color: transparent;
                padding: {SPACING['xs']}px {SPACING['sm']}px;
                border-radius: {SPACING['xs']}px;
                font-size: 16px;
            }}
        """)

class WordDisplay(QWidget):
    """A widget for displaying transcribed words in real-time."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.words = []
        self.current_index = -1
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container frame
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: {SPACING['sm']}px;
                border: 1px solid {COLORS['secondary']};
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(SPACING['md'], SPACING['md'],
                                          SPACING['md'], SPACING['md'])
        
        # Title
        title = QLabel("Live Transcription")
        title.setStyleSheet(f"""
            color: {COLORS['text']['primary']};
            font-weight: bold;
            font-size: 14px;
            margin-bottom: {SPACING['sm']}px;
        """)
        container_layout.addWidget(title)
        
        # Scroll area for words
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                width: 8px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['secondary']};
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Words container
        self.words_widget = QWidget()
        self.words_widget.setStyleSheet(f"""
            background-color: transparent;
            padding: {SPACING['sm']}px;
        """)
        
        self.words_layout = QHBoxLayout(self.words_widget)
        self.words_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.words_layout.setSpacing(SPACING['xs'])
        self.words_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.words_widget)
        container_layout.addWidget(scroll)
        
        layout.addWidget(container)
        
    def add_word(self, word: str):
        """Add a new word to the display."""
        word_label = WordLabel(word)
        self.words.append(word_label)
        self.words_layout.addWidget(word_label)
        self.current_index += 1
        word_label.highlight()
        
        # Ensure the latest word is visible
        self.words_widget.adjustSize()
        
    def clear(self):
        """Clear all words from the display."""
        for word in self.words:
            self.words_layout.removeWidget(word)
            word.deleteLater()
        self.words.clear()
        self.current_index = -1
        
    def get_text(self) -> str:
        """Get the complete text of all words."""
        return " ".join(word.text() for word in self.words)