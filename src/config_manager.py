import yaml
import os
from typing import Any, Dict, List, Optional
from event_bus import EventBus


class ConfigValidator:
    @staticmethod
    def validate_and_update(config: Dict, schema: Dict) -> Dict:
        ConfigValidator._validate_section(config, schema, [])
        return config

    @staticmethod
    def _validate_section(config: Dict, schema: Dict, path: List[str]):
        for key, value in schema.items():
            if key == 'available_backends':
                continue  # Skip validating the available_backends section
            current_path = path + [key]
            if key not in config:
                print(f"Adding missing key: {'.'.join(current_path)}")
                config[key] = ConfigValidator._get_default_value(value)
            elif isinstance(value, dict) and 'value' not in value:
                if not isinstance(config[key], dict):
                    print(f"Replacing invalid value for {'.'.join(current_path)} with default")
                    config[key] = {}
                ConfigValidator._validate_section(config[key], value, current_path)
            elif key == 'backend':
                # Special handling for backend options
                backend_type = config.get('backend_type')
                if backend_type:
                    backend_schema = schema['available_backends'][backend_type]
                    ConfigValidator._validate_section(config[key], backend_schema, current_path)
            elif not ConfigValidator._validate_value(config[key], value):
                print(f"Replacing invalid value for {'.'.join(current_path)} with default")
                config[key] = ConfigValidator._get_default_value(value)

        keys_to_remove = [key for key in config if key not in schema and key != 'backend']
        for key in keys_to_remove:
            print(f"Removing spurious key: {'.'.join(path + [key])}")
            del config[key]

    @staticmethod
    def _validate_value(value: Any, schema: Dict) -> bool:
        if 'type' in schema:
            if schema['type'] == 'str' and not isinstance(value, str):
                return False
            elif schema['type'] == 'int' and not isinstance(value, int):
                return False
            elif schema['type'] == 'float' and not isinstance(value, (int, float)):
                return False
            elif schema['type'] == 'bool' and not isinstance(value, bool):
                return False
            elif schema['type'] == 'list' and not isinstance(value, list):
                return False
            elif schema['type'] == 'int or null' and not (isinstance(value, int) or value is None):
                return False
            elif schema['type'] == 'dir_path':
                return isinstance(value, str) and (value == '' or os.path.isdir(value))
        if 'options' in schema and value not in schema['options']:
            return False
        return True

    @staticmethod
    def _get_default_value(schema: Dict) -> Any:
        if 'value' in schema:
            return schema['value']
        elif schema.get('type') == 'str':
            return ''
        elif schema.get('type') == 'int':
            return 0
        elif schema.get('type') == 'float':
            return 0.0
        elif schema.get('type') == 'bool':
            return False
        elif schema.get('type') == 'list':
            return []
        elif schema.get('type') == 'int or null':
            return None
        else:
            return {}


class ConfigLoader:
    @staticmethod
    def load_yaml(file_path: str) -> Dict:
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            return {}

    @staticmethod
    def save_yaml(data: Dict, file_path: str):
        with open(file_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)


class ProfileManager:
    def __init__(self, config: Dict, schema: Dict):
        self.config = config
        self.schema = schema
        if 'profiles' not in self.config:
            self.config['profiles'] = []

    def get_profiles(self, active_only: bool = False) -> List[Dict]:
        all_profiles = self.config.get('profiles', [])
        if active_only:
            active_profile_names = self.config.get('global_options', {}).get('active_profiles', [])
            return [profile for profile in all_profiles if profile['name'] in active_profile_names]
        return all_profiles

    def create_profile(self, name: str = 'Default') -> Dict:
        unique_name = self._generate_unique_name(name)
        new_profile = {'name': unique_name}
        for key, schema_value in self.schema['profiles'][0].items():
            if key == 'backend_type':
                new_profile[key] = schema_value['value']
            elif key == 'backend':
                new_profile[key] = {}
            elif key != 'name':
                new_profile[key] = self._get_default_value_from_schema(schema_value)

        backend_type = new_profile['backend_type']
        if backend_type in self.schema['available_backends']:
            for option_key, option_value in self.schema['available_backends'][backend_type].items():
                new_profile['backend'][option_key] = self._get_default_value_from_schema(option_value)

        return new_profile

    def add_profile(self, name: str) -> Dict:
        new_profile = self.create_profile(name)
        if 'profiles' not in self.config:
            self.config['profiles'] = []
        self.config['profiles'].append(new_profile)
        return new_profile

    def delete_profile(self, name: str) -> bool:
        if len(self.config['profiles']) <= 1:
            return False  # Prevent deleting the last profile
        self.config['profiles'] = [p for p in self.config['profiles'] if p['name'] != name]
        active_profiles = self.config.get('global_options', {}).get('active_profiles', [])
        if name in active_profiles:
            active_profiles.remove(name)
        return True

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        if old_name == new_name:
            return True
        if any(profile['name'] == new_name for profile in self.config['profiles']):
            return False
        for profile in self.config['profiles']:
            if profile['name'] == old_name:
                profile['name'] = new_name
                # Update active_profiles if necessary
                active_profiles = self.config.get('global_options', {}).get('active_profiles', [])
                if old_name in active_profiles:
                    active_profiles[active_profiles.index(old_name)] = new_name
                return True
        return False

    def _get_default_value_from_schema(self, schema_value: Dict) -> Any:
        if isinstance(schema_value, dict) and 'value' in schema_value:
            return schema_value['value']
        elif isinstance(schema_value, dict):
            # Create a section with nested defaults
            return {k: self._get_default_value_from_schema(v) for k, v in schema_value.items()}
        return None

    def _generate_unique_name(self, base_name: str) -> str:
        counter = 1
        new_name = base_name
        while any(profile['name'] == new_name for profile in self.config.get('profiles', [])):
            new_name = f"{base_name} ({counter})"
            counter += 1
        return new_name


class ConfigManager:
    _config: Dict = {}
    _schema: Dict = {}
    _profile_manager: Optional[ProfileManager] = None
    _event_bus: EventBus = None

    @classmethod
    def initialize(cls, event_bus: EventBus):
        cls._event_bus = event_bus
        cls._schema = ConfigLoader.load_yaml('src/config_schema.yaml')
        # Initialize with empty profiles list
        cls._profile_manager = ProfileManager({'profiles': []}, cls._schema)
        cls._config = cls._load_config()
        cls._validate_config()
        cls._profile_manager.config = cls._config  # Update ProfileManager with loaded config

    @classmethod
    def get_profiles(cls, active_only: bool = False) -> List[Dict]:
        return cls._profile_manager.get_profiles(active_only)

    @classmethod
    def rename_profile(cls, old_name: str, new_name: str) -> bool:
        return cls._profile_manager.rename_profile(old_name, new_name)

    @classmethod
    def create_profile(cls, name: str) -> Dict:
        unique_name = cls._profile_manager._generate_unique_name(name)
        return cls._profile_manager.add_profile(unique_name)

    @classmethod
    def delete_profile(cls, name: str) -> bool:
        return cls._profile_manager.delete_profile(name)

    @classmethod
    def get_section(cls, section_name: str, profile_name: Optional[str] = None) -> Dict:
        if profile_name:
            profile = next((p for p in cls._config['profiles'] if p['name'] == profile_name), None)
            if not profile:
                raise ValueError(f"Profile '{profile_name}' not found")
            if section_name == 'profiles':
                return profile
            else:
                return profile.get(section_name, {})
        return cls._config.get(section_name, {})

    @classmethod
    def get_value(cls, key: str, profile_name: Optional[str] = None) -> Any:
        keys = key.split('.')
        if profile_name or (keys[0] == 'profiles' and len(keys) > 1):
            if not profile_name:
                profile_name = keys[1]
                keys = keys[2:]
            profile = next((p for p in cls._config['profiles'] if p['name'] == profile_name), None)
            if not profile:
                raise ValueError(f"Profile '{profile_name}' not found")
            section = profile
        else:
            section = cls._config

        for k in keys:
            if isinstance(section, dict):
                section = section.get(k, None)
            else:
                return None
        return section

    @classmethod
    def set_value(cls, key: str, value: Any, profile_name: Optional[str] = None):
        keys = key.split('.')
        if profile_name or (keys[0] == 'profiles' and len(keys) > 1):
            if not profile_name:
                profile_name = keys[1]
                keys = keys[2:]
            profile = next((p for p in cls._config['profiles'] if p['name'] == profile_name), None)
            if not profile:
                raise ValueError(f"Profile '{profile_name}' not found")
            target = profile
        else:
            target = cls._config

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

        if keys[-1] == 'backend_type':
            # When backend_type changes, reset the backend options
            backend_schema = cls._schema['available_backends'][value]
            target['backend'] = {k: v['value'] for k, v in backend_schema.items() if 'value' in v}

    @classmethod
    def get_schema_for_key(cls, key: str) -> Dict:
        schema = cls._schema
        parts = key.split('.')

        # Special handling for profiles
        if parts[0] == 'profiles':
            profile_schema = schema.get('profiles', [{}])[0]
            profile_name = parts[1]
            remaining_parts = parts[2:]

            # Handle backend options specially
            if remaining_parts[0] == 'backend' and len(remaining_parts) > 1:
                backend_type = cls.get_value(f"profiles.{profile_name}.backend_type")
                if backend_type:
                    backend_schema = cls._schema.get('available_backends',
                                                     {}).get(backend_type, {})
                    for part in remaining_parts[1:]:
                        backend_schema = backend_schema.get(part, {})
                    return backend_schema
            else:
                # Navigate through the profile schema
                for part in remaining_parts:
                    profile_schema = profile_schema.get(part, {})
                return profile_schema

        # For non-profile keys, navigate through the schema normally
        for part in parts:
            if isinstance(schema, dict):
                schema = schema.get(part, {})
            else:
                return {}

        return schema

    @classmethod
    def save_config(cls):
        ConfigLoader.save_yaml(cls._config, 'config.yaml')
        cls._event_bus.emit("config_changed")

    @classmethod
    def reload_config(cls):
        cls._config = cls._load_config()
        cls._validate_config()
        cls._profile_manager = ProfileManager(cls._config, cls._schema)

    @classmethod
    def log_print(cls, message: str):
        if cls._config.get('global_options', {}).get('print_to_terminal', False):
            print(message)

    @classmethod
    def _load_config(cls) -> Dict:
        config = ConfigLoader.load_yaml('config.yaml')
        if not config:
            config = cls._create_default_config()
            ConfigLoader.save_yaml(config, 'config.yaml')
        return config

    @classmethod
    def _create_default_config(cls) -> Dict:
        default_config = {'profiles': []}
        for section, content in cls._schema.items():
            if section == 'profiles':
                default_profile = cls._profile_manager.create_profile()
                default_config['profiles'].append(default_profile)
            elif section == 'available_backends':
                # Skip this section as it's not part of the actual config
                continue
            else:
                default_config[section] = cls._create_default_section(content)
        return default_config

    @classmethod
    def _create_default_section(cls, schema_section: Dict) -> Dict:
        section = {}
        for key, value in schema_section.items():
            if isinstance(value, dict) and 'value' in value:
                section[key] = value['value']
            elif isinstance(value, dict):
                if value.get('type') == 'int or null':
                    section[key] = None
                else:
                    section[key] = cls._create_default_section(value)
        return section

    @classmethod
    def _get_default_value_from_schema(cls, schema_value: Dict) -> Any:
        if isinstance(schema_value, dict) and 'value' in schema_value:
            return schema_value['value']
        elif isinstance(schema_value, dict):
            # Create a section with nested defaults
            return cls._create_default_section(schema_value)
        return None

    @classmethod
    def _validate_config(cls):
        cls._config = ConfigValidator.validate_and_update(cls._config, cls._schema)
