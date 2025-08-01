import os
import sys
from dotenv import set_key, load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QMessageBox, QTabWidget, QWidget, QSizePolicy, QSpacerItem, QToolButton, QStyle, QFileDialog
)
from PyQt5.QtCore import Qt, QCoreApplication, QProcess, pyqtSignal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow
from utils import ConfigManager

load_dotenv()

class SettingsWindow(BaseWindow):
    settings_closed = pyqtSignal()
    settings_saved = pyqtSignal()

    def __init__(self):
        """Initialize the settings window."""
        super().__init__('WhisperWit Settings', 700, 700)
        self.schema = ConfigManager.get_schema()
        self.init_settings_ui()

    def init_settings_ui(self):
        """Initialize the settings user interface."""
        self.tabs = QTabWidget()
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
            tab_layout = QVBoxLayout()
            tab.setLayout(tab_layout)
            self.tabs.addTab(tab, category.replace('_', ' ').capitalize())

            self.create_settings_widgets(tab_layout, category, settings)
            tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def create_settings_widgets(self, layout, category, settings):
        """Create widgets for each setting in a category."""
        for sub_category, sub_settings in settings.items():
            if isinstance(sub_settings, dict) and 'value' in sub_settings:
                self.add_setting_widget(layout, sub_category, sub_settings, category)
            else:
                for key, meta in sub_settings.items():
                    self.add_setting_widget(layout, key, meta, category, sub_category)

    def create_buttons(self):
        """Create reset, save, and test microphone buttons."""
        reset_button = QPushButton('Reset to saved settings')
        reset_button.clicked.connect(self.reset_settings)
        self.main_layout.addWidget(reset_button)

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_settings)
        self.main_layout.addWidget(save_button)

        test_button = QPushButton('Test Microphone')
        test_button.clicked.connect(self.test_microphone)
        self.main_layout.addWidget(test_button)

    def test_microphone(self):
        """
        Test the selected microphone by recording and playing back a short audio clip.
        """
        try:
            import sounddevice as sd
            from PyQt5.QtWidgets import QMessageBox
            sample_rate = ConfigManager.get_config_value('recording_options', 'sample_rate')
            if not sample_rate:
                sample_rate = 16000
            duration = 3  # seconds
            QMessageBox.information(self, "Test Microphone", "Recording for 3 seconds. Please speak into your microphone.")
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
            sd.wait()
            QMessageBox.information(self, "Test Microphone", "Playback starting. Listen to the recorded audio.")
            sd.play(recording, samplerate=sample_rate)
            sd.wait()
            QMessageBox.information(self, "Test Microphone", "Microphone test completed.")
        except Exception as e:
            QMessageBox.critical(self, "Test Microphone Error", f"An error occurred during the microphone test: {str(e)}")

    def test_microphone(self):
        """
        Test the selected microphone by recording and playing back a short audio clip.
        Shows a volume level indicator during recording.
        """
        try:
            import sounddevice as sd
            import numpy as np
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QLabel
            from PyQt5.QtCore import QTimer
            
            # Create a dialog with a volume meter
            dialog = QDialog(self)
            dialog.setWindowTitle("Microphone Test")
            layout = QVBoxLayout()
            
            label = QLabel("Recording... Speak into your microphone")
            layout.addWidget(label)
            
            volume_bar = QProgressBar()
            volume_bar.setMinimum(0)
            volume_bar.setMaximum(100)
            volume_bar.setValue(0)
            layout.addWidget(volume_bar)
            
            dialog.setLayout(layout)
            
            # Setup recording parameters
            sample_rate = ConfigManager.get_config_value('recording_options', 'sample_rate') or 16000
            duration = 3  # seconds
            recording = []
            
            def update_volume():
                if len(recording) > 0:
                    # Calculate volume level from the most recent chunk
                    chunk = recording[-1]
                    volume = int(np.abs(chunk).mean() * 100)
                    volume_bar.setValue(min(100, volume))
            
            def input_callback(indata, frames, time, status):
                recording.append(indata.copy())
                
            # Start recording with callback
            stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                callback=input_callback,
                dtype=np.float32
            )
            
            # Update volume meter every 50ms
            timer = QTimer()
            timer.timeout.connect(update_volume)
            timer.start(50)
            
            with stream:
                dialog.exec_()  # Show dialog during recording
                
            # Stop the timer
            timer.stop()
            
            # Combine all recorded chunks
            if recording:
                full_recording = np.concatenate(recording)
                
                # Play back the recording
                sd.play(full_recording, samplerate=sample_rate)
                sd.wait()
                
        except Exception as e:
            QMessageBox.critical(self, "Test Microphone Error", f"An error occurred during the microphone test: {str(e)}")

    def add_setting_widget(self, layout, key, meta, category, sub_category=None):
        """Add a setting widget to the layout."""
        item_layout = QHBoxLayout()
        label = QLabel(f"{key.replace('_', ' ').capitalize()}:")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        widget = self.create_widget_for_type(key, meta, category, sub_category)
        if not widget:
            return

        help_button = self.create_help_button(meta.get('description', ''))

        item_layout.addWidget(label)
        if isinstance(widget, QWidget):
            item_layout.addWidget(widget)
        else:
            item_layout.addLayout(widget)
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
        
        # Special handling for selecting the input recording device
        if key == 'sound_device' and category == 'recording_options':
            return self.create_sound_device_combobox(current_value)
        
        if meta_type == 'bool':
            return self.create_checkbox(current_value, key)
        elif meta_type == 'str' and 'options' in meta:
            return self.create_combobox(current_value, meta['options'])
        elif meta_type == 'str':
            return self.create_line_edit(current_value, key)
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

    def create_line_edit(self, value, key=None):
        widget = QLineEdit(value)
        if key == 'api_key':
            widget.setEchoMode(QLineEdit.Password)
            widget.setText(os.getenv('OPENAI_API_KEY') or value)
        elif key == 'model_path':
            layout = QHBoxLayout()
            layout.addWidget(widget)
            browse_button = QPushButton('Browse')
            browse_button.clicked.connect(lambda: self.browse_model_path(widget))
            layout.addWidget(browse_button)
            layout.setContentsMargins(0, 0, 0, 0)
            container = QWidget()
            container.setLayout(layout)
            return container
        elif key == 'activation_key':
            widget.setReadOnly(True)
            widget.setPlaceholderText("Click here and press your desired key combination")
            
            def mouse_press(e):
                self.start_key_capture(widget)
                widget.grabKeyboard()  # Ensure we capture all keyboard input
                
            def focus_out(e):
                widget.releaseKeyboard()
                self.stop_key_capture(widget)
                
            def key_press(e):
                self.handle_key_press(e, widget)
                e.accept()  # Ensure the event is processed
                
            widget.mousePressEvent = mouse_press
            widget.focusOutEvent = focus_out
            widget.keyPressEvent = key_press
        return widget

    def start_key_capture(self, widget):
        """Start capturing keyboard input for the activation key."""
        widget.clear()
        widget.setPlaceholderText("Press your desired key combination...")
        widget.key_combination = set()

    def stop_key_capture(self, widget):
        """Stop capturing keyboard input."""
        if hasattr(widget, 'key_combination'):
            if not widget.text():
                widget.setPlaceholderText("Click here and press your desired key combination")
            delattr(widget, 'key_combination')

    def handle_key_press(self, event, widget):
        """Handle key press events for the activation key field."""
        if not hasattr(widget, 'key_combination'):
            return

        modifiers = event.modifiers()
        key = event.key()
        
        # Clear existing combination if starting a new one
        if not widget.key_combination:
            widget.key_combination = set()

        # Handle modifier keys
        if modifiers & Qt.ControlModifier:
            widget.key_combination.add('ctrl')
        if modifiers & Qt.ShiftModifier:
            widget.key_combination.add('shift')
        if modifiers & Qt.AltModifier:
            widget.key_combination.add('alt')

        # Handle special keys
        if key == Qt.Key_Space:
            widget.key_combination.add('space')
        elif key == Qt.Key_CapsLock:
            widget.key_combination.add('capslock')
        elif key == Qt.Key_Escape:
            widget.clear()
            self.stop_key_capture(widget)
            return
        elif key not in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt]:
            # For regular keys, use their text representation or key name for special keys
            if key in [Qt.Key_F1, Qt.Key_F2, Qt.Key_F3, Qt.Key_F4, Qt.Key_F5,
                      Qt.Key_F6, Qt.Key_F7, Qt.Key_F8, Qt.Key_F9, Qt.Key_F10,
                      Qt.Key_F11, Qt.Key_F12]:
                widget.key_combination.add(f'f{key - Qt.Key_F1 + 1}')
            else:
                key_text = event.text().lower()
                if key_text:
                    widget.key_combination.add(key_text)

        # Update the text field with the current combination
        if widget.key_combination:
            combination = '+'.join(sorted(widget.key_combination))
            widget.setText(combination)
    
    def create_sound_device_combobox(self, current_value):
        """
        Create a combobox widget for selecting an input recording device.
        Automatically selects the Windows default input device.
        """
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            default_device = sd.query_devices(kind='input')
            default_index = default_device.get('index', 0)
            
            widget = QComboBox()
            widget.setEnabled(False)  # Make it read-only since we're using system default
            widget.addItem(f"{default_device.get('name', 'Default Input Device')} (System Default)")
            
            # Store the default device index as the value
            widget.setProperty("device_index", default_index)
            return widget
            
        except Exception:
            widget = QComboBox()
            widget.addItem("Using System Default Input Device")
            widget.setEnabled(False)
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
        """Save the settings to the config file and .env file."""
        self.iterate_settings(self.save_setting)

        # Save the API key to the .env file
        api_key = ConfigManager.get_config_value('model_options', 'api', 'api_key') or ''
        set_key('.env', 'OPENAI_API_KEY', api_key)
        os.environ['OPENAI_API_KEY'] = api_key

        # Remove the API key from the config
        ConfigManager.set_config_value(None, 'model_options', 'api', 'api_key')

        ConfigManager.save_config()
        QMessageBox.information(self, 'Settings Saved', 'Settings have been saved. The application will now restart.')
        self.settings_saved.emit()
        self.close()

    def save_setting(self, widget, category, sub_category, key, meta):
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
        self.iterate_settings(self.update_widget_value)

    def update_widget_value(self, widget, category, sub_category, key, meta):
        """Update a single widget with the value from the configuration."""
        if sub_category:
            config_value = ConfigManager.get_config_value(category, sub_category, key)
        else:
            config_value = ConfigManager.get_config_value(category, key)

        self.set_widget_value(widget, config_value, meta.get('type'))

    def set_widget_value(self, widget, value, value_type):
        """Set the value of the widget."""
        if isinstance(widget, QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        elif isinstance(widget, QLineEdit):
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

    def closeEvent(self, event):
        """Confirm before closing the settings window without saving."""
        reply = QMessageBox.question(
            self,
            'Close without saving?',
            'Are you sure you want to close without saving?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            ConfigManager.reload_config()  # Revert to last saved configuration
            self.update_widgets_from_config()
            self.settings_closed.emit()
            super().closeEvent(event)
        else:
            event.ignore()
