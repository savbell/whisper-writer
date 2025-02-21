from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Callable, Set
import time

from utils import ConfigManager


class InputEvent(Enum):
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    MOUSE_PRESS = auto()
    MOUSE_RELEASE = auto()

class KeyCode(Enum):
    """Enum for key codes."""
    # Modifier keys
    CTRL_LEFT = auto()
    CTRL_RIGHT = auto()
    SHIFT_LEFT = auto()
    SHIFT_RIGHT = auto()
    ALT_LEFT = auto()
    ALT_RIGHT = auto()
    META_LEFT = auto()
    META_RIGHT = auto()

    # Function keys
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()
    F13 = auto()
    F14 = auto()
    F15 = auto()
    F16 = auto()
    F17 = auto()
    F18 = auto()
    F19 = auto()
    F20 = auto()
    F21 = auto()
    F22 = auto()
    F23 = auto()
    F24 = auto()

    # Number keys
    ONE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()
    SIX = auto()
    SEVEN = auto()
    EIGHT = auto()
    NINE = auto()
    ZERO = auto()

    # Letter keys
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    G = auto()
    H = auto()
    I = auto()
    J = auto()
    K = auto()
    L = auto()
    M = auto()
    N = auto()
    O = auto()
    P = auto()
    Q = auto()
    R = auto()
    S = auto()
    T = auto()
    U = auto()
    V = auto()
    W = auto()
    X = auto()
    Y = auto()
    Z = auto()

    # Special keys
    SPACE = auto()
    ENTER = auto()
    TAB = auto()
    BACKSPACE = auto()
    ESC = auto()
    INSERT = auto()
    DELETE = auto()
    HOME = auto()
    END = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    CAPS_LOCK = auto()
    NUM_LOCK = auto()
    SCROLL_LOCK = auto()
    PAUSE = auto()
    PRINT_SCREEN = auto()

    # Arrow keys
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

    # Numpad keys
    NUMPAD_0 = 96
    NUMPAD_1 = 97
    NUMPAD_2 = 98
    NUMPAD_3 = 99
    NUMPAD_4 = 100
    NUMPAD_5 = 101
    NUMPAD_6 = 102
    NUMPAD_7 = 103
    NUMPAD_8 = 104
    NUMPAD_9 = 105
    NUMPAD_MULTIPLY = 106
    NUMPAD_ADD = 107
    NUMPAD_SUBTRACT = 109
    NUMPAD_DECIMAL = 110
    NUMPAD_DIVIDE = 111

    # Additional special characters
    MINUS = auto()
    EQUALS = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    SEMICOLON = auto()
    QUOTE = auto()
    BACKQUOTE = auto()
    BACKSLASH = auto()
    COMMA = auto()
    PERIOD = auto()
    SLASH = auto()

    # Media keys
    MUTE = auto()
    VOLUME_DOWN = auto()
    VOLUME_UP = auto()
    PLAY_PAUSE = auto()
    NEXT_TRACK = auto()
    PREV_TRACK = auto()

    # Additional Media and Special Function Keys
    MEDIA_PLAY = auto()
    MEDIA_PAUSE = auto()
    MEDIA_PLAY_PAUSE = auto()
    MEDIA_STOP = auto()
    MEDIA_PREVIOUS = auto()
    MEDIA_NEXT = auto()
    MEDIA_REWIND = auto()
    MEDIA_FAST_FORWARD = auto()
    AUDIO_MUTE = auto()
    AUDIO_VOLUME_UP = auto()
    AUDIO_VOLUME_DOWN = auto()
    MEDIA_SELECT = auto()
    WWW = auto()
    MAIL = auto()
    CALCULATOR = auto()
    COMPUTER = auto()
    APP_SEARCH = auto()
    APP_HOME = auto()
    APP_BACK = auto()
    APP_FORWARD = auto()
    APP_STOP = auto()
    APP_REFRESH = auto()
    APP_BOOKMARKS = auto()
    BRIGHTNESS_DOWN = auto()
    BRIGHTNESS_UP = auto()
    DISPLAY_SWITCH = auto()
    KEYBOARD_ILLUMINATION_TOGGLE = auto()
    KEYBOARD_ILLUMINATION_DOWN = auto()
    KEYBOARD_ILLUMINATION_UP = auto()
    EJECT = auto()
    SLEEP = auto()
    WAKE = auto()
    EMOJI = auto()
    MENU = auto()
    CLEAR = auto()
    LOCK = auto()

    # Mouse Buttons
    MOUSE_LEFT = auto()
    MOUSE_RIGHT = auto()
    MOUSE_MIDDLE = auto()
    MOUSE_BACK = auto()
    MOUSE_FORWARD = auto()
    MOUSE_SIDE1 = auto()
    MOUSE_SIDE2 = auto()
    MOUSE_SIDE3 = auto()

class InputBackend(ABC):
    """
    Abstract base class for input backends.
    This class defines the interface that all input backends must implement.
    """

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """
        Check if this input backend is available on the current system.

        Returns:
            bool: True if the backend is available, False otherwise.
        """
        pass

    @abstractmethod
    def start(self):
        """
        Start the input backend.
        This method should initialize any necessary resources and begin listening for input events.
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop the input backend.
        This method should clean up any resources and stop listening for input events.
        """
        pass

    @abstractmethod
    def on_input_event(self, event: tuple[KeyCode, InputEvent]):
        """
        Handle an input event.
        This method is called when an input event is detected.

        :param event (Tuple[KeyCode, InputEvent]): A tuple containing the key code and the type of event.
        """
        pass

class KeyChord:
    """
    Represents a combination of keys that need to be pressed simultaneously.
    """

    def __init__(self, keys: Set[KeyCode | frozenset[KeyCode]]):
        """Initialize the KeyChord."""
        self.keys = keys
        self.pressed_keys: Set[KeyCode] = set()
        if keys:
            self.is_single_key = len(keys) == 1 and isinstance(next(iter(keys)), KeyCode)
            self.target_key = next(iter(keys)) if self.is_single_key else None
        else:
            self.is_single_key = False
            self.target_key = None
        self.last_trigger_time = 0
        self.debounce_delay = 0.3
        self.is_recording = False  # Track recording state

    def update(self, key: KeyCode, event_type: InputEvent) -> bool:
        """Update the state of pressed keys and check if the chord is active."""
        current_time = time.time()
        
        if event_type == InputEvent.KEY_PRESS:
            self.pressed_keys.add(key)
        else:
            self.pressed_keys.discard(key)
            
        # For single modifier keys, we want to trigger on press and maintain state until release
        if self.is_single_key and key == self.target_key:
            if event_type == InputEvent.KEY_PRESS:
                if current_time - self.last_trigger_time >= self.debounce_delay:
                    self.last_trigger_time = current_time
                    self.is_recording = True
                    return True
            elif event_type == InputEvent.KEY_RELEASE:
                self.is_recording = False
                return False
            return self.is_recording
            
        # For key combinations
        is_active = self.is_active()
        if is_active and current_time - self.last_trigger_time >= self.debounce_delay:
            self.last_trigger_time = current_time
            self.is_recording = True
            return True
        elif not is_active and self.is_recording:
            self.is_recording = False
            return False
        return self.is_recording

    def is_active(self) -> bool:
        """Check if all keys in the chord are currently pressed."""
        for key in self.keys:
            if isinstance(key, frozenset):
                if not any(k in self.pressed_keys for k in key):
                    return False
            elif key not in self.pressed_keys:
                return False
        return True

class KeyListener:
    """
    Manages input backends and listens for specific key combinations.
    """

    def __init__(self):
        """Initialize the KeyListener with backends and activation keys."""
        self.backends = []
        self.active_backend = None
        self.main_key_chord = None
        self.llm_key_chord = None
        self.llm_instruction_key_chord = None
        self.text_cleanup_chord = None
        self.callbacks = {
            "on_activate": [],
            "on_deactivate": [],
            "on_activate_with_llm": [],
            "on_deactivate_with_llm": [],
            "on_activate_with_llm_instruction": [],
            "on_deactivate_with_llm_instruction": [],
            "on_text_cleanup": []
        }
        self.load_activation_keys()
        self.initialize_backends()
        self.select_backend_from_config()

    def initialize_backends(self):
        """Initialize available input backends."""
        backend_classes = [EvdevBackend, PynputBackend]
        self.backends = [backend_class() for backend_class in backend_classes if backend_class.is_available()]

    def select_backend_from_config(self):
        """Select the active backend based on configuration."""
        preferred_backend = ConfigManager.get_config_value('recording_options', 'input_backend')

        if preferred_backend == 'auto':
            self.select_active_backend()
        else:
            backend_map = {
                'evdev': EvdevBackend,
                'pynput': PynputBackend
            }

            if preferred_backend in backend_map:
                try:
                    self.set_active_backend(backend_map[preferred_backend])
                except ValueError:
                    print(f"Preferred backend '{preferred_backend}' is not available. Falling back to auto selection.")
                    self.select_active_backend()
            else:
                print(f"Unknown backend '{preferred_backend}'. Falling back to auto selection.")
                self.select_active_backend()

    def select_active_backend(self):
        """Select the first available backend as active."""
        if not self.backends:
            raise RuntimeError("No supported input backend found")
        self.active_backend = self.backends[0]
        self.active_backend.on_input_event = self.on_input_event

    def set_active_backend(self, backend_class):
        """Set a specific backend as active."""
        new_backend = next((b for b in self.backends if isinstance(b, backend_class)), None)
        if new_backend:
            if self.active_backend:
                self.stop()
            self.active_backend = new_backend
            self.active_backend.on_input_event = self.on_input_event
            self.start()
        else:
            raise ValueError(f"Backend {backend_class.__name__} is not available")

    def update_backend(self):
        """Update the active backend based on current configuration."""
        self.select_backend_from_config()

    def start(self):
        """Start the active backend."""
        if self.active_backend:
            self.active_backend.start()
        else:
            raise RuntimeError("No active backend selected")

    def stop(self):
        """Stop the active backend."""
        if self.active_backend:
            self.active_backend.stop()

    def load_activation_keys(self):
        """Load activation keys from configuration."""
        main_key = ConfigManager.get_config_value('recording_options', 'activation_key')
        llm_key = ConfigManager.get_config_value('recording_options', 'llm_cleanup_key')
        llm_instruction_key = ConfigManager.get_config_value('recording_options', 'llm_instruction_key')
        text_cleanup_key = ConfigManager.get_config_value('recording_options', 'text_cleanup_key')
        
        main_keys = self.parse_key_combination(main_key)
        llm_keys = self.parse_key_combination(llm_key)
        llm_instruction_keys = self.parse_key_combination(llm_instruction_key)
        text_cleanup_keys = self.parse_key_combination(text_cleanup_key)
        
        self.main_key_chord = KeyChord(main_keys)
        self.llm_key_chord = KeyChord(llm_keys)
        self.llm_instruction_key_chord = KeyChord(llm_instruction_keys)
        self.text_cleanup_chord = KeyChord(text_cleanup_keys)

    def parse_key_combination(self, combination_string: str) -> Set[KeyCode | frozenset[KeyCode]]:
        """Parse a string representation of key combination into a set of KeyCodes."""
        if not combination_string:
            return set()
        
        keys = set()
        modifier_map = {
            'ctrl': frozenset({KeyCode.CTRL_LEFT, KeyCode.CTRL_RIGHT}),
            'lctrl': KeyCode.CTRL_LEFT,
            'rctrl': KeyCode.CTRL_RIGHT,
            'alt': frozenset({KeyCode.ALT_LEFT, KeyCode.ALT_RIGHT}),
            'lalt': KeyCode.ALT_LEFT,
            'ralt': KeyCode.ALT_RIGHT,
            'shift': frozenset({KeyCode.SHIFT_LEFT, KeyCode.SHIFT_RIGHT}),
            'lshift': KeyCode.SHIFT_LEFT,
            'rshift': KeyCode.SHIFT_RIGHT,
            'meta': frozenset({KeyCode.META_LEFT, KeyCode.META_RIGHT}),
            'lmeta': KeyCode.META_LEFT,
            'rmeta': KeyCode.META_RIGHT,
        }

        # Add number key mappings
        number_map = {
            '0': KeyCode.ZERO, '1': KeyCode.ONE, '2': KeyCode.TWO,
            '3': KeyCode.THREE, '4': KeyCode.FOUR, '5': KeyCode.FIVE,
            '6': KeyCode.SIX, '7': KeyCode.SEVEN, '8': KeyCode.EIGHT,
            '9': KeyCode.NINE
        }

        # Add numpad key mappings
        numpad_map = {
            'numpad0': KeyCode.NUMPAD_0,
            'numpad1': KeyCode.NUMPAD_1,
            'numpad2': KeyCode.NUMPAD_2,
            'numpad3': KeyCode.NUMPAD_3,
            'numpad4': KeyCode.NUMPAD_4,
            'numpad5': KeyCode.NUMPAD_5,
            'numpad6': KeyCode.NUMPAD_6,
            'numpad7': KeyCode.NUMPAD_7,
            'numpad8': KeyCode.NUMPAD_8,
            'numpad9': KeyCode.NUMPAD_9,
            'multiply': KeyCode.NUMPAD_MULTIPLY,
            'add': KeyCode.NUMPAD_ADD,
            'subtract': KeyCode.NUMPAD_SUBTRACT,
            'decimal': KeyCode.NUMPAD_DECIMAL,
            'divide': KeyCode.NUMPAD_DIVIDE,
        }

        for key in combination_string.lower().split('+'):
            key = key.strip()
            if key in modifier_map:
                keys.add(modifier_map[key])
            elif key in number_map:
                keys.add(number_map[key])
            elif key in numpad_map:
                keys.add(numpad_map[key])
            else:
                try:
                    keycode = KeyCode[key.upper()]
                    keys.add(keycode)
                except KeyError:
                    pass
        
        return keys

    def on_input_event(self, event):
        """Handle input events and trigger callbacks if either key chord becomes active or inactive."""
        if not self.active_backend:
            return

        key, event_type = event

        # Check main activation chord
        if self.main_key_chord:
            was_active = self.main_key_chord.is_active()
            is_active = self.main_key_chord.update(key, event_type)

            if not was_active and is_active:
                self._trigger_callbacks("on_activate")
            elif was_active and not is_active:
                self._trigger_callbacks("on_deactivate")

        # Check LLM cleanup chord
        if self.llm_key_chord:
            was_active_llm = self.llm_key_chord.is_active()
            is_active_llm = self.llm_key_chord.update(key, event_type)

            if not was_active_llm and is_active_llm:
                self._trigger_callbacks("on_activate_with_llm")
            elif was_active_llm and not is_active_llm:
                self._trigger_callbacks("on_deactivate_with_llm")

        # Check LLM instruction chord
        if self.llm_instruction_key_chord:
            was_active_llm_instruction = self.llm_instruction_key_chord.is_active()
            is_active_llm_instruction = self.llm_instruction_key_chord.update(key, event_type)

            if not was_active_llm_instruction and is_active_llm_instruction:
                self._trigger_callbacks("on_activate_with_llm_instruction")
            elif was_active_llm_instruction and not is_active_llm_instruction:
                self._trigger_callbacks("on_deactivate_with_llm_instruction")

        # Check text selection cleanup chord
        if self.text_cleanup_chord:
            was_active_text = self.text_cleanup_chord.is_active()
            is_active_text = self.text_cleanup_chord.update(key, event_type)

            if not was_active_text and is_active_text:
                self._trigger_callbacks("on_text_cleanup")

    def add_callback(self, event: str, callback: Callable):
        """Add a callback function for a specific event."""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _trigger_callbacks(self, event: str):
        """Trigger all callbacks associated with a specific event."""
        for callback in self.callbacks.get(event, []):
            callback()

    def update_activation_keys(self):
        """Update activation keys from the current configuration."""
        self.load_activation_keys()

class EvdevBackend(InputBackend):
    """
    Backend for handling input events using the evdev library.
    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if the evdev library is available."""
        try:
            import evdev
            return True
        except ImportError:
            return False

    def __init__(self):
        """Initialize the EvdevBackend."""
        self.devices: List[evdev.InputDevice] = []
        self.key_map: Optional[dict] = None
        self.evdev = None
        self.thread: Optional[threading.Thread] = None
        self.stop_event: Optional[threading.Event] = None

    def start(self):
        """Start the evdev backend."""
        import evdev
        import threading
        self.evdev = evdev
        self.key_map = self._create_key_map()

        # Initialize input devices
        self.devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        self.stop_event = threading.Event()
        self._setup_signal_handler()
        self._start_listening()

    def _setup_signal_handler(self):
        """Set up signal handlers for graceful shutdown."""
        import signal

        def signal_handler(signum, frame):
            print("Received termination signal. Stopping evdev backend...")
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def stop(self):
        """Stop the evdev backend and clean up resources."""
        if self.stop_event:
            self.stop_event.set()

        if self.thread:
            self.thread.join(timeout=1)  # Wait for up to 1 second
            if self.thread.is_alive():
                print("Thread did not terminate in time. Forcing exit.")

        # Close all devices
        for device in self.devices:
            try:
                device.close()
            except Exception:
                pass  # Ignore errors when closing devices
        self.devices = []

    def _start_listening(self):
        """Start the listening thread."""
        import threading
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.start()

    def _listen_loop(self):
        """Main loop for listening to input events."""
        import select
        while not self.stop_event.is_set():
            try:
                # Wait for input events with a timeout of 0.1 seconds
                r, _, _ = select.select(self.devices, [], [], 0.1)
                for device in r:
                    self._read_device_events(device)
            except Exception as e:
                if self.stop_event.is_set():
                    break
                print(f"Unexpected error in _listen_loop: {e}")

    def _read_device_events(self, device):
        """Read and process events from a single device."""
        try:
            for event in device.read():
                if event.type == self.evdev.ecodes.EV_KEY:
                    self._handle_input_event(event)
        except Exception as e:
            self._handle_device_error(device, e)

    def _handle_device_error(self, device, error):
        """Handle errors that occur when reading from a device."""
        import errno
        if isinstance(error, BlockingIOError) and error.errno == errno.EAGAIN:
            return  # Non-blocking IO is expected, just continue
        if isinstance(error, OSError) and (error.errno == errno.EBADF or error.errno == errno.ENODEV):
            print(f"Device {device.path} is no longer available. Removing it.")
            self.devices.remove(device)
        else:
            print(f"Unexpected error reading device: {error}")

    def _handle_input_event(self, event):
        """Process a single input event."""
        key_code, event_type = self._translate_key_event(event)
        if key_code is not None and event_type is not None:
            self.on_input_event((key_code, event_type))

    def _translate_key_event(self, native_event) -> Optional[tuple[KeyCode, InputEvent]]:
        """Translate a pynput event to our internal event representation."""
        # For evdev backend
        if hasattr(native_event, 'keystate'):
            key_event = native_event
            if key_event.keystate in [key_event.key_down, key_event.key_hold]:
                event_type = InputEvent.KEY_PRESS
            elif key_event.keystate == key_event.key_up:
                event_type = InputEvent.KEY_RELEASE
            else:
                return None
            
            key_code = self.key_map.get(key_event.scancode)
            if key_code is None:
                return None
            
            return key_code, event_type

        # For pynput backend
        pynput_key, is_press = native_event
        
        # Handle character keys
        if isinstance(pynput_key, self.keyboard.KeyCode):
            # Try to map from virtual key code first
            if hasattr(pynput_key, 'vk') and pynput_key.vk is not None:
                vk = pynput_key.vk
                
                # Map numpad virtual key codes (96-111)
                if 96 <= vk <= 111:
                    numpad_map = {
                        96: KeyCode.NUMPAD_0,
                        97: KeyCode.NUMPAD_1,
                        98: KeyCode.NUMPAD_2,
                        99: KeyCode.NUMPAD_3,
                        100: KeyCode.NUMPAD_4,
                        101: KeyCode.NUMPAD_5,
                        102: KeyCode.NUMPAD_6,
                        103: KeyCode.NUMPAD_7,
                        104: KeyCode.NUMPAD_8,
                        105: KeyCode.NUMPAD_9,
                        106: KeyCode.NUMPAD_MULTIPLY,
                        107: KeyCode.NUMPAD_ADD,
                        109: KeyCode.NUMPAD_SUBTRACT,
                        110: KeyCode.NUMPAD_DECIMAL,
                        111: KeyCode.NUMPAD_DIVIDE
                    }
                    if vk in numpad_map:
                        key_code = numpad_map[vk]
                        event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
                        return key_code, event_type
                
                # Try mapping from key_map
                mapped_key = self.key_map.get(self.keyboard.KeyCode.from_vk(vk))
                if mapped_key:
                    event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
                    return mapped_key, event_type
                
                # Map number virtual key codes (48-57 are 0-9)
                if 48 <= vk <= 57:
                    number_map = {
                        48: 'ZERO', 49: 'ONE', 50: 'TWO', 51: 'THREE', 52: 'FOUR',
                        53: 'FIVE', 54: 'SIX', 55: 'SEVEN', 56: 'EIGHT', 57: 'NINE'
                    }
                    try:
                        key_code = KeyCode[number_map[vk]]
                        event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
                        return key_code, event_type
                    except KeyError:
                        pass
        
        # Fall back to regular key mapping
        key_code = self.key_map.get(pynput_key)
        
        if key_code is None:
            return None
        
        event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
        return key_code, event_type

    def _create_key_map(self):
        """Create a mapping from evdev key codes to our internal KeyCode enum."""
        return {
            # Modifier keys
            self.evdev.ecodes.KEY_LEFTCTRL: KeyCode.CTRL_LEFT,
            self.evdev.ecodes.KEY_RIGHTCTRL: KeyCode.CTRL_RIGHT,
            self.evdev.ecodes.KEY_LEFTSHIFT: KeyCode.SHIFT_LEFT,
            self.evdev.ecodes.KEY_RIGHTSHIFT: KeyCode.SHIFT_RIGHT,
            self.evdev.ecodes.KEY_LEFTALT: KeyCode.ALT_LEFT,
            self.evdev.ecodes.KEY_RIGHTALT: KeyCode.ALT_RIGHT,
            self.evdev.ecodes.KEY_LEFTMETA: KeyCode.META_LEFT,
            self.evdev.ecodes.KEY_RIGHTMETA: KeyCode.META_RIGHT,

            # Function keys
            self.evdev.ecodes.KEY_F1: KeyCode.F1,
            self.evdev.ecodes.KEY_F2: KeyCode.F2,
            self.evdev.ecodes.KEY_F3: KeyCode.F3,
            self.evdev.ecodes.KEY_F4: KeyCode.F4,
            self.evdev.ecodes.KEY_F5: KeyCode.F5,
            self.evdev.ecodes.KEY_F6: KeyCode.F6,
            self.evdev.ecodes.KEY_F7: KeyCode.F7,
            self.evdev.ecodes.KEY_F8: KeyCode.F8,
            self.evdev.ecodes.KEY_F9: KeyCode.F9,
            self.evdev.ecodes.KEY_F10: KeyCode.F10,
            self.evdev.ecodes.KEY_F11: KeyCode.F11,
            self.evdev.ecodes.KEY_F12: KeyCode.F12,

            # Number keys
            self.evdev.ecodes.KEY_1: KeyCode.ONE,
            self.evdev.ecodes.KEY_2: KeyCode.TWO,
            self.evdev.ecodes.KEY_3: KeyCode.THREE,
            self.evdev.ecodes.KEY_4: KeyCode.FOUR,
            self.evdev.ecodes.KEY_5: KeyCode.FIVE,
            self.evdev.ecodes.KEY_6: KeyCode.SIX,
            self.evdev.ecodes.KEY_7: KeyCode.SEVEN,
            self.evdev.ecodes.KEY_8: KeyCode.EIGHT,
            self.evdev.ecodes.KEY_9: KeyCode.NINE,
            self.evdev.ecodes.KEY_0: KeyCode.ZERO,

            # Letter keys
            self.evdev.ecodes.KEY_A: KeyCode.A,
            self.evdev.ecodes.KEY_B: KeyCode.B,
            self.evdev.ecodes.KEY_C: KeyCode.C,
            self.evdev.ecodes.KEY_D: KeyCode.D,
            self.evdev.ecodes.KEY_E: KeyCode.E,
            self.evdev.ecodes.KEY_F: KeyCode.F,
            self.evdev.ecodes.KEY_G: KeyCode.G,
            self.evdev.ecodes.KEY_H: KeyCode.H,
            self.evdev.ecodes.KEY_I: KeyCode.I,
            self.evdev.ecodes.KEY_J: KeyCode.J,
            self.evdev.ecodes.KEY_K: KeyCode.K,
            self.evdev.ecodes.KEY_L: KeyCode.L,
            self.evdev.ecodes.KEY_M: KeyCode.M,
            self.evdev.ecodes.KEY_N: KeyCode.N,
            self.evdev.ecodes.KEY_O: KeyCode.O,
            self.evdev.ecodes.KEY_P: KeyCode.P,
            self.evdev.ecodes.KEY_Q: KeyCode.Q,
            self.evdev.ecodes.KEY_R: KeyCode.R,
            self.evdev.ecodes.KEY_S: KeyCode.S,
            self.evdev.ecodes.KEY_T: KeyCode.T,
            self.evdev.ecodes.KEY_U: KeyCode.U,
            self.evdev.ecodes.KEY_V: KeyCode.V,
            self.evdev.ecodes.KEY_W: KeyCode.W,
            self.evdev.ecodes.KEY_X: KeyCode.X,
            self.evdev.ecodes.KEY_Y: KeyCode.Y,
            self.evdev.ecodes.KEY_Z: KeyCode.Z,

            # Special keys
            self.evdev.ecodes.KEY_SPACE: KeyCode.SPACE,
            self.evdev.ecodes.KEY_ENTER: KeyCode.ENTER,
            self.evdev.ecodes.KEY_TAB: KeyCode.TAB,
            self.evdev.ecodes.KEY_BACKSPACE: KeyCode.BACKSPACE,
            self.evdev.ecodes.KEY_ESC: KeyCode.ESC,
            self.evdev.ecodes.KEY_INSERT: KeyCode.INSERT,
            self.evdev.ecodes.KEY_DELETE: KeyCode.DELETE,
            self.evdev.ecodes.KEY_HOME: KeyCode.HOME,
            self.evdev.ecodes.KEY_END: KeyCode.END,
            self.evdev.ecodes.KEY_PAGEUP: KeyCode.PAGE_UP,
            self.evdev.ecodes.KEY_PAGEDOWN: KeyCode.PAGE_DOWN,
            self.evdev.ecodes.KEY_CAPSLOCK: KeyCode.CAPS_LOCK,
            self.evdev.ecodes.KEY_NUMLOCK: KeyCode.NUM_LOCK,
            self.evdev.ecodes.KEY_SCROLLLOCK: KeyCode.SCROLL_LOCK,
            self.evdev.ecodes.KEY_PAUSE: KeyCode.PAUSE,
            self.evdev.ecodes.KEY_SYSRQ: KeyCode.PRINT_SCREEN,

            # Arrow keys
            self.evdev.ecodes.KEY_UP: KeyCode.UP,
            self.evdev.ecodes.KEY_DOWN: KeyCode.DOWN,
            self.evdev.ecodes.KEY_LEFT: KeyCode.LEFT,
            self.evdev.ecodes.KEY_RIGHT: KeyCode.RIGHT,

            # Numpad keys
            self.evdev.ecodes.KEY_KP0: KeyCode.NUMPAD_0,
            self.evdev.ecodes.KEY_KP1: KeyCode.NUMPAD_1,
            self.evdev.ecodes.KEY_KP2: KeyCode.NUMPAD_2,
            self.evdev.ecodes.KEY_KP3: KeyCode.NUMPAD_3,
            self.evdev.ecodes.KEY_KP4: KeyCode.NUMPAD_4,
            self.evdev.ecodes.KEY_KP5: KeyCode.NUMPAD_5,
            self.evdev.ecodes.KEY_KP6: KeyCode.NUMPAD_6,
            self.evdev.ecodes.KEY_KP7: KeyCode.NUMPAD_7,
            self.evdev.ecodes.KEY_KP8: KeyCode.NUMPAD_8,
            self.evdev.ecodes.KEY_KP9: KeyCode.NUMPAD_9,
            self.evdev.ecodes.KEY_KPPLUS: KeyCode.NUMPAD_ADD,
            self.evdev.ecodes.KEY_KPMINUS: KeyCode.NUMPAD_SUBTRACT,
            self.evdev.ecodes.KEY_KPASTERISK: KeyCode.NUMPAD_MULTIPLY,
            self.evdev.ecodes.KEY_KPSLASH: KeyCode.NUMPAD_DIVIDE,
            self.evdev.ecodes.KEY_KPDOT: KeyCode.NUMPAD_DECIMAL,
            self.evdev.ecodes.KEY_KPENTER: KeyCode.NUMPAD_ENTER,

            # Additional special characters
            self.evdev.ecodes.KEY_MINUS: KeyCode.MINUS,
            self.evdev.ecodes.KEY_EQUAL: KeyCode.EQUALS,
            self.evdev.ecodes.KEY_LEFTBRACE: KeyCode.LEFT_BRACKET,
            self.evdev.ecodes.KEY_RIGHTBRACE: KeyCode.RIGHT_BRACKET,
            self.evdev.ecodes.KEY_SEMICOLON: KeyCode.SEMICOLON,
            self.evdev.ecodes.KEY_APOSTROPHE: KeyCode.QUOTE,
            self.evdev.ecodes.KEY_GRAVE: KeyCode.BACKQUOTE,
            self.evdev.ecodes.KEY_BACKSLASH: KeyCode.BACKSLASH,
            self.evdev.ecodes.KEY_COMMA: KeyCode.COMMA,
            self.evdev.ecodes.KEY_DOT: KeyCode.PERIOD,
            self.evdev.ecodes.KEY_SLASH: KeyCode.SLASH,

            # Media keys
            self.evdev.ecodes.KEY_MUTE: KeyCode.MUTE,
            self.evdev.ecodes.KEY_VOLUMEDOWN: KeyCode.VOLUME_DOWN,
            self.evdev.ecodes.KEY_VOLUMEUP: KeyCode.VOLUME_UP,
            self.evdev.ecodes.KEY_PLAYPAUSE: KeyCode.PLAY_PAUSE,
            self.evdev.ecodes.KEY_NEXTSONG: KeyCode.NEXT_TRACK,
            self.evdev.ecodes.KEY_PREVIOUSSONG: KeyCode.PREV_TRACK,

            # Additional function keys (if needed)
            self.evdev.ecodes.KEY_F13: KeyCode.F13,
            self.evdev.ecodes.KEY_F14: KeyCode.F14,
            self.evdev.ecodes.KEY_F15: KeyCode.F15,
            self.evdev.ecodes.KEY_F16: KeyCode.F16,
            self.evdev.ecodes.KEY_F17: KeyCode.F17,
            self.evdev.ecodes.KEY_F18: KeyCode.F18,
            self.evdev.ecodes.KEY_F19: KeyCode.F19,
            self.evdev.ecodes.KEY_F20: KeyCode.F20,
            self.evdev.ecodes.KEY_F21: KeyCode.F21,
            self.evdev.ecodes.KEY_F22: KeyCode.F22,
            self.evdev.ecodes.KEY_F23: KeyCode.F23,
            self.evdev.ecodes.KEY_F24: KeyCode.F24,

            # Additional Media and Special Function Keys
            self.evdev.ecodes.KEY_PLAYPAUSE: KeyCode.MEDIA_PLAY_PAUSE,
            self.evdev.ecodes.KEY_STOP: KeyCode.MEDIA_STOP,
            self.evdev.ecodes.KEY_PREVIOUSSONG: KeyCode.MEDIA_PREVIOUS,
            self.evdev.ecodes.KEY_NEXTSONG: KeyCode.MEDIA_NEXT,
            self.evdev.ecodes.KEY_REWIND: KeyCode.MEDIA_REWIND,
            self.evdev.ecodes.KEY_FASTFORWARD: KeyCode.MEDIA_FAST_FORWARD,
            self.evdev.ecodes.KEY_MUTE: KeyCode.AUDIO_MUTE,
            self.evdev.ecodes.KEY_VOLUMEUP: KeyCode.AUDIO_VOLUME_UP,
            self.evdev.ecodes.KEY_VOLUMEDOWN: KeyCode.AUDIO_VOLUME_DOWN,
            self.evdev.ecodes.KEY_MEDIA: KeyCode.MEDIA_SELECT,
            self.evdev.ecodes.KEY_WWW: KeyCode.WWW,
            self.evdev.ecodes.KEY_MAIL: KeyCode.MAIL,
            self.evdev.ecodes.KEY_CALC: KeyCode.CALCULATOR,
            self.evdev.ecodes.KEY_COMPUTER: KeyCode.COMPUTER,
            self.evdev.ecodes.KEY_SEARCH: KeyCode.APP_SEARCH,
            self.evdev.ecodes.KEY_HOMEPAGE: KeyCode.APP_HOME,
            self.evdev.ecodes.KEY_BACK: KeyCode.APP_BACK,
            self.evdev.ecodes.KEY_FORWARD: KeyCode.APP_FORWARD,
            self.evdev.ecodes.KEY_STOP: KeyCode.APP_STOP,
            self.evdev.ecodes.KEY_REFRESH: KeyCode.APP_REFRESH,
            self.evdev.ecodes.KEY_BOOKMARKS: KeyCode.APP_BOOKMARKS,
            self.evdev.ecodes.KEY_BRIGHTNESSDOWN: KeyCode.BRIGHTNESS_DOWN,
            self.evdev.ecodes.KEY_BRIGHTNESSUP: KeyCode.BRIGHTNESS_UP,
            self.evdev.ecodes.KEY_DISPLAYTOGGLE: KeyCode.DISPLAY_SWITCH,
            self.evdev.ecodes.KEY_KBDILLUMTOGGLE: KeyCode.KEYBOARD_ILLUMINATION_TOGGLE,
            self.evdev.ecodes.KEY_KBDILLUMDOWN: KeyCode.KEYBOARD_ILLUMINATION_DOWN,
            self.evdev.ecodes.KEY_KBDILLUMUP: KeyCode.KEYBOARD_ILLUMINATION_UP,
            self.evdev.ecodes.KEY_EJECTCD: KeyCode.EJECT,
            self.evdev.ecodes.KEY_SLEEP: KeyCode.SLEEP,
            self.evdev.ecodes.KEY_WAKEUP: KeyCode.WAKE,
            self.evdev.ecodes.KEY_COMPOSE: KeyCode.EMOJI,
            self.evdev.ecodes.KEY_MENU: KeyCode.MENU,
            self.evdev.ecodes.KEY_CLEAR: KeyCode.CLEAR,
            self.evdev.ecodes.KEY_SCREENLOCK: KeyCode.LOCK,

            # Mouse Buttons
            self.evdev.ecodes.BTN_LEFT: KeyCode.MOUSE_LEFT,
            self.evdev.ecodes.BTN_RIGHT: KeyCode.MOUSE_RIGHT,
            self.evdev.ecodes.BTN_MIDDLE: KeyCode.MOUSE_MIDDLE,
            self.evdev.ecodes.BTN_SIDE: KeyCode.MOUSE_BACK,
            self.evdev.ecodes.BTN_EXTRA: KeyCode.MOUSE_FORWARD,
            self.evdev.ecodes.BTN_FORWARD: KeyCode.MOUSE_SIDE1,
            self.evdev.ecodes.BTN_BACK: KeyCode.MOUSE_SIDE2,
            self.evdev.ecodes.BTN_TASK: KeyCode.MOUSE_SIDE3,
        }

    def on_input_event(self, event):
        """
        Callback method to be overridden by the KeyListener.
        This method is called for each processed input event.
        """
        pass

class PynputBackend(InputBackend):
    """
    Input backend implementation using the pynput library.
    """

    @classmethod
    def is_available(cls) -> bool:
        """Check if pynput library is available."""
        try:
            import pynput
            return True
        except ImportError:
            return False

    def __init__(self):
        """Initialize PynputBackend."""
        self.keyboard_listener = None
        self.mouse_listener = None
        self.keyboard = None
        self.mouse = None
        self.key_map = None

    def start(self):
        """Start listening for keyboard and mouse events."""
        if self.keyboard is None or self.mouse is None:
            from pynput import keyboard, mouse
            self.keyboard = keyboard
            self.mouse = mouse
            self.key_map = self._create_key_map()

        self.keyboard_listener = self.keyboard.Listener(
            on_press=self._on_keyboard_press,
            on_release=self._on_keyboard_release
        )
        self.mouse_listener = self.mouse.Listener(
            on_click=self._on_mouse_click
        )
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop(self):
        """Stop listening for keyboard and mouse events."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

    def _translate_key_event(self, native_event) -> Optional[tuple[KeyCode, InputEvent]]:
        """Translate a pynput event to our internal event representation."""
        # For evdev backend
        if hasattr(native_event, 'keystate'):
            key_event = native_event
            if key_event.keystate in [key_event.key_down, key_event.key_hold]:
                event_type = InputEvent.KEY_PRESS
            elif key_event.keystate == key_event.key_up:
                event_type = InputEvent.KEY_RELEASE
            else:
                return None
            
            key_code = self.key_map.get(key_event.scancode)
            if key_code is None:
                return None
            
            return key_code, event_type

        # For pynput backend
        pynput_key, is_press = native_event
        
        # Handle character keys
        if isinstance(pynput_key, self.keyboard.KeyCode):
            # Try to map from virtual key code first
            if hasattr(pynput_key, 'vk') and pynput_key.vk is not None:
                vk = pynput_key.vk
                
                # Map numpad virtual key codes (96-111)
                if 96 <= vk <= 111:
                    numpad_map = {
                        96: KeyCode.NUMPAD_0,
                        97: KeyCode.NUMPAD_1,
                        98: KeyCode.NUMPAD_2,
                        99: KeyCode.NUMPAD_3,
                        100: KeyCode.NUMPAD_4,
                        101: KeyCode.NUMPAD_5,
                        102: KeyCode.NUMPAD_6,
                        103: KeyCode.NUMPAD_7,
                        104: KeyCode.NUMPAD_8,
                        105: KeyCode.NUMPAD_9,
                        106: KeyCode.NUMPAD_MULTIPLY,
                        107: KeyCode.NUMPAD_ADD,
                        109: KeyCode.NUMPAD_SUBTRACT,
                        110: KeyCode.NUMPAD_DECIMAL,
                        111: KeyCode.NUMPAD_DIVIDE
                    }
                    if vk in numpad_map:
                        key_code = numpad_map[vk]
                        event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
                        return key_code, event_type
                
                # Try mapping from key_map
                mapped_key = self.key_map.get(self.keyboard.KeyCode.from_vk(vk))
                if mapped_key:
                    event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
                    return mapped_key, event_type
                
                # Map number virtual key codes (48-57 are 0-9)
                if 48 <= vk <= 57:
                    number_map = {
                        48: 'ZERO', 49: 'ONE', 50: 'TWO', 51: 'THREE', 52: 'FOUR',
                        53: 'FIVE', 54: 'SIX', 55: 'SEVEN', 56: 'EIGHT', 57: 'NINE'
                    }
                    try:
                        key_code = KeyCode[number_map[vk]]
                        event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
                        return key_code, event_type
                    except KeyError:
                        pass
        
        # Fall back to regular key mapping
        key_code = self.key_map.get(pynput_key)
        
        if key_code is None:
            return None
        
        event_type = InputEvent.KEY_PRESS if is_press else InputEvent.KEY_RELEASE
        return key_code, event_type

    def _on_keyboard_press(self, key):
        """Handle keyboard press events."""
        translated_event = self._translate_key_event((key, True))
        if translated_event:
            # Only log if this key wasn't already pressed
            if not hasattr(self, '_pressed_keys'):
                self._pressed_keys = set()
            if translated_event[0] not in self._pressed_keys:
                # print(f"Press event: {translated_event}")
                self._pressed_keys.add(translated_event[0])
            self.on_input_event(translated_event)

    def _on_keyboard_release(self, key):
        """Handle keyboard release events."""
        translated_event = self._translate_key_event((key, False))
        if translated_event:
            if not hasattr(self, '_pressed_keys'):
                self._pressed_keys = set()
            if translated_event[0] in self._pressed_keys:
                # print(f"Release event: {translated_event}")
                self._pressed_keys.discard(translated_event[0])
            self.on_input_event(translated_event)

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        translated_event = self._translate_key_event((button, pressed))
        if translated_event:
            self.on_input_event(translated_event)

    def _create_key_map(self):
        """Create a mapping from pynput keys to our internal KeyCode enum."""
        key_map = {
            # Modifier keys
            self.keyboard.Key.ctrl_l: KeyCode.CTRL_LEFT,
            self.keyboard.Key.ctrl_r: KeyCode.CTRL_RIGHT,
            self.keyboard.Key.shift_l: KeyCode.SHIFT_LEFT,
            self.keyboard.Key.shift_r: KeyCode.SHIFT_RIGHT,
            self.keyboard.Key.alt_l: KeyCode.ALT_LEFT,
            self.keyboard.Key.alt_r: KeyCode.ALT_RIGHT,
            self.keyboard.Key.alt_gr: KeyCode.ALT_RIGHT,
            self.keyboard.Key.cmd_l: KeyCode.META_LEFT,
            self.keyboard.Key.cmd_r: KeyCode.META_RIGHT,

            # Function keys
            self.keyboard.Key.f1: KeyCode.F1,
            self.keyboard.Key.f2: KeyCode.F2,
            self.keyboard.Key.f3: KeyCode.F3,
            self.keyboard.Key.f4: KeyCode.F4,
            self.keyboard.Key.f5: KeyCode.F5,
            self.keyboard.Key.f6: KeyCode.F6,
            self.keyboard.Key.f7: KeyCode.F7,
            self.keyboard.Key.f8: KeyCode.F8,
            self.keyboard.Key.f9: KeyCode.F9,
            self.keyboard.Key.f10: KeyCode.F10,
            self.keyboard.Key.f11: KeyCode.F11,
            self.keyboard.Key.f12: KeyCode.F12,
            self.keyboard.Key.f13: KeyCode.F13,
            self.keyboard.Key.f14: KeyCode.F14,
            self.keyboard.Key.f15: KeyCode.F15,
            self.keyboard.Key.f16: KeyCode.F16,
            self.keyboard.Key.f17: KeyCode.F17,
            self.keyboard.Key.f18: KeyCode.F18,
            self.keyboard.Key.f19: KeyCode.F19,
            self.keyboard.Key.f20: KeyCode.F20,

            # Number keys
            self.keyboard.KeyCode.from_char('1'): KeyCode.ONE,
            self.keyboard.KeyCode.from_char('2'): KeyCode.TWO,
            self.keyboard.KeyCode.from_char('3'): KeyCode.THREE,
            self.keyboard.KeyCode.from_char('4'): KeyCode.FOUR,
            self.keyboard.KeyCode.from_char('5'): KeyCode.FIVE,
            self.keyboard.KeyCode.from_char('6'): KeyCode.SIX,
            self.keyboard.KeyCode.from_char('7'): KeyCode.SEVEN,
            self.keyboard.KeyCode.from_char('8'): KeyCode.EIGHT,
            self.keyboard.KeyCode.from_char('9'): KeyCode.NINE,
            self.keyboard.KeyCode.from_char('0'): KeyCode.ZERO,

            # Letter keys
            self.keyboard.KeyCode.from_char('a'): KeyCode.A,
            self.keyboard.KeyCode.from_char('b'): KeyCode.B,
            self.keyboard.KeyCode.from_char('c'): KeyCode.C,
            self.keyboard.KeyCode.from_char('d'): KeyCode.D,
            self.keyboard.KeyCode.from_char('e'): KeyCode.E,
            self.keyboard.KeyCode.from_char('f'): KeyCode.F,
            self.keyboard.KeyCode.from_char('g'): KeyCode.G,
            self.keyboard.KeyCode.from_char('h'): KeyCode.H,
            self.keyboard.KeyCode.from_char('i'): KeyCode.I,
            self.keyboard.KeyCode.from_char('j'): KeyCode.J,
            self.keyboard.KeyCode.from_char('k'): KeyCode.K,
            self.keyboard.KeyCode.from_char('l'): KeyCode.L,
            self.keyboard.KeyCode.from_char('m'): KeyCode.M,
            self.keyboard.KeyCode.from_char('n'): KeyCode.N,
            self.keyboard.KeyCode.from_char('o'): KeyCode.O,
            self.keyboard.KeyCode.from_char('p'): KeyCode.P,
            self.keyboard.KeyCode.from_char('q'): KeyCode.Q,
            self.keyboard.KeyCode.from_char('r'): KeyCode.R,
            self.keyboard.KeyCode.from_char('s'): KeyCode.S,
            self.keyboard.KeyCode.from_char('t'): KeyCode.T,
            self.keyboard.KeyCode.from_char('u'): KeyCode.U,
            self.keyboard.KeyCode.from_char('v'): KeyCode.V,
            self.keyboard.KeyCode.from_char('w'): KeyCode.W,
            self.keyboard.KeyCode.from_char('x'): KeyCode.X,
            self.keyboard.KeyCode.from_char('y'): KeyCode.Y,
            self.keyboard.KeyCode.from_char('z'): KeyCode.Z,

            # Special keys
            self.keyboard.Key.space: KeyCode.SPACE,
            self.keyboard.Key.enter: KeyCode.ENTER,
            self.keyboard.Key.tab: KeyCode.TAB,
            self.keyboard.Key.backspace: KeyCode.BACKSPACE,
            self.keyboard.Key.esc: KeyCode.ESC,
            self.keyboard.Key.insert: KeyCode.INSERT,
            self.keyboard.Key.delete: KeyCode.DELETE,
            self.keyboard.Key.home: KeyCode.HOME,
            self.keyboard.Key.end: KeyCode.END,
            self.keyboard.Key.page_up: KeyCode.PAGE_UP,
            self.keyboard.Key.page_down: KeyCode.PAGE_DOWN,
            self.keyboard.Key.caps_lock: KeyCode.CAPS_LOCK,
            self.keyboard.Key.num_lock: KeyCode.NUM_LOCK,
            self.keyboard.Key.scroll_lock: KeyCode.SCROLL_LOCK,
            self.keyboard.Key.pause: KeyCode.PAUSE,
            self.keyboard.Key.print_screen: KeyCode.PRINT_SCREEN,

            # Arrow keys
            self.keyboard.Key.up: KeyCode.UP,
            self.keyboard.Key.down: KeyCode.DOWN,
            self.keyboard.Key.left: KeyCode.LEFT,
            self.keyboard.Key.right: KeyCode.RIGHT,

            # Numpad keys
            self.keyboard.Key.num_lock: KeyCode.NUM_LOCK,
            self.keyboard.KeyCode.from_vk(96): KeyCode.NUMPAD_0,
            self.keyboard.KeyCode.from_vk(97): KeyCode.NUMPAD_1,
            self.keyboard.KeyCode.from_vk(98): KeyCode.NUMPAD_2,
            self.keyboard.KeyCode.from_vk(99): KeyCode.NUMPAD_3,
            self.keyboard.KeyCode.from_vk(100): KeyCode.NUMPAD_4,
            self.keyboard.KeyCode.from_vk(101): KeyCode.NUMPAD_5,
            self.keyboard.KeyCode.from_vk(102): KeyCode.NUMPAD_6,
            self.keyboard.KeyCode.from_vk(103): KeyCode.NUMPAD_7,
            self.keyboard.KeyCode.from_vk(104): KeyCode.NUMPAD_8,
            self.keyboard.KeyCode.from_vk(105): KeyCode.NUMPAD_9,
            self.keyboard.KeyCode.from_vk(106): KeyCode.NUMPAD_MULTIPLY,
            self.keyboard.KeyCode.from_vk(107): KeyCode.NUMPAD_ADD,
            self.keyboard.KeyCode.from_vk(109): KeyCode.NUMPAD_SUBTRACT,
            self.keyboard.KeyCode.from_vk(110): KeyCode.NUMPAD_DECIMAL,
            self.keyboard.KeyCode.from_vk(111): KeyCode.NUMPAD_DIVIDE,

            # Additional special characters
            self.keyboard.KeyCode.from_char('-'): KeyCode.MINUS,
            self.keyboard.KeyCode.from_char('='): KeyCode.EQUALS,
            self.keyboard.KeyCode.from_char('['): KeyCode.LEFT_BRACKET,
            self.keyboard.KeyCode.from_char(']'): KeyCode.RIGHT_BRACKET,
            self.keyboard.KeyCode.from_char(';'): KeyCode.SEMICOLON,
            self.keyboard.KeyCode.from_char("'"): KeyCode.QUOTE,
            self.keyboard.KeyCode.from_char('`'): KeyCode.BACKQUOTE,
            self.keyboard.KeyCode.from_char('\\'): KeyCode.BACKSLASH,
            self.keyboard.KeyCode.from_char(','): KeyCode.COMMA,
            self.keyboard.KeyCode.from_char('.'): KeyCode.PERIOD,
            self.keyboard.KeyCode.from_char('/'): KeyCode.SLASH,

            # Media keys
            self.keyboard.Key.media_volume_mute: KeyCode.AUDIO_MUTE,
            self.keyboard.Key.media_volume_down: KeyCode.AUDIO_VOLUME_DOWN,
            self.keyboard.Key.media_volume_up: KeyCode.AUDIO_VOLUME_UP,
            self.keyboard.Key.media_play_pause: KeyCode.MEDIA_PLAY_PAUSE,
            self.keyboard.Key.media_next: KeyCode.MEDIA_NEXT,
            self.keyboard.Key.media_previous: KeyCode.MEDIA_PREVIOUS,

            # Mouse buttons
            self.mouse.Button.left: KeyCode.MOUSE_LEFT,
            self.mouse.Button.right: KeyCode.MOUSE_RIGHT,
            self.mouse.Button.middle: KeyCode.MOUSE_MIDDLE,
        }
        
        # Add uppercase letter mappings
        key_map.update({
            self.keyboard.KeyCode.from_char(c.upper()): getattr(KeyCode, c.upper())
            for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        })
        
        # Add existing lowercase mappings
        key_map.update({
            self.keyboard.KeyCode.from_char(c.lower()): getattr(KeyCode, c)
            for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        })
        
        return key_map

    def on_input_event(self, event):
        """
        Callback method to be set by the KeyListener.
        This method is called for each processed input event.
        """
        pass