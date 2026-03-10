import subprocess
import os
import signal
import time
from pynput.keyboard import Controller as PynputController

from utils import ConfigManager

def run_command_or_exit_on_failure(command):
    """
    Run a shell command and exit if it fails.

    Args:
        command (list): The command to run as a list of strings.
    """
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)

class InputSimulator:
    """
    A class to simulate keyboard input using various methods.
    """

    def __init__(self):
        """
        Initialize the InputSimulator with the specified configuration.
        """
        self.input_method = ConfigManager.get_config_value('post_processing', 'input_method')
        self.dotool_process = None

        if self.input_method == 'pynput':
            self.keyboard = PynputController()
        elif self.input_method == 'clipboard':
            self._win32_api_configured = False
        elif self.input_method == 'dotool':
            self._initialize_dotool()

    def _initialize_dotool(self):
        """
        Initialize the dotool process for input simulation.
        """
        self.dotool_process = subprocess.Popen("dotool", stdin=subprocess.PIPE, text=True)
        assert self.dotool_process.stdin is not None

    def _terminate_dotool(self):
        """
        Terminate the dotool process if it's running.
        """
        if self.dotool_process:
            os.kill(self.dotool_process.pid, signal.SIGINT)
            self.dotool_process = None

    def typewrite(self, text):
        """
        Simulate typing the given text with the specified interval between keystrokes.

        Args:
            text (str): The text to type.
        """
        interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
        if self.input_method == 'clipboard':
            self._typewrite_clipboard(text)
        elif self.input_method == 'pynput':
            self._typewrite_pynput(text, interval)
        elif self.input_method == 'ydotool':
            self._typewrite_ydotool(text, interval)
        elif self.input_method == 'dotool':
            self._typewrite_dotool(text, interval)

    def _ensure_win32_api(self):
        """Configure ctypes function signatures for Win32 clipboard API (once)."""
        if self._win32_api_configured:
            return
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
        user32.GetClipboardData.restype = ctypes.c_void_p
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        user32.SetClipboardData.restype = ctypes.c_void_p
        self._win32_api_configured = True

    def _win32_set_clipboard(self, text):
        """Set clipboard content using Windows API."""
        import ctypes
        self._ensure_win32_api()
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        encoded = text.encode('utf-16-le') + b'\x00\x00'
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not h:
            return
        ptr = kernel32.GlobalLock(h)
        if not ptr:
            kernel32.GlobalFree(h)
            return
        ctypes.memmove(ptr, encoded, len(encoded))
        kernel32.GlobalUnlock(h)

        if user32.OpenClipboard(0):
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_UNICODETEXT, h)
            user32.CloseClipboard()
        else:
            kernel32.GlobalFree(h)

    def _win32_get_clipboard(self):
        """Get clipboard text content using Windows API. Returns None on failure."""
        import ctypes
        self._ensure_win32_api()
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        CF_UNICODETEXT = 13
        result = None

        if user32.OpenClipboard(0):
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if handle:
                ptr = kernel32.GlobalLock(handle)
                if ptr:
                    result = ctypes.wstring_at(ptr)
                    kernel32.GlobalUnlock(handle)
            user32.CloseClipboard()
        return result

    # Delay (in seconds) to wait for the paste operation to complete
    # before restoring the original clipboard content.
    _PASTE_SETTLE_DELAY = 0.2

    def _typewrite_clipboard(self, text):
        """
        Insert text by pasting from the clipboard (Ctrl+V).
        Uses Windows API directly via ctypes — no external dependencies,
        works with any keyboard layout, and handles Unicode correctly.
        Windows only. Falls back to pynput on other platforms.
        """
        import sys
        if sys.platform != 'win32':
            print("Warning: 'clipboard' input method is Windows only. Falling back to pynput.")
            interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
            return self._typewrite_pynput(text, interval)

        import ctypes
        user32 = ctypes.windll.user32

        VK_CONTROL = 0x11
        VK_V = 0x56
        KEYEVENTF_KEYUP = 0x0002

        old_clipboard = self._win32_get_clipboard()

        try:
            self._win32_set_clipboard(text)
            time.sleep(0.05)

            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_V, 0, 0, 0)
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            time.sleep(self._PASTE_SETTLE_DELAY)
        finally:
            if old_clipboard is not None:
                try:
                    self._win32_set_clipboard(old_clipboard)
                except Exception:
                    pass

    def _typewrite_pynput(self, text, interval):
        """
        Simulate typing using pynput.

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)

    def _typewrite_ydotool(self, text, interval):
        """
        Simulate typing using ydotool.

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        cmd = "ydotool"
        run_command_or_exit_on_failure([
            cmd,
            "type",
            "--key-delay",
            str(interval * 1000),
            "--",
            text,
        ])

    def _typewrite_dotool(self, text, interval):
        """
        Simulate typing using dotool.

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        assert self.dotool_process and self.dotool_process.stdin
        self.dotool_process.stdin.write(f"typedelay {interval * 1000}\n")
        self.dotool_process.stdin.write(f"type {text}\n")
        self.dotool_process.stdin.flush()

    def cleanup(self):
        """
        Perform cleanup operations, such as terminating the dotool process.
        """
        if self.input_method == 'dotool':
            self._terminate_dotool()
