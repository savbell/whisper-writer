from typing import Optional, List

from input_backend.input_backend_base import InputBackendBase
from enums import KeyCode, InputEvent


class EvdevBackend(InputBackendBase):
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
        import evdev
        import threading
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
        if isinstance(error, OSError) and (error.errno == errno.EBADF or
                                           error.errno == errno.ENODEV):
            print(f"Device {device.path} is no longer available. Removing it.")
            self.devices.remove(device)
        else:
            print(f"Unexpected error reading device: {error}")

    def _handle_input_event(self, event):
        """Process a single input event."""
        key_code, event_type = self._translate_key_event(event)
        if key_code is not None and event_type is not None:
            self.on_input_event((key_code, event_type))

    def _translate_key_event(self, event) -> tuple[KeyCode | None, InputEvent | None]:
        """Translate an evdev event to our internal representation."""
        key_event = self.evdev.categorize(event)
        if not isinstance(key_event, self.evdev.events.KeyEvent):
            return None, None

        key_code = self.key_map.get(key_event.scancode)
        if key_code is None:
            return None, None

        if key_event.keystate in [key_event.key_down, key_event.key_hold]:
            event_type = InputEvent.KEY_PRESS
        elif key_event.keystate == key_event.key_up:
            event_type = InputEvent.KEY_RELEASE
        else:
            return None, None

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
        Callback method to be overridden by the InputManager.
        This method is called for each processed input event.
        """
        pass
