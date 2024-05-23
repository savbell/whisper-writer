from PyQt5.QtCore import QThread, pyqtSignal
from pynput import keyboard

class KeyListener(QThread):
    activationKeyPressed = pyqtSignal()
    activationKeyReleased = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.required_keys = set(config['recording_options']['activation_key'].split('+'))
        self.pressed_keys = set()
        self.is_key_pressed = False
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

    """
    Check if the required keys are pressed and emit the activationKeyPressed signal.
    """
    def on_press(self, key):
        if not self.is_key_pressed:
            if hasattr(key, 'name'):
                self.pressed_keys.add(key.name)
            elif hasattr(key, 'char'):
                self.pressed_keys.add(key.char)
            elif hasattr(key, 'vk'):
                self.pressed_keys.add(str(key.vk))
            
            if self.required_keys.issubset(self.pressed_keys) and not self.is_key_pressed:
                self.is_key_pressed = True
                self.activationKeyPressed.emit()

    """
    Check if the required keys are released and emit the activationKeyReleased signal.
    """
    def on_release(self, key):
        if hasattr(key, 'name'):
            self.pressed_keys.discard(key.name)
        elif hasattr(key, 'char'):
            self.pressed_keys.discard(key.char)
        elif hasattr(key, 'vk'):
            self.pressed_keys.discard(str(key.vk))
        
        if not self.required_keys.issubset(self.pressed_keys) and self.is_key_pressed:
            self.is_key_pressed = False
            self.activationKeyReleased.emit()
    
    
    """
    Start listening for key events.
    """
    def start_listening(self):
        if self.listener and self.listener.running:
            self.listener.stop()
        
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()