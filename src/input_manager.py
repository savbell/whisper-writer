from typing import Set, Dict, Type

from event_bus import EventBus
from enums import InputEvent, KeyCode
from config_manager import ConfigManager
from input_backend.input_backend_base import InputBackendBase
from input_backend.evdev_backend import EvdevBackend
from input_backend.pynput_backend import PynputBackend


class KeyChord:
    """Represents a combination of keys that need to be pressed simultaneously."""

    def __init__(self, keys: Set[KeyCode | frozenset[KeyCode]]):
        """Initialize the KeyChord."""
        self.keys = keys
        self.pressed_keys: Set[KeyCode] = set()

    def update(self, key: KeyCode, event_type: InputEvent) -> bool:
        """Update the state of pressed keys and check if the chord is active."""
        if event_type == InputEvent.KEY_PRESS:
            self.pressed_keys.add(key)
        elif event_type == InputEvent.KEY_RELEASE:
            self.pressed_keys.discard(key)
        return self.is_active()

    def is_active(self) -> bool:
        """Check if all keys in the chord are currently pressed."""
        for key in self.keys:
            if isinstance(key, frozenset):
                if not any(k in self.pressed_keys for k in key):
                    return False
            elif key not in self.pressed_keys:
                return False
        return True


class InputManager:
    """Manages input backends and listens for specific key combinations."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_backend: InputBackendBase | None = None
        self.shortcuts: Dict[str, KeyChord] = {}
        self.backend_classes: Dict[str, Type[InputBackendBase]] = {
            'evdev': EvdevBackend,
            'pynput': PynputBackend
        }
        self.load_shortcuts()
        self.initialize_active_backend()

    def load_shortcuts(self):
        active_profiles = ConfigManager.get_profiles(active_only=True)
        for profile in active_profiles:
            profile_name = profile['name']
            shortcut = ConfigManager.get_value('activation_key', profile_name)
            keys = self.parse_key_combination(shortcut)
            self.shortcuts[profile_name] = KeyChord(keys)

    def initialize_active_backend(self):
        preferred_backend = ConfigManager.get_value('global_options.input_backend')

        if preferred_backend == 'auto' or preferred_backend not in self.backend_classes:
            self.select_auto_backend()
        else:
            try:
                self.set_active_backend(self.backend_classes[preferred_backend])
            except ValueError:
                print(f"Preferred backend '{preferred_backend}' failed to initialize. "
                      f"Falling back to auto selection.")
                self.select_auto_backend()

    def select_auto_backend(self):
        for backend_class in self.backend_classes.values():
            if backend_class.is_available():
                try:
                    self.set_active_backend(backend_class)
                    return
                except ValueError:
                    continue
        raise RuntimeError("No supported input backend found")

    def set_active_backend(self, backend_class: Type[InputBackendBase]):
        if self.active_backend:
            self.stop()
            self.active_backend = None

        if backend_class.is_available():
            new_backend = backend_class()
            new_backend.on_input_event = self.on_input_event
            self.active_backend = new_backend
        else:
            raise ValueError(f"Backend {backend_class.__name__} is not available")

    def start(self):
        if self.active_backend:
            self.active_backend.start()
        else:
            raise RuntimeError("No active backend selected")

    def stop(self):
        if self.active_backend:
            self.active_backend.stop()

    def parse_key_combination(self, combination_string: str) -> Set[KeyCode | frozenset[KeyCode]]:
        """Parse a string representation of key combination into a set of KeyCodes."""
        keys = set()
        key_map = {
            'CTRL': frozenset({KeyCode.CTRL_LEFT, KeyCode.CTRL_RIGHT}),
            'SHIFT': frozenset({KeyCode.SHIFT_LEFT, KeyCode.SHIFT_RIGHT}),
            'ALT': frozenset({KeyCode.ALT_LEFT, KeyCode.ALT_RIGHT}),
            'META': frozenset({KeyCode.META_LEFT, KeyCode.META_RIGHT}),
        }

        for key in combination_string.upper().split('+'):
            key = key.strip()
            if key in key_map:
                keys.add(key_map[key])
            else:
                try:
                    keycode = KeyCode[key]
                    keys.add(keycode)
                except KeyError:
                    print(f"Unknown key: {key}")
        return keys

    def on_input_event(self, event):
        """Handle input events and trigger callbacks if the key chord becomes active."""
        key, event_type = event

        for profile_name, key_chord in self.shortcuts.items():
            was_active = key_chord.is_active()
            is_active = key_chord.update(key, event_type)

            if not was_active and is_active:
                self.event_bus.emit("shortcut_triggered", profile_name, "press")
            elif was_active and not is_active:
                self.event_bus.emit("shortcut_triggered", profile_name, "release")

    def update_shortcuts(self):
        self.load_shortcuts()

    def cleanup(self):
        self.stop()
        # Reset all attributes to enforce garbage collection
        self.active_backend = None
        self.shortcuts = None
