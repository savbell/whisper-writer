import subprocess
import os
import signal
import time
import pyperclip
from pynput.keyboard import Controller as PynputController, Key

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

        if self.input_method in ('pynput', 'clipboard'):
            self.keyboard = PynputController()
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

    def release_held_modifiers(self):
        """Release any physically held modifier keys to prevent interference with typing."""
        if hasattr(self, 'keyboard') and self.keyboard:
            for mod_key in (Key.ctrl_l, Key.ctrl_r,
                            Key.shift_l, Key.shift_r,
                            Key.alt_l, Key.alt_r,
                            Key.cmd_l, Key.cmd_r):
                try:
                    self.keyboard.release(mod_key)
                except Exception:
                    pass

    def typewrite(self, text):
        """
        Simulate typing the given text with the specified interval between keystrokes.

        Args:
            text (str): The text to type.
        """
        interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
        if self.input_method == 'pynput':
            self._typewrite_pynput(text, interval)
        elif self.input_method == 'clipboard':
            self._typewrite_clipboard(text)
        elif self.input_method == 'ydotool':
            self._typewrite_ydotool(text, interval)
        elif self.input_method == 'dotool':
            self._typewrite_dotool(text, interval)

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

    def _typewrite_clipboard(self, text):
        """
        Simulate typing using clipboard paste.

        pynput's press/release synthesizes Shift+letter for capital letters, which
        JetBrains IDEs swallow (dropping the first letter of every sentence). To
        work around this, the text is copied to the clipboard and pasted via
        Ctrl+V (lowercase 'v', so no capital-letter issue). The user's original
        clipboard contents are preserved.

        Args:
            text (str): The text to type.
        """
        if not text:
            return

        # Save the user's current clipboard
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = None

        # Copy the text to clipboard
        pyperclip.copy(text)
        time.sleep(0.05)

        # Paste via Ctrl+V (lowercase v avoids the capital-letter bug)
        self.keyboard.press(Key.ctrl)
        time.sleep(0.02)
        self.keyboard.press('v')
        time.sleep(0.02)
        self.keyboard.release('v')
        time.sleep(0.02)
        self.keyboard.release(Key.ctrl)
        time.sleep(0.05)

        # Restore the user's original clipboard
        if old_clipboard is not None:
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass

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
