import os
import importlib.util
from typing import List

from utils import ConfigManager
from post_processing_base import PostProcessor


class PostProcessingManager:
    def __init__(self):
        self.scripts_folder = 'scripts'
        self.enabled_scripts = ConfigManager.get_config_value('post_processing.enabled_scripts')
        self.processors: List[PostProcessor] = []
        self._load_processors()

    def _load_processors(self):
        for script_name in self.enabled_scripts:
            script_path = os.path.join(self.scripts_folder, f"{script_name}.py")
            if os.path.exists(script_path):
                try:
                    spec = importlib.util.spec_from_file_location(script_name, script_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    processor_class = getattr(module, 'Processor')
                    if issubclass(processor_class, PostProcessor):
                        self.processors.append(processor_class())
                    else:
                        print(f"Warning: {script_name} does not contain a valid Processor class")
                except Exception as e:
                    print(f"Error loading {script_name}: {str(e)}")
            else:
                print(f"Warning: Script {script_name} not found")

    def process(self, text: str) -> str:
        for processor in self.processors:
            text = processor.process(text)
        return text


def post_process(text: str) -> str:
    manager = PostProcessingManager()
    return manager.process(text)
