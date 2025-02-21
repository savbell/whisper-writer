from pynput.keyboard import Controller, Key
import time
import platform
import subprocess
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from utils import ConfigManager
if platform.system() == 'Windows':
    import pythoncom  # For COM initialization
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, IAudioMeterInformation

class MediaController:
    def __init__(self):
        self.keyboard = Controller()
        self.was_playing = False
        self.initial_state_playing = False  # Track initial state
        self.original_volumes = {}  # Store original volumes for each session
        self.system = platform.system()
        if self.system == 'Windows':
            # Initialize COM in the main thread
            pythoncom.CoInitialize()

    def is_audio_playing(self):
        """Check if audio is actually playing by monitoring audio levels"""
        try:
            if self.system == 'Windows':
                # Initialize COM for this thread
                pythoncom.CoInitialize()
                try:
                    # Get all active audio sessions
                    sessions = AudioUtilities.GetAllSessions()
                    
                    for session in sessions:
                        if session.Process and session.Process.name() not in ['python.exe', 'pythonw.exe']:
                            # Get audio meter information
                            volume = session._ctl.QueryInterface(IAudioMeterInformation)
                            peak = volume.GetPeakValue()
                            print(f"Checking audio for {session.Process.name()}: Peak = {peak}")
                            if peak > 0.0001:  # Detect actual audio signal
                                print(f"Detected audio playing in {session.Process.name()}")
                                return True
                    print("No active audio detected")
                    return False
                finally:
                    # Uninitialize COM when done
                    pythoncom.CoUninitialize()
            
            elif self.system == 'Linux':
                # Use pactl to check for audio levels
                result = subprocess.run(['pactl', 'list', 'sink-inputs'], 
                                     capture_output=True, text=True)
                is_playing = 'RUNNING' in result.stdout and 'volume:' in result.stdout
                print(f"Audio playing status check (Linux): {is_playing}")
                return is_playing
            
            elif self.system == 'Darwin':  # macOS
                # Use CoreAudio to check audio levels
                result = subprocess.run(['osascript', '-e',
                    'get volume settings & " " & get (output muted of (get volume settings))'],
                    capture_output=True, text=True)
                volume, muted = result.stdout.strip().split()
                is_playing = int(volume) > 0 and muted.lower() == 'false'
                print(f"Audio playing status check (macOS): {is_playing}")
                return is_playing
                
        except Exception as e:
            print(f"Error checking audio state: {str(e)}")
            return False

    def adjust_volume(self, reduce_by_percent):
        """Reduce volume by specified percentage of current volume"""
        try:
            if self.system == 'Windows':
                pythoncom.CoInitialize()
                try:
                    sessions = AudioUtilities.GetAllSessions()
                    for session in sessions:
                        if session.Process and session.Process.name() not in ['python.exe', 'pythonw.exe']:
                            volume = session.SimpleAudioVolume
                            current_volume = volume.GetMasterVolume()
                            # Store original volume
                            self.original_volumes[session.Process.name()] = current_volume
                            # Calculate new volume (as percentage of current)
                            new_volume = current_volume * (1 - reduce_by_percent/100)
                            volume.SetMasterVolume(new_volume, None)
                            print(f"Reduced volume for {session.Process.name()} from {current_volume:.2f} to {new_volume:.2f}")
                finally:
                    pythoncom.CoUninitialize()
        except Exception as e:
            print(f"Error adjusting volume: {str(e)}")

    def restore_volumes(self):
        """Restore original volumes"""
        try:
            if self.system == 'Windows':
                pythoncom.CoInitialize()
                try:
                    sessions = AudioUtilities.GetAllSessions()
                    for session in sessions:
                        if session.Process and session.Process.name() in self.original_volumes:
                            volume = session.SimpleAudioVolume
                            original_volume = self.original_volumes[session.Process.name()]
                            volume.SetMasterVolume(original_volume, None)
                            print(f"Restored volume for {session.Process.name()} to {original_volume:.2f}")
                finally:
                    pythoncom.CoUninitialize()
                self.original_volumes.clear()
        except Exception as e:
            print(f"Error restoring volumes: {str(e)}")

    def pause_media(self):
        """Handle media control based on settings"""
        self.initial_state_playing = self.is_audio_playing()
        
        if self.initial_state_playing:
            print("Pausing media playback")
            self.keyboard.press(Key.media_play_pause)
            self.keyboard.release(Key.media_play_pause)
            time.sleep(0.1)
            self.was_playing = True
        else:
            print("No audio playing - skipping audio control")
            self.was_playing = False

    def resume_media(self):
        """Restore audio state"""
        if self.was_playing and self.initial_state_playing:
            print("Resuming media playback")
            self.keyboard.press(Key.media_play_pause)
            self.keyboard.release(Key.media_play_pause)
            time.sleep(0.1)
        
        self.was_playing = False
        self.initial_state_playing = False

    def __del__(self):
        """Cleanup when the object is destroyed"""
        if self.system == 'Windows':
            try:
                pythoncom.CoUninitialize()
            except:
                pass