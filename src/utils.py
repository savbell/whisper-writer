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
            cls._instance.schema = cls._instance.load_config_schema(schema_path)
            cls._instance.config = cls._instance.load_config_values()

    @classmethod
    def get_schema(cls):
        """Get the configuration schema."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        return cls._instance.schema

    @classmethod
    def get_config_section(cls, section):
        """Get a specific section of the configuration."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        return cls._instance.config.get(section, {})

    @classmethod
    def get_config_value(cls, *keys):
        """Get a specific configuration value using nested keys."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        value = cls._instance.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    @classmethod
    def set_config_value(cls, value, *keys):
        """Set a specific configuration value using nested keys."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        config = cls._instance.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    @classmethod
    def console_print(cls, message):
        """Print a message to the console if enabled in the configuration."""
        if cls._instance and cls._instance.config['misc']['print_to_terminal']:
            print(message)

    @staticmethod
    def load_config_schema(schema_path=None):
        """Load the configuration schema from a YAML file."""
        if schema_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(base_dir, 'config_schema.yaml')

        with open(schema_path, 'r') as file:
            schema = yaml.safe_load(file)
        return schema

    def load_config_values(self, config_path=os.path.join('src', 'config.yaml')):
        """Load configuration values from a YAML file, using schema as default."""
        config = {}
        for category, settings in self.schema.items():
            config[category] = {}
            for sub_category, sub_settings in settings.items():
                if isinstance(sub_settings, dict) and 'value' in sub_settings:
                    config[category][sub_category] = sub_settings['value']
                else:
                    config[category][sub_category] = {}
                    for key, meta in sub_settings.items():
                        config[category][sub_category][key] = meta['value']

        # Load user settings if they exist
        if config_path and os.path.isfile(config_path):
            with open(config_path, 'r') as file:
                user_config = yaml.safe_load(file)
                for category, settings in user_config.items():
                    if category in config:
                        for sub_category, sub_settings in settings.items():
                            if isinstance(sub_settings, dict):
                                for key, value in sub_settings.items():
                                    config[category][sub_category][key] = value
                            else:
                                config[category][sub_category] = sub_settings

        return config

    @classmethod
    def save_config(cls, config_path=os.path.join('src', 'config.yaml')):
        """Save the current configuration to a YAML file."""
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        with open(config_path, 'w') as file:
            yaml.dump(cls._instance.config, file, default_flow_style=False)

    @classmethod
    def reload_config(cls):
        """
        Reload the configuration from the file.
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        cls._instance.config = cls._instance.load_config_values()
