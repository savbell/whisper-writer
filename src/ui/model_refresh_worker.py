from PyQt5.QtCore import QObject, pyqtSignal
from utils import ConfigManager

class ModelRefreshWorker(QObject):
    finished = pyqtSignal(list)

    def __init__(self, llm_processor, api_type):
        super().__init__()
        self.llm_processor = llm_processor
        self.api_type = api_type

    def run(self):
        """Fetch models and emit results."""
        ConfigManager.console_print(f"\n=== ModelRefreshWorker Running ===")
        ConfigManager.console_print(f"API Type: {self.api_type}")
        try:
            ConfigManager.console_print("Calling get_available_models...")
            models = self.llm_processor.get_available_models(self.api_type)
            ConfigManager.console_print(f"Models received: {models}")
        except Exception as e:
            ConfigManager.console_print(f"Error in worker: {str(e)}")
            models = []
        
        ConfigManager.console_print(f"Emitting finished signal with models: {models}")
        self.finished.emit(models)
        ConfigManager.console_print("=== ModelRefreshWorker Complete ===\n")
