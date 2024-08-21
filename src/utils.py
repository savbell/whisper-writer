import yaml
import os


class ConfigManager:
    _instance = None

    def __init__(self):
        """Initialize the ConfigManager instance."""
        self.config = None
        self.schema = None

    @classmethod
    def initialize(cls, schema_path=None):
        """Initialize the ConfigManager with the given schema path."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.schema = cls._instance._load_config_schema(schema_path)
            cls._instance.config = cls._instance._load_default_config()
            cls._instance._load_user_config()

    @classmethod
    def get_schema(cls):
        """Get the configuration schema."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        return cls._instance.schema

    @classmethod
    def get_config_section(cls, key):
        """Get a specific section of the configuration using a dotted key."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        keys = cls._split_keys(key)
        section = cls._instance.config
        for k in keys:
            if isinstance(section, dict) and k in section:
                section = section[k]
            else:
                return {}
        return section

    @classmethod
    def get_config_value(cls, key):
        """Get a specific configuration value using a dotted key."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        keys = cls._split_keys(key)
        value = cls._instance.config
        schema = cls.get_schema()
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
                schema = schema.get(k, {})
            elif isinstance(value, list):
                try:
                    index = int(k)
                    value = value[index]
                except (ValueError, IndexError):
                    return None
            else:
                # If the key is not found in the config, check the schema
                return cls._get_schema_value(key)

        # Convert the value to the correct type based on the schema
        value_type = schema.get('type')
        return cls._convert_value(value, value_type)

    @classmethod
    def _get_schema_value(cls, key):
        """Get a value from the schema if it's not in the config."""
        schema = cls.get_schema()
        keys = cls._split_keys(key)
        value = schema
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        if isinstance(value, dict) and 'value' in value:
            return cls._convert_value(value['value'], value.get('type'))
        return None

    @staticmethod
    def _convert_value(value, value_type):
        """Convert a value to the specified type."""
        if value_type == 'int':
            return int(value) if value is not None and value != '' else None
        elif value_type == 'float':
            return float(value) if value is not None and value != '' else None
        elif value_type == 'bool':
            return bool(value) if isinstance(value, bool) else value.lower() in ('true', 'yes',
                                                                                 'on', '1')
        elif value_type == 'int or null':
            if value is None or value == '':
                return None
            try:
                return int(value)
            except ValueError:
                return value  # Keep it as a string if it's not convertible to int
        elif value_type == 'list':
            return list(value) if value is not None else []
        else:
            return value  # For strings and other types, return as is

    @classmethod
    def set_config_value(cls, key, value):
        """Set a specific configuration value using a dotted key."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        keys = cls._split_keys(key)
        config = cls._instance.config
        schema = cls._instance.schema
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            if k not in schema:
                schema[k] = {}
            config = config[k]
            schema = schema[k]

        value_type = schema[keys[-1]].get('type') if keys[-1] in schema else None
        config[keys[-1]] = cls._convert_value(value, value_type)

    @classmethod
    def _load_config_schema(cls, schema_path=None):
        """Load the configuration schema from a YAML file."""
        if schema_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(base_dir, 'config_schema.yaml')

        with open(schema_path, 'r') as file:
            schema = yaml.safe_load(file)
        return schema

    def _load_default_config(self):
        """Load default configuration values from the schema."""
        def extract_value(item):
            if isinstance(item, dict):
                if 'value' in item:
                    return self._convert_value(item['value'], item.get('type'))
                else:
                    return {k: extract_value(v) for k, v in item.items()}
            return item

        return extract_value(self.schema)

    def _load_user_config(self, config_path=os.path.join('src', 'config.yaml')):
        """Load user configuration and merge with default config."""
        if config_path and os.path.isfile(config_path):
            try:
                with open(config_path, 'r') as file:
                    user_config = yaml.safe_load(file)
                    self._merge_configs(self.config, user_config)
            except yaml.YAMLError:
                print("Error in configuration file. Using default configuration.")

    def _merge_configs(self, default_config, user_config):
        for key, value in user_config.items():
            if isinstance(value, dict):
                if key not in default_config:
                    default_config[key] = {}
                self._merge_configs(default_config[key], value)
            else:
                schema_value = self.schema
                for k in self._split_keys(key):
                    schema_value = schema_value.get(k, {})
                value_type = schema_value.get('type')
                default_config[key] = self._convert_value(value, value_type)

    @classmethod
    def get_all_keys(cls):
        """Get all configuration keys in dotted format."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        def get_keys(config, prefix=''):
            keys = []
            for key, value in config.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    keys.extend(get_keys(value, new_key))
                elif isinstance(value, list):
                    keys.append(new_key)
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            keys.extend(get_keys(item, f"{new_key}.{i}"))
                else:
                    keys.append(new_key)
            return keys

        return get_keys(cls._instance.config)

    @classmethod
    def save_config(cls, config_path=os.path.join('src', 'config.yaml')):
        """Save the current configuration to a YAML file, excluding capabilities."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        config_to_save = cls._instance.config.copy()
        cls._remove_capabilities(config_to_save)

        with open(config_path, 'w') as file:
            yaml.dump(config_to_save, file, default_flow_style=False)

    @classmethod
    def _remove_capabilities(cls, config):
        """Recursively remove 'capabilities' from the config."""
        if isinstance(config, dict):
            config.pop('capabilities', None)
            for value in config.values():
                cls._remove_capabilities(value)
        elif isinstance(config, list):
            for item in config:
                cls._remove_capabilities(item)

    @classmethod
    def reload_config(cls):
        """
        Reload the configuration from the file.
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        cls._instance.config = cls._instance._load_default_config()
        cls._instance._load_user_config()

    @classmethod
    def config_file_exists(cls):
        """Check if a valid config file exists."""
        config_path = os.path.join('src', 'config.yaml')
        return os.path.isfile(config_path)

    @staticmethod
    def _split_keys(dotted_key):
        return dotted_key.split('.')

    @classmethod
    def _remove_config_value(cls, key):
        """Remove a configuration value using a dotted key."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        keys = cls._split_keys(key)
        config = cls._instance.config
        for k in keys[:-1]:
            if k in config:
                config = config[k]
            else:
                return  # Key doesn't exist, nothing to remove
        if keys[-1] in config:
            del config[keys[-1]]

    @classmethod
    def clean_config(cls):
        """Remove configuration values that are not in the schema."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        schema_keys = set(cls._get_all_keys_from_schema())
        config_keys = set(cls.get_all_keys())
        keys_to_remove = config_keys - schema_keys

        for key in keys_to_remove:
            cls._remove_config_value(key)

    @classmethod
    def _get_all_keys_from_schema(cls):
        """Get all keys from the schema in dotted format."""
        def get_keys(schema, prefix=''):
            keys = []
            for key, value in schema.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    if 'type' in value and value['type'] == 'list':
                        keys.append(new_key)
                    elif 'value' not in value:
                        keys.extend(get_keys(value, new_key))
                    else:
                        keys.append(new_key)
            return keys

        return get_keys(cls._instance.schema)

    @classmethod
    def get_available_scripts(cls):
        """Get a list of available post-processing scripts."""
        scripts_dir = os.path.join('scripts')
        if not os.path.exists(scripts_dir):
            return []
        return [f[:-3] for f in os.listdir(scripts_dir)
                if f.endswith('.py') and f != '__init__.py']

    @classmethod
    def console_print(cls, message):
        """Print a message to the console if enabled in the configuration."""
        if cls._instance and cls._instance.config['misc']['print_to_terminal']:
            print(message)
