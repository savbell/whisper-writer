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
            self.pressed_keys.add(self.get_key_name(key))
            
            if self.required_keys.issubset(self.pressed_keys) and not self.is_key_pressed:
                self.is_key_pressed = True
                self.activationKeyPressed.emit()

    """
    Check if the required keys are released and emit the activationKeyReleased signal.
    """
    def on_release(self, key):
        self.pressed_keys.discard(self.get_key_name(key))
        
        if not self.required_keys.issubset(self.pressed_keys) and self.is_key_pressed:
            self.is_key_pressed = False
            self.activationKeyReleased.emit()
    
    """
    Get the key name from the key object.
    """
    def get_key_name(self, key):
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return 'ctrl'
        elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            return 'shift'
        elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            return 'alt'
        elif key in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            return 'cmd'
        elif hasattr(key, 'char'):
            return key.char
        elif hasattr(key, 'name'):
            return key.name
        return str(key)
    
    """
    Start listening for key events.
    """
    def start_listening(self):
        if self.listener and self.listener.running:
            self.listener.stop()
        
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()