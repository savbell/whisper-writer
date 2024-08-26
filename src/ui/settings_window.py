import os
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QTabWidget, QGroupBox, QGridLayout,
                             QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QFileDialog,
                             QScrollArea, QToolButton, QMessageBox, QVBoxLayout, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QIntValidator, QDoubleValidator

from config_manager import ConfigManager


class SettingsWindow(QWidget):
    close_window = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(700, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.create_tabs()
        self.create_buttons(layout)
        self.setLayout(layout)

    def create_tabs(self):
        # Global options tab
        global_tab = self.create_global_tab()
        self.tabs.addTab(global_tab, "Global Options")

        # Profile tabs
        profiles = ConfigManager.get_profiles()
        for profile in profiles:
            profile_name = profile['name']
            profile_tab = self.create_profile_tab(profile_name)
            self.tabs.addTab(profile_tab, profile_name)

        # Add profile button
        self.tabs.setCornerWidget(self.create_add_profile_button(), Qt.TopRightCorner)

    def create_global_tab(self):
        tab = QScrollArea()
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)

        global_options = ConfigManager.get_section('global_options')
        self.create_section_widgets(tab_layout, global_options, 'global_options')

        # Add stretch factor to push widgets to the top
        tab_layout.addStretch(1)

        tab.setWidget(tab_widget)
        tab.setWidgetResizable(True)
        return tab

    def create_profile_tab(self, profile_name):
        tab = QScrollArea()
        tab_widget = QWidget()
        tab_layout = QVBoxLayout()

        profile_config = ConfigManager.get_section('profiles', profile_name)

        # Add backend_type widget
        backend_type_key = f'profiles.{profile_name}.backend_type'
        backend_type_widget = self.create_setting_widget(backend_type_key,
                                                         profile_config['backend_type'])
        if isinstance(backend_type_widget.input_widget, QComboBox):
            backend_type_widget.input_widget.currentTextChanged.connect(
                lambda value, pn=profile_name: self.update_backend_options(pn, value)
            )
        tab_layout.addWidget(backend_type_widget)

        # Add activation_key widget
        activation_key = f'profiles.{profile_name}.activation_key'
        activation_key_widget = self.create_setting_widget(activation_key,
                                                           profile_config['activation_key'])
        tab_layout.addWidget(activation_key_widget)

        # Create group boxes for other sections
        for section_name, section in profile_config.items():
            if section_name not in ['backend_type', 'name', 'activation_key']:
                group_box = QGroupBox(section_name.replace('_', ' ').capitalize())
                group_box.setObjectName(f"{profile_name}_{section_name}")  # Set a unique obj name
                group_layout = QVBoxLayout()
                if isinstance(section, dict):
                    self.create_section_widgets(group_layout,
                                                section,
                                                f'profiles.{profile_name}.{section_name}')
                else:
                    widget = self.create_setting_widget(f'profiles.{profile_name}.{section_name}',
                                                        section)
                    group_layout.addWidget(widget)
                group_box.setLayout(group_layout)
                tab_layout.addWidget(group_box)

        # Add delete profile button
        delete_button = QPushButton(f"Delete {profile_name}")
        delete_button.clicked.connect(lambda: self.delete_profile(profile_name))
        tab_layout.addWidget(delete_button)

        # Add rename button
        rename_button = QPushButton("Rename Profile")
        rename_button.clicked.connect(lambda: self.rename_profile(profile_name))
        tab_layout.addWidget(rename_button)

        tab_widget.setLayout(tab_layout)
        tab.setWidget(tab_widget)
        tab.setWidgetResizable(True)
        return tab

    def rename_profile(self, old_name):
        new_name, ok = QInputDialog.getText(self, 'Rename Profile', 'Enter new profile name:')
        if ok and new_name:
            if ConfigManager.rename_profile(old_name, new_name):
                # Update tab name
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == old_name:
                        self.tabs.setTabText(i, new_name)
                        break

                # Update the tab's content
                new_tab = self.create_profile_tab(new_name)
                self.tabs.removeTab(i)
                self.tabs.insertTab(i, new_tab, new_name)

                # Update active profiles widget
                self.update_active_profiles_widget()

                # Inform user of successful rename
                QMessageBox.information(self,
                                        'Profile Renamed',
                                        f'Profile "{old_name}" has been renamed to "{new_name}".')
            else:
                QMessageBox.warning(self,
                                    'Rename Failed',
                                    f'The name "{new_name}" is already in use or '
                                    f'the profile could not be found.')

    def update_backend_options(self, profile_name, backend_type):
        ConfigManager.set_value(f'profiles.{profile_name}.backend_type', backend_type)

        # Refresh the backend options
        backend_group = self.findChild(QGroupBox, f"{profile_name}_backend")
        if backend_group:
            backend_layout = backend_group.layout()
            # Clear existing widgets
            while backend_layout.count():
                item = backend_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Add new widgets
            backend_config = ConfigManager.get_section('backend', profile_name)
            self.create_section_widgets(backend_layout, backend_config,
                                        f'profiles.{profile_name}.backend')
        else:
            print(f"Backend group for {profile_name} not found")  # Debug print
            # If the backend group doesn't exist, recreate the entire profile tab
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == profile_name:
                    new_tab = self.create_profile_tab(profile_name)
                    self.tabs.removeTab(i)
                    self.tabs.insertTab(i, new_tab, profile_name)
                    self.tabs.setCurrentIndex(i)
                    break

        # Force the UI to update
        self.update()

    def create_section_widgets(self, layout, section, section_path):
        if not isinstance(section, dict):
            widget = self.create_setting_widget(section_path, section)
            if widget:
                layout.addWidget(widget)
            return

        for key, value in section.items():
            if isinstance(value, dict):
                # This is a nested section, create a group box
                group_box = QGroupBox(key.replace('_', ' ').capitalize())
                group_layout = QVBoxLayout()
                # Pass the nested section path to the next level
                self.create_section_widgets(group_layout, value, f'{section_path}.{key}')
                group_box.setLayout(group_layout)
                layout.addWidget(group_box)
            else:
                # This is a setting, create a widget for it
                # Pass the full setting path to the widget
                widget = self.create_setting_widget(f'{section_path}.{key}', value)
                if widget:
                    layout.addWidget(widget)

    def create_setting_widget(self, config_key, value):
        # No need to extract the actual key; use the full path provided
        widget = SettingWidget(config_key, value)
        return widget

    def create_add_profile_button(self):
        button = QPushButton("Add Profile")
        button.clicked.connect(self.add_profile)
        return button

    def add_profile(self):
        new_profile = ConfigManager.create_profile("New Profile")
        profile_name = new_profile['name']
        profile_tab = self.create_profile_tab(profile_name)
        self.tabs.addTab(profile_tab, profile_name)
        self.tabs.setCurrentIndex(self.tabs.count() - 1)  # Switch to the new tab

        # Update the active profiles widget
        self.update_active_profiles_widget()

    def delete_profile(self, profile_name):
        if self.tabs.count() <= 2:  # 1 for global options, 1 for the last profile
            QMessageBox.warning(self, 'Cannot Delete Profile',
                                'You cannot delete the last remaining profile.')
            return

        reply = QMessageBox.question(self, 'Delete Profile',
                                     f"Delete the profile '{profile_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if ConfigManager.delete_profile(profile_name):
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == profile_name:
                        self.tabs.removeTab(i)
                        break
                self.update_active_profiles_widget()
                QMessageBox.information(self, 'Profile Deleted',
                                        f'Profile "{profile_name}" has been deleted.')
            else:
                QMessageBox.warning(self, 'Cannot Delete Profile',
                                    'The profile could not be deleted. '
                                    'It may be the last remaining profile.')

    def update_active_profiles_widget(self):
        global_tab = self.tabs.widget(0)  # Assuming global options is always the first tab
        if global_tab and isinstance(global_tab, QScrollArea):
            scroll_content = global_tab.widget()
            if scroll_content and scroll_content.layout():
                for i in range(scroll_content.layout().count()):
                    widget = scroll_content.layout().itemAt(i).widget()
                    if (isinstance(widget, SettingWidget) and
                            widget.config_key == 'global_options.active_profiles'):
                        all_profiles = [profile['name']
                                        for profile in ConfigManager.get_profiles()]
                        active_profiles = ConfigManager.get_value('global_options.active_profiles')

                        # Create a new CheckboxListWidget with updated options
                        new_widget = CheckboxListWidget(all_profiles, active_profiles)
                        new_widget.optionsChanged.connect(widget.update_config)

                        # Replace the old widget with the new one
                        old_layout = widget.layout()
                        old_layout.replaceWidget(widget.input_widget, new_widget)
                        widget.input_widget.deleteLater()
                        widget.input_widget = new_widget
                        break

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
        ConfigManager.save_config()
        self.close()

    def reset_settings(self):
        ConfigManager.reload_config()
        self.create_tabs()  # Recreate all tabs to reflect the reset config

    def closeEvent(self, event):
        event.accept()


class SettingWidget(QWidget):
    def __init__(self, config_key, value):
        super().__init__()
        self.config_key = config_key
        self.value = value
        self.schema = ConfigManager.get_schema_for_key(config_key)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label_text = self.config_key.split('.')[-1].replace('_', ' ').capitalize()
        self.label = QLabel(label_text)

        self.input_widget = self.create_input_widget()

        help_button = QToolButton()
        help_button.setIcon(QIcon.fromTheme("help-contents"))
        help_button.clicked.connect(self.show_help)

        if isinstance(self.input_widget, CheckboxListWidget):
            layout.addWidget(self.label, 0, 0, Qt.AlignTop)
            layout.addWidget(self.input_widget, 0, 1, Qt.AlignTop)  # Align to top
            layout.addWidget(help_button, 0, 2, Qt.AlignTop)

            # Adjust the internal layout of CheckboxListWidget
            checkbox_layout = self.input_widget.layout()
            checkbox_layout.setContentsMargins(0, 0, 0, 0)  # Remove any internal margins
            checkbox_layout.setSpacing(2)  # Reduce spacing between checkboxes
        else:
            layout.addWidget(self.label, 0, 0)
            layout.addWidget(self.input_widget, 0, 1)
            layout.addWidget(help_button, 0, 2)

        self.setLayout(layout)

    def create_input_widget(self):
        widget_type = self.schema.get('type')
        if widget_type == 'bool':
            return self.create_checkbox()
        elif widget_type == 'str' and 'options' in self.schema:
            return self.create_combobox()
        elif widget_type == 'int':
            return self.create_line_edit(QIntValidator())
        elif widget_type == 'float':
            return self.create_line_edit(QDoubleValidator())
        elif widget_type == 'int or null':
            return self.create_line_edit(QIntValidator(), allow_empty=True)
        elif widget_type == 'str':
            return self.create_line_edit()
        elif widget_type == 'list':
            return self.create_checkbox_list()
        elif widget_type == 'dir_path':
            return self.create_dir_path_widget()
        else:
            return QLabel(f"Unsupported type: {widget_type}")

    def create_checkbox_list(self):
        if self.config_key == 'global_options.active_profiles':
            options = [profile['name'] for profile in ConfigManager.get_profiles()]
        elif self.config_key.endswith('enabled_scripts'):
            options = self.get_available_scripts()
        else:
            options = self.schema.get('options', [])

        widget = CheckboxListWidget(options, self.value)
        widget.optionsChanged.connect(self.update_config)
        return widget

    def get_available_scripts(self):
        script_folder = 'scripts'  # Adjust this path as needed
        if os.path.exists(script_folder):
            return [f for f in os.listdir(script_folder) if f.endswith('.py')]
        return []

    def create_line_edit(self, validator=None, allow_empty=False):
        widget = QLineEdit()
        if validator:
            widget.setValidator(validator)
        if allow_empty:
            widget.setPlaceholderText("Auto")
        widget.setText(str(self.value) if self.value is not None else '')
        widget.editingFinished.connect(self.update_config)
        return widget

    def create_checkbox(self):
        widget = QCheckBox()
        widget.setChecked(bool(self.value))
        widget.stateChanged.connect(self.update_config)
        return widget

    def create_combobox(self):
        widget = QComboBox()
        widget.addItems(self.schema['options'])
        widget.setCurrentText(str(self.value))
        widget.currentTextChanged.connect(self.update_config)
        return widget

    def create_list_widget(self):
        widget = QLineEdit()
        widget.setText(', '.join(map(str, self.value)))
        widget.editingFinished.connect(self.update_config)
        return widget

    def create_dir_path_widget(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        line_edit = QLineEdit(self.value if self.value else '')
        browse_button = QPushButton("Browse")

        layout.addWidget(line_edit)
        layout.addWidget(browse_button)

        def browse_directory():
            directory = QFileDialog.getExistingDirectory(self, "Select Directory")
            if directory:
                line_edit.setText(directory)
                self.update_config(directory)

        browse_button.clicked.connect(browse_directory)
        line_edit.editingFinished.connect(lambda: self.update_config(line_edit.text()))

        return widget

    def update_config(self, value=None):
        if isinstance(self.input_widget, QWidget) and self.schema.get('type') == 'dir_path':
            line_edit = self.input_widget.findChild(QLineEdit)
            if line_edit:
                value = line_edit.text()
        elif isinstance(self.input_widget, CheckboxListWidget):
            if value is None:
                value = self.input_widget.get_selected_options()
        elif isinstance(self.input_widget, QCheckBox):
            value = self.input_widget.isChecked()
        elif isinstance(self.input_widget, QComboBox):
            value = self.input_widget.currentText()
        elif isinstance(self.input_widget, QLineEdit):
            if self.schema.get('type') == 'int':
                value = int(self.input_widget.text())
            elif self.schema.get('type') == 'float':
                value = float(self.input_widget.text())
            elif self.schema.get('type') == 'int or null':
                value = int(self.input_widget.text()) if self.input_widget.text() else None
            else:
                value = self.input_widget.text()

        ConfigManager.set_value(self.config_key, value)

    def show_help(self):
        QMessageBox.information(self, "Help", self.schema.get('description',
                                                              'No description available.'))


class CheckboxListWidget(QWidget):
    optionsChanged = pyqtSignal(list)

    def __init__(self, options, selected_options, parent=None):
        super().__init__(parent)
        self.options = options
        self.selected_options = selected_options
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.checkboxes = {}

        for option in self.options:
            checkbox = QCheckBox(option)
            checkbox.setChecked(option in self.selected_options)
            checkbox.stateChanged.connect(self.update_selected_options)
            self.checkboxes[option] = checkbox
            layout.addWidget(checkbox)

        self.setLayout(layout)

    def update_selected_options(self):
        self.selected_options = [option for option, checkbox in self.checkboxes.items()
                                 if checkbox.isChecked()]
        self.optionsChanged.emit(self.selected_options)

    def get_selected_options(self):
        return self.selected_options
