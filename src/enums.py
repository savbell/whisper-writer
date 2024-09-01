from enum import Enum, auto


class RecordingMode(Enum):
    CONTINUOUS = 1
    VOICE_ACTIVITY_DETECTION = 2
    PRESS_TO_TOGGLE = 3
    HOLD_TO_RECORD = 4


class ProfileState(Enum):
    IDLE = 0
    RECORDING = 1
    TRANSCRIBING = 2
    STREAMING = 3


class TranscribingState(Enum):
    IDLE = 0
    PROCESSING = 1
    STREAMING = 2
    DRAINING = 3


class AudioManagerState(Enum):
    STOPPED = 0
    IDLE = 1
    RECORDING = 2


class InputEvent(Enum):
    KEY_PRESS = auto()
    KEY_RELEASE = auto()
    MOUSE_PRESS = auto()
    MOUSE_RELEASE = auto()


class KeyCode(Enum):
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
    NUMPAD_0 = auto()
    NUMPAD_1 = auto()
    NUMPAD_2 = auto()
    NUMPAD_3 = auto()
    NUMPAD_4 = auto()
    NUMPAD_5 = auto()
    NUMPAD_6 = auto()
    NUMPAD_7 = auto()
    NUMPAD_8 = auto()
    NUMPAD_9 = auto()
    NUMPAD_ADD = auto()
    NUMPAD_SUBTRACT = auto()
    NUMPAD_MULTIPLY = auto()
    NUMPAD_DIVIDE = auto()
    NUMPAD_DECIMAL = auto()
    NUMPAD_ENTER = auto()

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
