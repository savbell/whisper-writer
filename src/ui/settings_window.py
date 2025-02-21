import os
import sys
from dotenv import set_key, load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QMessageBox, QTabWidget, QWidget, QSizePolicy, QSpacerItem, QToolButton, QStyle, QFileDialog, QTextEdit, QSpinBox, QScrollArea
)
from PyQt5.QtCore import Qt, QCoreApplication, QProcess, pyqtSignal, QMetaObject, QThread, QTimer
from PyQt5.QtGui import QFont, QIntValidator
import sounddevice as sd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow
from utils import ConfigManager
from keyring_manager import KeyringManager
from llm_processor import LLMProcessor
from ui.model_refresh_worker import ModelRefreshWorker

load_dotenv()

class SettingsWindow(BaseWindow):
    settings_closed = pyqtSignal()
    settings_saved = pyqtSignal()

    def __init__(self):
        """Initialize the settings window."""
        super().__init__('Settings', 800, 800)  # Reduced height from 1050 to 800
        self.schema = ConfigManager.get_schema()
        self.llm_processor = None  # Initialize to None
        self.model_combo = None
        self.refresh_thread = None  # Add thread reference
        self.init_settings_ui()
        
        # Check if we're in API mode (no GPU tools available)
        try:
            import faster_whisper
            has_faster_whisper = True
        except ImportError:
            has_faster_whisper = False
        
        try:
            import vosk
            has_vosk = True
        except ImportError:
            has_vosk = False
        
        # If neither is available, set API mode
        if not has_faster_whisper and not has_vosk:
            self.set_api_mode(True)

    def init_settings_ui(self):
        """Initialize the settings user interface."""
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont('Segoe UI', 11))
        self.main_layout.addWidget(self.tabs)

        self.create_tabs()
        self.create_buttons()

        # Connect the use_api checkbox state change
        self.use_api_checkbox = self.findChild(QCheckBox, 'model_options_use_api_input')
        if self.use_api_checkbox:
            self.use_api_checkbox.stateChanged.connect(lambda: self.toggle_api_local_options(self.use_api_checkbox.isChecked()))
            self.toggle_api_local_options(self.use_api_checkbox.isChecked())

    def create_tabs(self):
        """Create tabs for each category in the schema."""
        for category, settings in self.schema.items():
            tab = QWidget()
            
            # Create a scroll area for the tab content
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Create a container widget for the scroll area
            scroll_content = QWidget()
            tab_layout = QVBoxLayout()
            scroll_content.setLayout(tab_layout)
            
            # Add the settings widgets to the scroll content
            self.create_settings_widgets(tab_layout, category, settings)
            
            # Add spacer at the bottom
            tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
            
            # Set the scroll content as the widget for the scroll area
            scroll_area.setWidget(scroll_content)
            
            # Create a layout for the tab to hold the scroll area
            main_tab_layout = QVBoxLayout()
            main_tab_layout.addWidget(scroll_area)
            tab.setLayout(main_tab_layout)
            
            self.tabs.addTab(tab, category.replace('_', ' ').capitalize())

    def create_settings_widgets(self, layout, category, settings):
        """Create widgets for each setting in a category."""
        for sub_category, sub_settings in settings.items():
            if isinstance(sub_settings, dict):
                if 'value' in sub_settings:
                    # This is a direct setting
                    self.add_setting_widget(layout, sub_category, sub_settings, category)
                else:
                    # This is a subcategory with multiple settings
                    for key, meta in sub_settings.items():
                        self.add_setting_widget(layout, key, meta, category, sub_category)

    def create_buttons(self):
        """Create reset and save buttons."""
        reset_button = QPushButton('Reset to saved settings')
        reset_button.setFont(QFont('Segoe UI', 11))
        reset_button.clicked.connect(self.reset_settings)
        self.main_layout.addWidget(reset_button)

        save_button = QPushButton('Save')
        save_button.setFont(QFont('Segoe UI', 11))
        save_button.clicked.connect(self.save_settings)
        self.main_layout.addWidget(save_button)

    def add_setting_widget(self, layout, key, meta, category, sub_category=None):
        """Add a setting widget to the layout."""
        item_layout = QHBoxLayout()
        widget = None
        
        # Special handling for volume reduction to add % symbol
        if key == 'recording_volume_reduction':
            label = QLabel("Recording Volume Reduction:")
            widget = QLineEdit()
            widget.setText(str(meta.get('value', 0)))
            widget.setValidator(QIntValidator(0, 100))  # Only allow integers 0-100
            widget.setPlaceholderText("0-100")
            widget.setToolTip("Reduce system audio volume by this percentage during recording\n"
                             "0% means no reduction\n"
                             "50% means reduce current volume by half\n"
                             "100% means mute audio")
            # Add % label after the input
            percent_label = QLabel("%")
            percent_label.setFont(QFont('Segoe UI', 11))
            item_layout.addWidget(percent_label)
        # Special handling for model fields to clarify their purpose
        elif category == 'llm_post_processing':
            if key == 'model':
                label = QLabel("Cleanup Model:")  # Changed from just "Model:"
            elif key == 'instruction_model':
                label = QLabel("Instruction Model:")
            else:
                label = QLabel(f"{key.replace('_', ' ').capitalize()}:")
        else:
            label = QLabel(f"{key.replace('_', ' ').capitalize()}:")
        
        # Create widget if not already created
        widget = self.create_widget_for_type(key, meta, category, sub_category)
        if not widget:
            return

        # Set larger font for the widget if it's a text-based widget
        if isinstance(widget, (QLineEdit, QComboBox, QTextEdit, QSpinBox)):
            widget.setFont(QFont('Segoe UI', 11))

        label.setFont(QFont('Segoe UI', 11))
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        help_button = self.create_help_button(meta.get('description', ''))

        item_layout.addWidget(label)
        item_layout.addWidget(widget)
        item_layout.addWidget(help_button)
        layout.addLayout(item_layout)

        # Set object names for the widget, label, and help button
        widget_name = f"{category}_{sub_category}_{key}_input" if sub_category else f"{category}_{key}_input"
        label_name = f"{category}_{sub_category}_{key}_label" if sub_category else f"{category}_{key}_label"
        help_name = f"{category}_{sub_category}_{key}_help" if sub_category else f"{category}_{key}_help"
        
        label.setObjectName(label_name)
        help_button.setObjectName(help_name)
        
        if isinstance(widget, QWidget):
            widget.setObjectName(widget_name)
        else:
            # If it's a layout (for model_path), set the object name on the QLineEdit
            line_edit = widget.itemAt(0).widget()
            if isinstance(line_edit, QLineEdit):
                line_edit.setObjectName(widget_name)

    def create_widget_for_type(self, key, meta, category, sub_category):
        """Create a widget based on the meta type."""
        meta_type = meta.get('type')
        current_value = self.get_config_value(category, sub_category, key, meta)

        # Special handling for find replace file
        if category == 'post_processing' and key == 'find_replace_file':
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            file_edit = QLineEdit()
            file_edit.setFont(QFont('Segoe UI', 11))
            file_edit.setPlaceholderText("Select find/replace rules file...")
            if current_value:
                file_edit.setText(current_value)
            
            browse_button = QPushButton('Browse')
            browse_button.setFont(QFont('Segoe UI', 11))
            browse_button.clicked.connect(lambda: self.browse_find_replace_file(file_edit))
            
            layout.addWidget(file_edit)
            layout.addWidget(browse_button)
            
            return container

        # Special handling for sound device selection
        if category == 'recording_options' and key == 'sound_device':
            combo = QComboBox()
            combo.setFont(QFont('Segoe UI', 11))
            devices = self.get_available_sound_devices()
            default_index = None  # Initialize default_index
            
            for device in devices:
                combo.addItem(device['name'], device['index'])
                if device['default']:
                    default_index = device['index']
            
            # Set current value if it exists, otherwise use default device if available
            if current_value is not None:
                index = combo.findData(int(current_value))
                if index >= 0:
                    combo.setCurrentIndex(index)
            elif default_index is not None:  # Only try to set default if one was found
                index = combo.findData(default_index)
                if index >= 0:
                    combo.setCurrentIndex(index)
            elif combo.count() > 0:  # If no default, but we have devices, select the first one
                combo.setCurrentIndex(0)
                
            return combo

        if category == 'llm_post_processing':
            if key in ['text_cleanup_system_message', 'instruction_system_message', 'system_prompt']:
                container = QWidget()
                layout = QVBoxLayout()
                container.setLayout(layout)
                
                # Text edit for system message
                text_edit = QTextEdit()
                text_edit.setPlaceholderText(f"Enter system message for {key.replace('_', ' ')}")
                text_edit.setText(current_value or '')
                text_edit.setMinimumHeight(100)
                text_edit.setFont(QFont('Segoe UI', 11))
                
                # File path selection
                file_layout = QHBoxLayout()
                file_edit = QLineEdit()
                file_edit.setPlaceholderText("Optional: Path to system message file")
                file_edit.setObjectName(f"{key}_file_path")
                
                # Load the saved file path
                saved_file_path = ConfigManager.get_config_value("llm_post_processing", f"{key}_file_path")
                if saved_file_path:
                    file_edit.setText(saved_file_path)
                
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda: self.browse_system_message_file(file_edit, text_edit))
                
                file_layout.addWidget(file_edit)
                file_layout.addWidget(browse_btn)
                
                layout.addWidget(text_edit)
                layout.addLayout(file_layout)
                
                return container
            
            elif key == 'api_type':
                widget = self.create_combobox(current_value, meta['options'])
                widget.setObjectName('llm_post_processing_api_type_input')
                widget.currentTextChanged.connect(self.refresh_model_choices)
                return widget
            elif key in ['cleanup_model', 'instruction_model']:
                widget = QLineEdit(current_value or '')
                widget.setObjectName(f'llm_post_processing_{key}_input')
                widget.setPlaceholderText(f"Enter {key.replace('_', ' ')} name")
                return widget
            elif key == 'model':
                widget = QLineEdit(current_value or '')
                widget.setObjectName('llm_post_processing_model_input')
                widget.setPlaceholderText("Enter model name (e.g. gpt-4o-mini for OpenAI, llama3.2 for Ollama)")
                return widget

        if meta_type == 'bool':
            return self.create_checkbox(current_value, key)
        elif meta_type == 'str' and 'options' in meta:
            return self.create_combobox(current_value, meta['options'])
        elif meta_type == 'str':
            is_api_key = key.endswith('api_key')
            return self.create_line_edit(current_value, key, is_api_key)
        elif meta_type in ['int', 'float']:
            return self.create_line_edit(str(current_value))
        return None

    def create_checkbox(self, value, key):
        widget = QCheckBox()
        widget.setChecked(value)
        if key == 'use_api':
            widget.setObjectName('model_options_use_api_input')
        return widget

    def create_combobox(self, value, options):
        widget = QComboBox()
        widget.addItems(options)
        widget.setCurrentText(value)
        return widget

    def create_line_edit(self, value, key=None, password_mode=False):
        widget = QLineEdit(value)
        
        if password_mode:
            widget.setEchoMode(QLineEdit.Password)
            # Load appropriate API key from keyring
            if key == 'openai_transcription_api_key':
                widget.setText(KeyringManager.get_api_key("openai_transcription") or value)
            elif key == 'deepgram_transcription_api_key':
                widget.setText(KeyringManager.get_api_key("deepgram_transcription") or value)
            elif key == 'groq_transcription_api_key':
                widget.setText(KeyringManager.get_api_key("groq_transcription") or value)
            elif key == 'claude_api_key':
                widget.setText(KeyringManager.get_api_key("claude") or value)
            elif key == 'openai_api_key':
                widget.setText(KeyringManager.get_api_key("openai_llm") or value)
            elif key == 'gemini_api_key':
                widget.setText(KeyringManager.get_api_key("gemini") or value)
            elif key == 'groq_api_key':
                widget.setText(KeyringManager.get_api_key("groq") or value)
        elif key == 'model_path':
            widget.setPlaceholderText("Optional: Path to local model file")
        
        return widget

    def create_help_button(self, description):
        help_button = QToolButton()
        help_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        help_button.setAutoRaise(True)
        help_button.setToolTip(description)
        help_button.setCursor(Qt.PointingHandCursor)
        help_button.setFocusPolicy(Qt.TabFocus)
        help_button.clicked.connect(lambda: self.show_description(description))
        return help_button

    def get_config_value(self, category, sub_category, key, meta):
        if sub_category:
            return ConfigManager.get_config_value(category, sub_category, key) or meta['value']
        return ConfigManager.get_config_value(category, key) or meta['value']

    def browse_model_path(self, widget):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Whisper Model File", "", "Model Files (*.bin);;All Files (*)")
        if file_path:
            widget.setText(file_path)

    def show_description(self, description):
        """Show a description dialog."""
        QMessageBox.information(self, 'Description', description)

    def save_settings(self):
        """Save the settings to the config file and keyring."""
        ConfigManager.console_print("Saving settings...")
        self.iterate_settings(self.save_setting)

        # Save API keys to keyring
        openai_transcription_key = ConfigManager.get_config_value('model_options', 'api', 'openai_transcription_api_key') or ''
        deepgram_transcription_key = ConfigManager.get_config_value('model_options', 'api', 'deepgram_transcription_api_key') or ''
        groq_transcription_key = ConfigManager.get_config_value('model_options', 'api', 'groq_transcription_api_key') or ''
        claude_api_key = ConfigManager.get_config_value('llm_post_processing', 'claude_api_key') or ''
        openai_llm_key = ConfigManager.get_config_value('llm_post_processing', 'openai_api_key') or ''
        gemini_api_key = ConfigManager.get_config_value('llm_post_processing', 'gemini_api_key') or ''
        groq_api_key = ConfigManager.get_config_value('llm_post_processing', 'groq_api_key') or ''
        
        # Save to keyring
        KeyringManager.save_api_key("openai_transcription", openai_transcription_key)
        KeyringManager.save_api_key("deepgram_transcription", deepgram_transcription_key)
        KeyringManager.save_api_key("groq_transcription", groq_transcription_key)
        KeyringManager.save_api_key("claude", claude_api_key)
        KeyringManager.save_api_key("openai_llm", openai_llm_key)
        KeyringManager.save_api_key("gemini", gemini_api_key)
        KeyringManager.save_api_key("groq", groq_api_key)
        
        # Remove API keys from config
        ConfigManager.set_config_value(None, 'model_options', 'api', 'openai_transcription_api_key')
        ConfigManager.set_config_value(None, 'model_options', 'api', 'deepgram_transcription_api_key')
        ConfigManager.set_config_value(None, 'model_options', 'api', 'groq_transcription_api_key')
        ConfigManager.set_config_value(None, 'llm_post_processing', 'claude_api_key')
        ConfigManager.set_config_value(None, 'llm_post_processing', 'openai_api_key')
        ConfigManager.set_config_value(None, 'llm_post_processing', 'gemini_api_key')
        ConfigManager.set_config_value(None, 'llm_post_processing', 'groq_api_key')

        ConfigManager.save_config()
        
        QMessageBox.information(self, 'Settings Saved', 'Settings have been saved. The application will now restart.')
        self.settings_saved.emit()
        self.close()

    def save_setting(self, widget, category, sub_category, key, meta):
        """Save a single setting to the config."""
        if isinstance(widget, QWidget) and widget.layout():
            layout = widget.layout()
            text_edit = None
            file_edit = None
            
            # Find both the text edit and file edit widgets
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if isinstance(item.widget(), QTextEdit):
                    text_edit = item.widget()
                elif isinstance(item.widget(), QLineEdit):  # Direct QLineEdit check
                    file_edit = item.widget()
                elif isinstance(item.layout(), QHBoxLayout):
                    for j in range(item.layout().count()):
                        file_widget = item.layout().itemAt(j).widget()
                        if isinstance(file_widget, QLineEdit):
                            file_edit = file_widget
                            break
            
            # Save both the text content and file path
            if text_edit:
                value = text_edit.toPlainText()
                ConfigManager.console_print(f"Saving {category}.{key} with value: {value}")
                ConfigManager.set_config_value(value, category, key)
            
            if file_edit:
                file_path = file_edit.text()
                if category == 'post_processing' and key == 'find_replace_file':
                    # Direct save for find/replace file path
                    ConfigManager.console_print(f"Saving {category}.{key} with value: {file_path}")
                    ConfigManager.set_config_value(file_path, category, key)
                else:
                    # For other file paths that use the _file_path suffix
                    ConfigManager.console_print(f"Saving {category}.{key}_file_path with value: {file_path}")
                    ConfigManager.set_config_value(file_path, category, f"{key}_file_path")
            
            return

        # Special handling for sound device combo box
        if category == 'recording_options' and key == 'sound_device' and isinstance(widget, QComboBox):
            value = widget.currentData()  # Get the device index
            ConfigManager.console_print(f"Saving sound device selection: {value} ({widget.currentText()})")
        else:
            # Handle regular widgets
            value = self.get_widget_value_typed(widget, meta.get('type'))
        
        if sub_category:
            ConfigManager.set_config_value(value, category, sub_category, key)
        else:
            ConfigManager.set_config_value(value, category, key)

    def reset_settings(self):
        """Reset the settings to the saved values."""
        ConfigManager.reload_config()
        self.update_widgets_from_config()

    def update_widgets_from_config(self):
        """Update all widgets with values from the current configuration."""
        ConfigManager.console_print("Updating widgets from config...")
        
        # Load API keys from keyring
        whisper_key = KeyringManager.get_api_key("whisper")
        claude_key = KeyringManager.get_api_key("claude")
        openai_key = KeyringManager.get_api_key("openai_llm")
        gemini_key = KeyringManager.get_api_key("gemini")
        groq_key = KeyringManager.get_api_key("groq")
        
        ConfigManager.console_print("Loading API keys from keyring...")
        
        self.iterate_settings(self.update_widget_value)
        
        # Update API key fields
        for widget, category, sub_category, key, _ in self.iterate_settings():
            if category == 'model_options' and sub_category == 'api' and key == 'api_key':
                widget.setText(whisper_key)
                ConfigManager.console_print("Set Whisper API key widget")
            elif category == 'llm_post_processing':
                if key == 'claude_api_key':
                    widget.setText(claude_key)
                    ConfigManager.console_print("Set Claude API key widget")
                elif key == 'openai_api_key':
                    widget.setText(openai_key)
                    ConfigManager.console_print("Set OpenAI LLM key widget")
                elif key == 'gemini_api_key':
                    widget.setText(gemini_key)
                    ConfigManager.console_print("Set Gemini API key widget")    
                elif key == 'groq_api_key':
                    widget.setText(groq_key)
                    ConfigManager.console_print("Set Groq API key widget")

    def update_widget_value(self, widget, category, sub_category, key, meta):
        """Update a single widget with its value from the config."""
        # Skip API key fields as they're handled separately
        if (category == 'model_options' and sub_category == 'api' and key == 'api_key') or \
           (category == 'llm_post_processing' and key == 'api_key'):
            return
        
        value = self.get_config_value(category, sub_category, key, meta)
        self.set_widget_value(widget, value, meta.get('type'))

    def set_widget_value(self, widget, value, value_type):
        """Set the value of the widget."""
        if isinstance(widget, QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else '')
        elif isinstance(widget, QTextEdit):  # Add handling for QTextEdit
            widget.setText(str(value) if value is not None else '')
        elif isinstance(widget, QWidget) and widget.layout():
            # This is for the model_path widget
            line_edit = widget.layout().itemAt(0).widget()
            if isinstance(line_edit, QLineEdit):
                line_edit.setText(str(value) if value is not None else '')

    def get_widget_value_typed(self, widget, value_type):
        """Get the value of the widget with proper typing."""
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            return widget.currentText() or None
        elif isinstance(widget, QLineEdit):
            text = widget.text()
            if value_type == 'int':
                return int(text) if text else None
            elif value_type == 'float':
                return float(text) if text else None
            else:
                return text or None
        elif isinstance(widget, QTextEdit):  # Add handling for QTextEdit
            return widget.toPlainText() or None
        elif isinstance(widget, QWidget) and widget.layout():
            # This is for the model_path widget
            line_edit = widget.layout().itemAt(0).widget()
            if isinstance(line_edit, QLineEdit):
                return line_edit.text() or None
        return None

    def toggle_api_local_options(self, use_api):
        """Toggle visibility of API and local options."""
        self.iterate_settings(lambda w, c, s, k, m: self.toggle_widget_visibility(w, c, s, k, use_api))

    def toggle_widget_visibility(self, widget, category, sub_category, key, use_api):
        if sub_category in ['api', 'local']:
            widget.setVisible(use_api if sub_category == 'api' else not use_api)
            
            # Also toggle visibility of the corresponding label and help button
            label = self.findChild(QLabel, f"{category}_{sub_category}_{key}_label")
            help_button = self.findChild(QToolButton, f"{category}_{sub_category}_{key}_help")
            
            if label:
                label.setVisible(use_api if sub_category == 'api' else not use_api)
            if help_button:
                help_button.setVisible(use_api if sub_category == 'api' else not use_api)

    def iterate_settings(self, func):
        """Iterate over all settings and apply a function to each."""
        for category, settings in self.schema.items():
            for sub_category, sub_settings in settings.items():
                if isinstance(sub_settings, dict) and 'value' in sub_settings:
                    widget = self.findChild(QWidget, f"{category}_{sub_category}_input")
                    if widget:
                        func(widget, category, None, sub_category, sub_settings)
                else:
                    for key, meta in sub_settings.items():
                        widget = self.findChild(QWidget, f"{category}_{sub_category}_{key}_input")
                        if widget:
                            func(widget, category, sub_category, key, meta)

    def handleCloseButton(self):
        """Override base window close button handler to hide instead of close."""
        ConfigManager.console_print("Settings window closing via X button")
        self.settings_closed.emit()
        self.hide()

    def reject(self):
        """Handle when the window is closed without saving (e.g., Escape key or X button)."""
        self.settings_closed.emit()
        self.hide()

    def load_settings(self):
        """Load settings from config and keyring."""
        # Get API keys from keyring
        openai_transcription_key = KeyringManager.get_api_key("openai_transcription") or ''
        deepgram_transcription_key = KeyringManager.get_api_key("deepgram_transcription") or ''
        groq_transcription_key = KeyringManager.get_api_key("groq_transcription") or ''
        claude_key = KeyringManager.get_api_key("claude") or ''
        openai_key = KeyringManager.get_api_key("openai_llm") or ''
        gemini_key = KeyringManager.get_api_key("gemini") or ''
        groq_key = KeyringManager.get_api_key("groq") or ''

        # Update API key fields
        for widget, category, sub_category, key, _ in self.iterate_settings():
            if category == 'model_options' and sub_category == 'api':
                if key == 'openai_transcription_api_key':
                    widget.setText(openai_transcription_key)
                elif key == 'deepgram_transcription_api_key':
                    widget.setText(deepgram_transcription_key)
                elif key == 'groq_transcription_api_key':
                    widget.setText(groq_transcription_key)
            elif category == 'llm_post_processing':
                if key == 'claude_api_key':
                    widget.setText(claude_key)
                elif key == 'openai_api_key':
                    widget.setText(openai_key)
                elif key == 'gemini_api_key':
                    widget.setText(gemini_key)
                elif key == 'groq_api_key':
                    widget.setText(groq_key)

    def create_model_selector(self):
        """Create text fields for model selection."""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the text fields
        self.cleanup_model_input = QLineEdit()
        self.cleanup_model_input.setObjectName('llm_post_processing_cleanup_model_input')
        
        self.instruction_model_input = QLineEdit()
        self.instruction_model_input.setObjectName('llm_post_processing_instruction_model_input')
        
        # Add to layout
        layout.addWidget(self.cleanup_model_input)
        layout.addWidget(self.instruction_model_input)
        
        container.setLayout(layout)
        return container

    def refresh_model_choices(self, combo_box=None):
        """Refresh the model choices based on the selected API type."""
        ConfigManager.console_print("\n=== Starting Model Refresh ===")
        ConfigManager.console_print(f"Combo box type: {type(combo_box)}")
        
        api_type_combo = self.findChild(QComboBox, 'llm_post_processing_api_type_input')
        if not api_type_combo:
            ConfigManager.console_print("Error: API type combo box not found")
            return
            
        api_type = api_type_combo.currentText()
        ConfigManager.console_print(f"Selected API type: {api_type}")
        
        # Initialize LLM processor if needed
        if not self.llm_processor:
            ConfigManager.console_print("Initializing LLM processor...")
            self.llm_processor = LLMProcessor(api_type=api_type)
        else:
            self.llm_processor.api_type = api_type
        
        # Find the combo boxes in the UI
        cleanup_combo = self.findChild(QComboBox, 'llm_post_processing_cleanup_model_input')
        instruction_combo = self.findChild(QComboBox, 'llm_post_processing_instruction_model_input')
        
        ConfigManager.console_print(f"Found cleanup combo: {cleanup_combo}")
        ConfigManager.console_print(f"Found instruction combo: {instruction_combo}")
        
        # If a specific combo box was passed, only update that one
        if combo_box and isinstance(combo_box, QComboBox):
            combos_to_update = [combo_box]
        else:
            combos_to_update = []
            if cleanup_combo:
                combos_to_update.append(cleanup_combo)
            if instruction_combo:
                combos_to_update.append(instruction_combo)
        
        ConfigManager.console_print(f"Will update {len(combos_to_update)} combo boxes")
        ConfigManager.console_print(f"Combo boxes to update: {[combo.objectName() for combo in combos_to_update]}")
        
        # Try fetching models
        try:
            models = self.llm_processor.get_available_models(api_type)
            ConfigManager.console_print(f"Direct fetch results: {models}")
            if models:
                self.update_model_combos(models, combos_to_update)
        except Exception as e:
            ConfigManager.console_print(f"Error fetching models: {str(e)}")

    def update_model_combos(self, models, combos_to_update):
        """Update combo boxes with fetched models."""
        ConfigManager.console_print("\n=== Updating Model Combos ===")
        ConfigManager.console_print(f"Received models: {models}")
        ConfigManager.console_print(f"Number of combos to update: {len(combos_to_update)}")
        ConfigManager.console_print(f"Combo boxes to update: {[combo.objectName() for combo in combos_to_update]}")
        
        # Ensure we're on the main thread
        if QThread.currentThread() != QApplication.instance().thread():
            ConfigManager.console_print("Warning: Updating from background thread, moving to main thread")
            QApplication.instance().processEvents()
        
        for combo in combos_to_update:
            if not combo:
                ConfigManager.console_print("Error: Null combo box encountered")
                continue
            
            if not isinstance(combo, QComboBox):
                ConfigManager.console_print(f"Error: Invalid combo box type: {type(combo)}")
                continue
            
            ConfigManager.console_print(f"\nUpdating combo box: {combo.objectName()}")
            ConfigManager.console_print(f"Combo box exists: {combo is not None}")
            ConfigManager.console_print(f"Combo box visible: {combo.isVisible()}")
            ConfigManager.console_print(f"Combo box enabled: {combo.isEnabled()}")
            ConfigManager.console_print(f"Current items: {[combo.itemText(i) for i in range(combo.count())]}")
            
            # Store current state
            was_enabled = combo.isEnabled()
            current_text = combo.currentText()
            ConfigManager.console_print(f"Current state - enabled: {was_enabled}, text: {current_text}")
            
            # Block signals and clear
            combo.blockSignals(True)
            combo.clear()
            ConfigManager.console_print("Cleared combo box")
            
            if models:
                ConfigManager.console_print(f"Adding {len(models)} models to combo box")
                for model in models:
                    combo.addItem(str(model))
                    ConfigManager.console_print(f"Added model: {model}")
                
                # Get the appropriate config value
                config_key = 'cleanup_model' if combo == self.cleanup_model_combo else 'instruction_model'
                current_model = ConfigManager.get_config_value('llm_post_processing', config_key)
                ConfigManager.console_print(f"Config model: {current_model}")
                
                if current_model in models:
                    combo.setCurrentText(current_model)
                    ConfigManager.console_print(f"Set to config model: {current_model}")
                else:
                    combo.setCurrentIndex(0)
                    ConfigManager.console_print(f"Set to first model: {combo.currentText()}")
            else:
                message = "No models found - Is Ollama running?" if self.llm_processor.api_type == 'ollama' else "No models available - Check API key"
                combo.addItem(message)
                ConfigManager.console_print(f"Added message: {message}")
            
            # Restore state and force update
            combo.setEnabled(True)
            combo.blockSignals(False)
            combo.repaint()
            
            # Verify final state
            ConfigManager.console_print(f"Final state - count: {combo.count()}")
            ConfigManager.console_print(f"Final items: {[combo.itemText(i) for i in range(combo.count())]}")
            ConfigManager.console_print(f"Current text: {combo.currentText()}")
            ConfigManager.console_print(f"Enabled: {combo.isEnabled()}")
            ConfigManager.console_print(f"Visible: {combo.isVisible()}")
        
        # Force a UI update
        QApplication.processEvents()
        ConfigManager.console_print("=== UI update complete ===\n")

    def showEvent(self, event):
        """Handle window show event to initialize models."""
        super().showEvent(event)
        if self.model_combo:
            self.refresh_model_choices()

    def browse_system_message_file(self, file_edit, text_edit):
        """Browse for a system message file and load its contents."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select System Message File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            file_edit.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    current_text = text_edit.toPlainText()
                    if current_text:
                        text_edit.setText(f"{current_text}\n\n{content}")
                    else:
                        text_edit.setText(content)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to read file: {str(e)}")

    def set_api_mode(self, use_api: bool):
        """Set the API mode checkbox state."""
        use_api_checkbox = self.findChild(QCheckBox, 'model_options_use_api_input')
        if use_api_checkbox:
            use_api_checkbox.setChecked(use_api)
            self.toggle_api_local_options(use_api)

    def get_available_sound_devices(self):
        """Get list of available sound devices that support recording."""
        try:
            devices = sd.query_devices()
            input_devices = []
            for i, device in enumerate(devices):
                try:
                    # Test if we can open an input stream with this device
                    with sd.InputStream(device=i, channels=1, samplerate=16000, blocksize=1024):
                        pass  # If we get here, the device works for recording
                    
                    if device['max_input_channels'] > 0:  # Only include input devices
                        name = f"{i}: {device['name']}"
                        input_devices.append({
                            'index': i,
                            'name': name,
                            'channels': device['max_input_channels'],
                            'default': device is sd.default.device[0]
                        })
                except sd.PortAudioError as e:
                    # ConfigManager.console_print(f"Device {i}: {device['name']} not suitable for recording: {str(e)}")
                    continue
                
            return input_devices
        except Exception as e:
            ConfigManager.console_print(f"Error getting sound devices: {str(e)}")
            return []

    def browse_find_replace_file(self, file_edit):
        """Browse for a find/replace rules file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Find/Replace Rules File", 
            "", 
            "Rule Files (*.txt *.json);;Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            file_edit.setText(file_path)
