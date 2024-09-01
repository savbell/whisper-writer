import subprocess
import os
import signal
import time
import fcntl
import struct
from pynput.keyboard import Key, Controller as PynputController

from config_manager import ConfigManager
from event_bus import EventBus


class OutputManager:
    """A class to simulate keyboard output using various methods."""
    def __init__(self, profile_name: str, event_bus: EventBus):
        """Initialize the OutputManager with the specified configuration."""
        self.config = ConfigManager.get_section('post_processing', profile_name)
        self.output_method = self.config.get('keyboard_simulator')
        self.dotool_process = None
        self.uinput_backend = None

        if self.output_method == 'pynput':
            self.keyboard = PynputController()
        elif self.output_method == 'dotool':
            self._initialize_dotool()
        elif self.output_method == 'uinput':
            self.uinput_backend = UinputBackend(self.config)

    def typewrite(self, text):
        """Simulate typing the given text with the specified interval between keystrokes."""
        interval = self.config.get('writing_key_press_delay')
        if self.output_method == 'pynput':
            self._typewrite_pynput(text, interval)
        elif self.output_method == 'ydotool':
            self._typewrite_ydotool(text, interval)
        elif self.output_method == 'dotool':
            self._typewrite_dotool(text, interval)
        elif self.output_method == 'uinput':
            self.uinput_backend.typewrite(text, interval)

    def backspace(self, count: int):
        """Simulate pressing the backspace key 'count' times."""
        if self.output_method == 'pynput':
            self._backspace_pynput(count)
        elif self.output_method == 'ydotool':
            self._backspace_ydotool(count)
        elif self.output_method == 'dotool':
            self._backspace_dotool(count)
        elif self.output_method == 'uinput':
            self.uinput_backend.backspace(count)

    def _typewrite_pynput(self, text, interval):
        """Simulate typing using pynput."""
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)

    def _backspace_pynput(self, count):
        """Simulate backspace using pynput."""
        for _ in range(count):
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)
            time.sleep(0.05)

    def _typewrite_ydotool(self, text, interval):
        """Simulate typing using ydotool."""
        cmd = "ydotool"
        command = [
            cmd,
            "type",
            "--key-delay",
            str(interval * 1000),
            "--",
            text,
        ]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")

    def _backspace_ydotool(self, count):
        """Simulate backspace using ydotool."""
        cmd = "ydotool"
        backspace_commands = ["key"] + ["14:1", "14:0"] * count
        command = [cmd] + backspace_commands

        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")

    def _initialize_dotool(self):
        """Initialize the dotool process for output simulation."""
        self.dotool_process = subprocess.Popen("dotool", stdin=subprocess.PIPE, text=True)
        assert self.dotool_process.stdin is not None

    def _terminate_dotool(self):
        """Terminate the dotool process if it's running."""
        if self.dotool_process:
            os.kill(self.dotool_process.pid, signal.SIGINT)
            self.dotool_process = None

    def _typewrite_dotool(self, text, interval):
        """Simulate typing using dotool."""
        assert self.dotool_process and self.dotool_process.stdin
        self.dotool_process.stdin.write(f"typedelay {interval * 1000}\n")
        self.dotool_process.stdin.write(f"type {text}\n")
        self.dotool_process.stdin.flush()

    def _backspace_dotool(self, count):
        """Simulate backspace using dotool."""
        assert self.dotool_process and self.dotool_process.stdin
        backspace_commands = "k:14 " * count
        self.dotool_process.stdin.write(f"key {backspace_commands}\n")
        self.dotool_process.stdin.flush()

    def cleanup(self):
        """Perform cleanup operations, such as terminating the dotool process."""
        if self.output_method == 'dotool':
            self._terminate_dotool()
        elif self.output_method == 'uinput':
            if self.uinput_backend:
                self.uinput_backend.cleanup()


class UinputBackend:
    # Constants
    UINPUT_MAX_NAME_SIZE = 80
    ABS_MAX = 0x3f
    ABS_CNT = ABS_MAX + 1

    UI_DEV_CREATE = 0x5501
    UI_DEV_DESTROY = 0x5502
    UI_SET_EVBIT = 0x40045564
    UI_SET_KEYBIT = 0x40045565

    EV_SYN = 0x00
    EV_KEY = 0x01
    SYN_REPORT = 0

    KEY_CODES = {
        'a': 30, 'b': 48, 'c': 46, 'd': 32, 'e': 18, 'f': 33, 'g': 34, 'h': 35, 'i': 23,
        'j': 36, 'k': 37, 'l': 38, 'm': 50, 'n': 49, 'o': 24, 'p': 25, 'q': 16, 'r': 19,
        's': 31, 't': 20, 'u': 22, 'v': 47, 'w': 17, 'x': 45, 'y': 21, 'z': 44,
        '0': 11, '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10,
        ' ': 57, ',': 51, '.': 52, '-': 12, '=': 13, ';': 39, "'": 40, '\\': 43, '/': 53,
        '[': 26, ']': 27, '`': 41, '?': 53, '!': 2, '@': 3, '#': 4, '$': 5, '%': 6, '^': 7,
        '&': 8, '*': 9, '(': 10, ')': 11, '_': 12, '+': 13, '{': 26, '}': 27, '|': 43,
        ':': 39, '"': 40, '<': 51, '>': 52, '~': 41,
        'KEY_LEFTSHIFT': 42, 'KEY_RIGHTSHIFT': 54,
        'KEY_LEFTCTRL': 29, 'KEY_RIGHTCTRL': 97,
        'KEY_LEFTALT': 56, 'KEY_RIGHTALT': 100,
        'KEY_LEFTMETA': 125, 'KEY_RIGHTMETA': 126,
        'KEY_BACKSPACE': 14
    }

    SHIFT_CHARS = '~!@#$%^&*()_+{}|:"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self, config):
        self.config = config
        self.uinput_fd = None
        self.device_name = 'WhisperWriter Virtual Keyboard'.encode()
        self.initialize_device()

    def initialize_device(self):
        self.uinput_fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)

        # Enable key and synchronization events
        fcntl.ioctl(self.uinput_fd, self.UI_SET_EVBIT, self.EV_KEY)
        fcntl.ioctl(self.uinput_fd, self.UI_SET_EVBIT, self.EV_SYN)

        # Enable all key codes
        for i in range(256):
            fcntl.ioctl(self.uinput_fd, self.UI_SET_KEYBIT, i)

        # Create the device
        device_struct = struct.pack('80sHHHHi' + 'i' * (self.ABS_CNT * 4),
                                    self.device_name,
                                    0x03,  # BUS_USB
                                    0x1234,  # Vendor ID
                                    0x5678,  # Product ID
                                    0,  # Version
                                    0,  # FF effects
                                    *(0 for _ in range(self.ABS_CNT * 4)))  # Absolute axes info

        os.write(self.uinput_fd, device_struct)
        fcntl.ioctl(self.uinput_fd, self.UI_DEV_CREATE)

        # Give the system some time to create the device
        time.sleep(0.1)

    def _emit(self, type, code, value):
        t = time.time()
        sec = int(t)
        usec = int((t - sec) * 1000000)
        event = struct.pack('llHHI', sec, usec, type, code, value)
        os.write(self.uinput_fd, event)

    def _syn(self):
        self._emit(self.EV_SYN, self.SYN_REPORT, 0)

    def _press_key(self, key_code):
        self._emit(self.EV_KEY, key_code, 1)
        self._syn()

    def _release_key(self, key_code):
        self._emit(self.EV_KEY, key_code, 0)
        self._syn()

    def _type_char(self, char, interval):
        shift_needed = char in self.SHIFT_CHARS
        if char.isupper():
            key_code = self.KEY_CODES.get(char.lower())
        else:
            key_code = self.KEY_CODES.get(char)

        if key_code is None:
            print(f"Character '{char}' not supported")
            return

        if shift_needed:
            self._press_key(self.KEY_CODES['KEY_LEFTSHIFT'])

        self._press_key(key_code)
        time.sleep(interval)  # Interval must be here to properly register shifted characters
        self._release_key(key_code)

        if shift_needed:
            self._release_key(self.KEY_CODES['KEY_LEFTSHIFT'])

    def typewrite(self, text, interval):
        for char in text:
            self._type_char(char, interval)

    def backspace(self, count: int):
        backspace_code = self.KEY_CODES['KEY_BACKSPACE']
        for _ in range(count):
            self._press_key(backspace_code)
            time.sleep(0.005)  # Small delay between backspaces
            self._release_key(backspace_code)

    def cleanup(self):
        if self.uinput_fd:
            fcntl.ioctl(self.uinput_fd, self.UI_DEV_DESTROY)
            os.close(self.uinput_fd)
