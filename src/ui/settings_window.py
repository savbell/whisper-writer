import os
import sys
from dotenv import set_key, load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QMessageBox, QTabWidget, QWidget, QSizePolicy, QSpacerItem, QToolButton, QStyle
)
from PyQt5.QtCore import Qt, QCoreApplication, QProcess, pyqtSignal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow
from utils import load_config_schema, load_config_values, save_config

load_dotenv()

class SettingsWindow(BaseWindow):
    settingsClosed = pyqtSignal()
    
    def __init__(self, schema):
        """
        Initialize the settings window.
        """
        self.schema = schema
        self.config = load_config_values(schema)
        self.initial_config = self.config.copy()
        self.default_config = load_config_values(schema, config_path=None)
        self.api_widgets = []
        self.local_widgets = []
        super().__init__('Settings', 700, 700)
        self.initSettingsUI()

    def initSettingsUI(self):
        """
        Initialize the settings user interface.
        """
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        for category, settings in self.schema.items():
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab.setLayout(tab_layout)
            self.tabs.addTab(tab, category.replace('_', ' ').capitalize())

            for sub_category, sub_settings in settings.items():
                if isinstance(sub_settings, dict) and 'value' in sub_settings:
                    self.add_setting_widget(tab_layout, sub_category, sub_settings, category)
                else:
                    for key, meta in sub_settings.items():
                        self.add_setting_widget(tab_layout, key, meta, category, sub_category)
            
            tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
                        
        reset_button = QPushButton('Reset to default')
        reset_button.clicked.connect(self.resetSettings)
        self.main_layout.addWidget(reset_button)

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.saveSettings)
        self.main_layout.addWidget(save_button)

        # Connect the use_api checkbox state change
        self.use_api_checkbox = self.findChild(QCheckBox, 'transcription_model_options_use_api_input')
        if self.use_api_checkbox:
            self.use_api_checkbox.stateChanged.connect(self.toggle_api_local_options)
            self.toggle_api_local_options(self.use_api_checkbox.isChecked())

    def add_setting_widget(self, layout, key, meta, category, sub_category=None):
        """
        Add a setting widget to the layout.
        """
        item_layout = QHBoxLayout()

        label = QLabel(f"{key.replace('_', ' ').capitalize()}:")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        meta_type = meta.get('type')

        # Retrieve the current value from the loaded config
        if sub_category:
            current_value = self.config.get(category, {}).get(sub_category, {}).get(key, meta['value'])
        else:
            current_value = self.config.get(category, {}).get(key, meta['value'])

        if meta_type == 'bool':
            widget = QCheckBox()
            widget.setChecked(current_value)
            if key == 'use_api':
                widget.setObjectName('transcription_model_options_use_api_input')
        elif meta_type == 'str' and 'options' in meta:
            widget = QComboBox()
            widget.addItems(meta['options'])
            widget.setCurrentText(current_value)
        elif meta_type == 'str':
            widget = QLineEdit(current_value)
            if key == 'api_key':
                widget.setEchoMode(QLineEdit.Password)
                widget.setText(os.getenv('OPENAI_API_KEY') or current_value)
        elif meta_type == 'int':
            widget = QLineEdit(str(current_value))
        elif meta_type == 'float':
            widget = QLineEdit(str(current_value))
        else:
            return

        widget.setToolTip(meta.get('description', ''))
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        help_button = QToolButton()
        help_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        help_button.setAutoRaise(True)
        help_button.setToolTip(meta.get('description', ''))
        help_button.setCursor(Qt.PointingHandCursor)
        help_button.setFocusPolicy(Qt.TabFocus)
        help_button.clicked.connect(lambda: self.show_description(meta.get('description', '')))

        item_layout.addWidget(label)
        item_layout.addWidget(widget)
        item_layout.addWidget(help_button)
        layout.addLayout(item_layout)

        # Use a unique attribute name to avoid conflicts
        if sub_category:
            setattr(self, f"{category}_{sub_category}_{key}_input", widget)
        else:
            setattr(self, f"{category}_{key}_input", widget)

        # Store the widget in the relevant list
        if sub_category == 'api':
            self.api_widgets.append((label, widget, help_button))
        elif sub_category == 'local':
            self.local_widgets.append((label, widget, help_button))

    def show_description(self, description):
        """
        Show a description dialog.
        """
        QMessageBox.information(self, 'Description', description)

    def saveSettings(self):
        """
        Save the settings to the config.yaml file and API key to .env file.
        """
        for category, settings in self.schema.items():
            for sub_category, sub_settings in settings.items():
                if isinstance(sub_settings, dict) and 'value' in sub_settings:
                    widget = getattr(self, f"{category}_{sub_category}_input", None)
                    if widget is None:
                        continue
                    self.config[category][sub_category] = self.get_widget_value(widget, sub_settings.get('type'))
                else:
                    for key, meta in sub_settings.items():
                        widget = getattr(self, f"{category}_{sub_category}_{key}_input", None)
                        if widget is None:
                            continue
                        if sub_category not in self.config[category]:
                            self.config[category][sub_category] = {}
                        self.config[category][sub_category][key] = self.get_widget_value(widget, meta.get('type'))

        # Save the API key to the .env file
        api_key = self.config['model_options']['api']['api_key'] or ''
        set_key('.env', 'OPENAI_API_KEY', api_key)
        os.environ['OPENAI_API_KEY'] = api_key
            
        # Remove the API key from the config
        self.config['model_options']['api']['api_key'] = None

        save_config(self.config)
        QMessageBox.information(self, 'Settings Saved', 'Settings have been saved. Restarting application...')
        self.restart_application()

    def restart_application(self):
        """
        Restart the application to apply the new settings.
        """
        QCoreApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def resetSettings(self):
        """
        Reset the settings to the default values.
        """
        self.reset_to_initial_settings(self.default_config)

    def reset_to_initial_settings(self, config_source):
        """
        Reset the settings to the initial values when the window was opened.
        """
        for category, settings in self.schema.items():
            for sub_category, sub_settings in settings.items():
                if isinstance(sub_settings, dict) and 'value' in sub_settings:
                    widget = getattr(self, f"{category}_{sub_category}_input", None)
                    if widget is None:
                        continue
                    initial_value = config_source[category][sub_category]
                    self.set_widget_value(widget, initial_value, sub_settings.get('type'))
                else:
                    for key, meta in sub_settings.items():
                        widget = getattr(self, f"{category}_{sub_category}_{key}_input", None)
                        if widget is None:
                            continue
                        initial_value = config_source[category][sub_category][key]
                        self.set_widget_value(widget, initial_value, meta.get('type'))

    def set_widget_value(self, widget, value, value_type):
        """
        Set the value of the widget.
        """
        if isinstance(widget, QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        elif isinstance(widget, QLineEdit):
            if value_type == 'int' or value_type == 'float':
                widget.setText(str(value))
            else:
                widget.setText(value)

    def get_widget_value(self, widget, value_type):
        """
        Get the value of the widget.
        """
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            value = widget.currentText()
            return value if value else None
        elif isinstance(widget, QLineEdit):
            text = widget.text()
            if value_type == 'int':
                return int(text) if text else None
            elif value_type == 'float':
                return float(text) if text else None
            else:
                return text if text else None

    def toggle_api_local_options(self, use_api):
        """
        Toggle whether the API or local options are visible.
        """
        for label, widget, help_button in self.api_widgets:
            label.setVisible(use_api)
            widget.setVisible(use_api)
            help_button.setVisible(use_api)
        
        for label, widget, help_button in self.local_widgets:
            label.setVisible(not use_api)
            widget.setVisible(not use_api)
            help_button.setVisible(not use_api)

    def closeEvent(self, event):
        """
        Confirm before closing the settings window without saving.
        """
        reply = QMessageBox.question(
            self,
            'Close without saving?',
            'Are you sure you want to close without saving?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reset_to_initial_settings(self.initial_config)
            self.settingsClosed.emit()
            super().closeEvent(event)
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    schema = load_config_schema()
    settings_window = SettingsWindow(schema)
    settings_window.show()
    
    sys.exit(app.exec_())
