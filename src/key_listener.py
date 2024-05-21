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

    def on_press(self, key):
        if not self.is_key_pressed:
            if hasattr(key, 'name'):
                self.pressed_keys.add(key.name)
            elif hasattr(key, 'char'):
                self.pressed_keys.add(key.char)
            
            if self.required_keys.issubset(self.pressed_keys) and not self.is_key_pressed:
                self.is_key_pressed = True
                self.activationKeyPressed.emit()

    def on_release(self, key):
        if hasattr(key, 'name'):
            self.pressed_keys.discard(key.name)
        elif hasattr(key, 'char'):
            self.pressed_keys.discard(key.char)
        
        if not self.required_keys.issubset(self.pressed_keys) and self.is_key_pressed:
            self.is_key_pressed = False
            self.activationKeyReleased.emit()
        
    def start_listening(self):
        self.listener.start()
        self.start()
