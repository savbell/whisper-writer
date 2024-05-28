import yaml
import os

def load_config_schema(schema_path=None):
    """
    Loads the schema for the configuration file.
    """
    if schema_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base_dir, 'config_schema.yaml')
    
    with open(schema_path, 'r') as file:
        schema = yaml.safe_load(file)
    return schema

def load_config_values(schema, config_path=os.path.join('src', 'config.yaml')):
    """
    Loads the values from the configuration file.
    """
    config = {}
    for category, settings in schema.items():
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

def save_config(config, config_path=os.path.join('src', 'config.yaml')):
    """
    Save the configuration to a yaml file.
    """
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
        