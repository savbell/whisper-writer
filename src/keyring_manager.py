import keyring
from utils import ConfigManager

class KeyringManager:
    APP_NAME = "whisperwriter"
    
    @staticmethod
    def save_api_key(service_name: str, key: str):
        """Save an API key to the system keyring."""
        if not key:  # If key is empty, remove it from keyring
            try:
                keyring.delete_password(KeyringManager.APP_NAME, service_name)
            except keyring.errors.PasswordDeleteError:
                pass  # Key doesn't exist, that's fine
            return
            
        keyring.set_password(KeyringManager.APP_NAME, service_name, key)
        ConfigManager.console_print(f"Saved {service_name} API key to keyring")

    @staticmethod
    def get_api_key(service_name: str) -> str:
        """Get an API key from the system keyring."""
        try:
            key = keyring.get_password(KeyringManager.APP_NAME, service_name)
            return key if key else ""
        except:
            return ""