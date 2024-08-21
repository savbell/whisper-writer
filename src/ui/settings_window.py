from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
                             QLabel, QLineEdit, QSpacerItem, QSizePolicy, QComboBox,
                             QCheckBox, QPushButton, QScrollArea, QToolButton, QMessageBox,
                             QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from utils import ConfigManager


class SettingsWindow(QWidget):
    settings_saved = pyqtSignal()
    settings_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(700, 700)
        self.config_manager = ConfigManager()
        self.binding_manager = BindingManager()
        self.config_manager.clean_config()  # remove keys not in schema
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.create_tabs()
        self.create_buttons(layout)
        self.setLayout(layout)

    def create_tabs(self):
        schema = self.config_manager.get_schema()
        for category in schema.keys():
            tab = QScrollArea()
            tab_widget = QWidget()
            tab_layout = QVBoxLayout()
            self.create_category_widgets(tab_layout, category)
            tab_widget.setLayout(tab_layout)
            tab.setWidget(tab_widget)
            tab.setWidgetResizable(True)
            self.tabs.addTab(tab, category.replace('_', ' ').capitalize())

    def create_category_widgets(self, layout, category):
        keys = self.config_manager.get_all_keys()
        category_keys = [k for k in keys if k.startswith(category)]

        for key in category_keys:
            parts = key.split('.')
            current_layout = layout

            for i, part in enumerate(parts[1:-1]):  # Skip the first (category) and last (setting name) parts
                group_name = '.'.join(parts[:i+2])
                if not self.find_group_box(current_layout, group_name):
                    group_box = QGroupBox(part.replace('_', ' ').capitalize())
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)
                    current_layout.addWidget(group_box)
                    current_layout = group_layout
                else:
                    current_layout = self.find_group_box(current_layout, group_name).layout()

            try:
                widget = self.create_setting_widget(key)
                if widget:
                    current_layout.addWidget(widget)
            except Exception as e:
                print(f"Error creating widget for key {key}: {str(e)}")

        # Add spacer at the bottom to push all widgets to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

    def find_group_box(self, layout, name):
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if (isinstance(widget, QGroupBox) and
                    widget.title().lower().replace(' ', '_')) == name.split('.')[-1]:
                return widget
        return None

    def create_setting_widget(self, config_key):
        schema = self.config_manager.get_schema()
        parts = config_key.split('.')
        meta = schema

        try:
            for part in parts:
                if part not in meta:
                    print(f"Warning: Key '{config_key}' not found in schema. Skipping.")
                    return None
                meta = meta[part]

            if 'value' not in meta:
                print(f"Warning: Key '{config_key}' does not have a 'value' in schema. Skipping.")
                return None

            widget = SettingWidget(config_key, meta, self.config_manager, self.binding_manager)
            return widget
        except Exception as e:
            print(f"Error processing key '{config_key}': {str(e)}")
            return None

    def create_buttons(self, layout):
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(save_button)
        button_layout.addWidget(reset_button)
        layout.addLayout(button_layout)

    def save_settings(self):
        self.binding_manager.update_all_config()
        self.config_manager.save_config()
        self.settings_saved.emit()

    def reset_settings(self):
        self.config_manager.reload_config()
        self.binding_manager.update_all_widgets()

    def closeEvent(self, event):
        self.settings_closed.emit()
        event.accept()


class SettingWidget(QWidget):
    def __init__(self, config_key, meta, config_manager, binding_manager):
        super().__init__()
        self.config_key = config_key
        self.meta = meta
        self.config_manager = config_manager
        self.binding_manager = binding_manager
        self.is_capability = 'capabilities' in config_key.split('.')
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Reduce widget margins

        # Use the last part of the key as the label
        label_text = self.config_key.split('.')[-1].replace('_', ' ').capitalize()
        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        if self.is_capability:
            self.input_widget = QLabel(str(self.meta['value']))
        else:
            self.input_widget = self.create_input_widget()
        layout.addWidget(self.input_widget)

        # Add file browser button for model_path
        if self.config_key.endswith('model_path'):
            self.browse_button = QPushButton("Browse")
            self.browse_button.clicked.connect(self.browse_folder)
            layout.addWidget(self.browse_button)

        # Add help icon
        help_button = QToolButton()
        help_button.setIcon(QIcon.fromTheme("help-contents"))
        help_button.clicked.connect(self.show_help)
        layout.addWidget(help_button)

        # If it's the scripts widget, align the label to the top
        if self.config_key.endswith('enabled_scripts'):
            layout.setAlignment(self.label, Qt.AlignTop)
            layout.setAlignment(help_button, Qt.AlignTop)
        else:
            layout.setAlignment(self.label, Qt.AlignVCenter)
            layout.setAlignment(help_button, Qt.AlignVCenter)

        self.setLayout(layout)

    def show_help(self):
        QMessageBox.information(self, "Help", self.meta.get('description',
                                                            'No description available.'))

    def create_input_widget(self):
        if self.is_capability:
            return QLabel(str(self.meta['value']))

        widget_type = self.meta.get('type')
        if widget_type == 'bool':
            return self.create_checkbox()
        elif widget_type == 'str' and 'options' in self.meta:
            return self.create_combobox()
        elif widget_type in ['str', 'int', 'float', 'int or null']:
            return self.create_line_edit()
        elif widget_type == 'list' and self.config_key.endswith('enabled_scripts'):
            return self.create_scripts_widget()
        else:
            return QLabel(f"Unsupported type: {widget_type}")

    def create_scripts_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins
        widget.setLayout(layout)

        available_scripts = self.config_manager.get_available_scripts()
        enabled_scripts = self.config_manager.get_config_value(self.config_key)

        self.script_checkboxes = {}
        for script in available_scripts:
            checkbox = QCheckBox(script)
            checkbox.setChecked(script in enabled_scripts)
            layout.addWidget(checkbox)
            self.script_checkboxes[script] = checkbox

        self.binding_manager.add_binding(self.config_key, widget,
                                         self.get_enabled_scripts,
                                         self.set_enabled_scripts)
        return widget

    def get_enabled_scripts(self, widget):
        return [script for script, checkbox in self.script_checkboxes.items()
                if checkbox.isChecked()]

    def set_enabled_scripts(self, widget, value):
        for script, checkbox in self.script_checkboxes.items():
            checkbox.setChecked(script in value)

    def create_checkbox(self):
        widget = QCheckBox()
        current_value = self.config_manager.get_config_value(self.config_key)
        widget.setChecked(bool(current_value))
        self.binding_manager.add_binding(self.config_key, widget,
                                         lambda w: w.isChecked(),
                                         lambda w, v: w.setChecked(bool(v)))
        return widget

    def create_combobox(self):
        widget = QComboBox()
        widget.addItems(self.meta['options'])
        current_value = self.config_manager.get_config_value(self.config_key)
        widget.setCurrentText(str(current_value))
        self.binding_manager.add_binding(self.config_key, widget,
                                         lambda w: w.currentText(),
                                         lambda w, v: w.setCurrentText(str(v)))
        return widget

    def create_line_edit(self):
        widget = QLineEdit()
        current_value = self.config_manager.get_config_value(self.config_key)
        widget.setText(str(current_value) if current_value is not None else '')

        if self.meta.get('type') == 'int or null':
            # For 'int or null' type, we need a custom getter and setter
            self.binding_manager.add_binding(self.config_key, widget,
                                             lambda w: self._parse_int_or_null(w.text()),
                                             lambda w, v: w.setText(str(v) if v is not None else ''))
        else:
            self.binding_manager.add_binding(self.config_key, widget,
                                             lambda w: w.text(),
                                             lambda w, v: w.setText(str(v) if v is not None else ''))
        return widget

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Model Folder")
        if folder:
            self.input_widget.setText(folder)

    @staticmethod
    def _parse_int_or_null(value):
        if value == '':
            return None
        try:
            return int(value)
        except ValueError:
            return value  # Return as string if it can't be converted to int


class BindingManager:
    def __init__(self):
        self.bindings = {}

    def add_binding(self, config_key, widget, getter, setter):
        if 'capabilities' not in config_key.split('.'):
            if config_key.endswith('enabled_scripts'):
                self.bindings[config_key] = ScriptsBinding(config_key, widget, getter, setter)
            else:
                self.bindings[config_key] = Binding(config_key, widget, getter, setter)

    def update_all_widgets(self):
        for binding in self.bindings.values():
            binding.update_widget()

    def update_all_config(self):
        for binding in self.bindings.values():
            binding.update_config()


class Binding:
    def __init__(self, config_key, widget, getter, setter):
        self.config_key = config_key
        self.widget = widget
        self.getter = getter
        self.setter = setter
        self.config_manager = ConfigManager()

    def update_widget(self):
        value = self.config_manager.get_config_value(self.config_key)
        self.setter(self.widget, value)

    def update_config(self):
        value = self.getter(self.widget)
        self.config_manager.set_config_value(self.config_key, value)


class ScriptsBinding(Binding):
    def update_widget(self):
        value = self.config_manager.get_config_value(self.config_key)
        self.setter(self.widget, value)

    def update_config(self):
        value = self.getter(self.widget)
        self.config_manager.set_config_value(self.config_key, value)
