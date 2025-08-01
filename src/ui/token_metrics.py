from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QFrame)
from PyQt5.QtCore import Qt

from .styles import COLORS, SPACING

class ProgressSection(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING['sm'])
        layout.setContentsMargins(SPACING['md'], SPACING['md'],
                                SPACING['md'], SPACING['md'])
        
        # Label and percentage in one line
        header = QHBoxLayout()
        
        self.title_label = QLabel(f"{title}: 0%")
        self.title_label.setStyleSheet("""
            font-family: system-ui;
            color: white;
            font-size: 14px;
        """)
        header.addWidget(self.title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 0.1);
                height: 8px;
            }
            
            QProgressBar::chunk {
                background-color: #007AFF;
            }
        """)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        
    def update_progress(self, percent):
        """Update progress bar and percentage text."""
        self.progress.setValue(int(percent))
        self.title_label.setText(f"{self.title_label.text().split(':')[0]}: {int(percent)}%")

class TokenMetricsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING['lg'])
        layout.setContentsMargins(SPACING['lg'], SPACING['lg'],
                                SPACING['lg'], SPACING['lg'])
        
        # Progress sections
        self.whisper_progress = ProgressSection("Audio Processing Usage")
        layout.addWidget(self.whisper_progress)
        
        self.gpt_progress = ProgressSection("Text Enhancement Usage")
        layout.addWidget(self.gpt_progress)
        
        layout.addStretch()
    
    def update_metrics(self, whisper_duration, gpt_tokens, total_cost, whisper_cost=None, gpt_cost=None):
        """Update progress bars with current values."""
        # Calculate percentages
        whisper_percent = min(100, (whisper_duration / 3600) * 100)  # Max 1 hour
        gpt_percent = min(100, (gpt_tokens / 1_000_000) * 100)      # Max 1M tokens
        
        # Update progress sections
        self.whisper_progress.update_progress(whisper_percent)
        self.gpt_progress.update_progress(gpt_percent)