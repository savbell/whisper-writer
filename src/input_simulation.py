import subprocess
import os
import signal
import time
import win32clipboard
import win32con
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

        if self.input_method == 'pynput':
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

    def typewrite(self, text):
        """
        Simulate typing the given text. Uses clipboard for long text and keystrokes for short text.

        Args:
            text (str): The text to type.
        """
        # Get the character threshold from config, default to 1000 if not set
        char_threshold = ConfigManager.get_config_value('post_processing', 'clipboard_threshold') or 1000
        
        # Use clipboard for long text
        if len(text) > char_threshold:
            self._paste_with_clipboard_preservation(text)
            return

        # Use regular keystroke simulation for shorter text
        interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
        if self.input_method == 'pynput':
            self._typewrite_pynput(text, interval)
        elif self.input_method == 'ydotool':
            self._typewrite_ydotool(text, interval)
        elif self.input_method == 'dotool':
            self._typewrite_dotool(text, interval)

    def _paste_with_clipboard_preservation(self, text):
        """
        Paste text using the clipboard while preserving original clipboard content,
        including images and other data formats.

        Args:
            text (str): The text to paste.
        """
        # Store all clipboard formats
        saved_formats = {}
        win32clipboard.OpenClipboard()
        
        try:
            # Get the list of available formats
            format_id = win32clipboard.EnumClipboardFormats(0)
            while format_id:
                try:
                    data = win32clipboard.GetClipboardData(format_id)
                    saved_formats[format_id] = data
                except:
                    pass  # Skip formats we can't handle
                format_id = win32clipboard.EnumClipboardFormats(format_id)
                
            # Clear clipboard and set our text
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
            
            # Simulate Ctrl+V
            if self.input_method == 'pynput':
                with self.keyboard.pressed(Key.ctrl):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
            elif self.input_method == 'ydotool':
                run_command_or_exit_on_failure([
                    "ydotool", "key", "ctrl+v"
                ])
            elif self.input_method == 'dotool':
                assert self.dotool_process and self.dotool_process.stdin
                self.dotool_process.stdin.write("key ctrl+v\n")
                self.dotool_process.stdin.flush()
                
            # Wait for paste to complete
            time.sleep(0.1)
            
            # Restore all original clipboard formats
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            for format_id, data in saved_formats.items():
                try:
                    win32clipboard.SetClipboardData(format_id, data)
                except:
                    pass  # Skip if we can't restore a particular format
                    
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass  # Ensure clipboard is closed even if an error occurred

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
