from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

# Modern color scheme
COLORS = {
    'primary': '#1a1a1a',     # Almost black
    'secondary': '#2d2d2d',   # Dark gray
    'accent': '#4299E1',      # Bright blue
    'background': '#1a1a1a',  # Almost black
    'surface': '#2d2d2d',     # Dark gray
    'error': '#E53E3E',       # Red
    'success': '#48BB78',     # Green
    'text': {
        'primary': '#FFFFFF',   # White
        'secondary': '#A0AEC0', # Light gray
        'disabled': '#4A5568'   # Medium gray
    }
}

# Consistent spacing units
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24
}

# Shadow definitions
SHADOWS = {
    'sm': '0 1px 3px rgba(0,0,0,0.12)',
    'md': '0 4px 6px rgba(0,0,0,0.1)',
    'lg': '0 10px 15px rgba(0,0,0,0.1)'
}

# Card styles
CARD_STYLE = f"""
    QWidget {{
        background-color: {COLORS['surface']};
        border-radius: {SPACING['md']}px;
        border: 1px solid {COLORS['secondary']};
        color: {COLORS['text']['primary']};
    }}
    
    QLabel {{
        padding: 0;
        margin: 0;
    }}
    
    QPushButton {{
        margin-top: {SPACING['md']}px;
        min-height: 32px;
    }}
"""

# Button styles
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['accent']};
        color: white;
        border: none;
        border-radius: {SPACING['xs']}px;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['primary']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['secondary']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['text']['disabled']};
    }}
"""

# Input field styles
INPUT_STYLE = f"""
    QLineEdit {{
        background-color: {COLORS['background']};
        border: 1px solid {COLORS['text']['disabled']};
        border-radius: {SPACING['xs']}px;
        padding: {SPACING['sm']}px;
        color: {COLORS['text']['primary']};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS['accent']};
    }}
"""

# Label styles
LABEL_STYLE = f"""
    QLabel {{
        color: {COLORS['text']['primary']};
        font-size: 14px;
    }}
"""

# Metric card styles
METRIC_CARD_STYLE = f"""
    QWidget#metricCard {{
        background-color: {COLORS['surface']};
        border-radius: {SPACING['sm']}px;
        padding: {SPACING['md']}px;
    }}
    
    QLabel#metricValue {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORS['primary']};
    }}
    
    QLabel#metricLabel {{
        font-size: 14px;
        color: {COLORS['text']['secondary']};
    }}
"""

# Progress bar styles
PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        border: none;
        border-radius: {SPACING['xs']}px;
        background-color: {COLORS['background']};
        height: 8px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['accent']};
        border-radius: {SPACING['xs']}px;
    }}
"""

def set_dark_theme(app):
    """Apply dark theme to the application."""
    dark_palette = QPalette()
    
    # Set color roles
    dark_palette.setColor(QPalette.Window, QColor("#1a1a1a"))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor("#2d2d2d"))
    dark_palette.setColor(QPalette.AlternateBase, QColor("#353535"))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor("#353535"))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor("#4299E1"))
    dark_palette.setColor(QPalette.Highlight, QColor("#4299E1"))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    app.setPalette(dark_palette)
    
    # Update color scheme for dark theme
    global COLORS
    COLORS.update({
        'primary': '#4299E1',     # Bright blue
        'secondary': '#2D3748',   # Dark blue-gray
        'accent': '#4299E1',      # Bright blue
        'background': '#1a1a1a',  # Dark gray
        'surface': '#2d2d2d',     # Medium gray
        'text': {
            'primary': '#FFFFFF',   # White
            'secondary': '#A0AEC0', # Light gray
            'disabled': '#4A5568'   # Medium gray
        }
    })