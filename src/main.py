import os
import subprocess
import sys
import time
import winreg
# Import faster_whisper (and thus CTranslate2's native runtime) BEFORE PyQt5.
# On Windows + NVIDIA GPU, importing PyQt5 first causes an access violation when
# CTranslate2 later loads the model on CUDA (conflicting OpenMP runtimes). Loading
# CTranslate2's libraries first avoids the crash.
import faster_whisper  # noqa: F401  (import order matters; do not move below PyQt5)
import sounddevice as sd
from audioplayer import AudioPlayer
from pynput.keyboard import Controller
from PyQt5.QtCore import QObject, QProcess, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox

from key_listener import KeyListener
from result_thread import ResultThread
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from transcription import create_local_model
from input_simulation import InputSimulator
from utils import ConfigManager


class WhisperWriterApp(QObject):
    def __init__(self):
        """
        Initialize the application, opening settings window if no configuration file is found.
        """
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(os.path.join('assets', 'ww-logo.png')))

        ConfigManager.initialize()

        self.settings_window = SettingsWindow()
        self.settings_window.settings_closed.connect(self.on_settings_closed)
        self.settings_window.settings_saved.connect(self.restart_app)

        if ConfigManager.config_file_exists():
            self.initialize_components()
        else:
            print('No valid configuration file found. Opening settings window...')
            self.settings_window.show()

    def initialize_components(self):
        """
        Initialize the components of the application.
        """
        self.input_simulator = InputSimulator()
        self.last_transcription = None

        self.key_listener = KeyListener()
        self.key_listener.add_callback("activation", "on_activate", self.on_activation)
        self.key_listener.add_callback("activation", "on_deactivate", self.on_deactivation)
        self.key_listener.add_callback("repaste", "on_activate", self.on_repaste)

        model_options = ConfigManager.get_config_section('model_options')
        model_path = model_options.get('local', {}).get('model_path')
        self.local_model = create_local_model() if not model_options.get('use_api') else None

        self.result_thread = None

        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.key_listener.start)
        self.main_window.closeApp.connect(self.exit_app)

        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.status_window = StatusWindow()

        self.create_tray_icon()

        if ConfigManager.get_config_value('misc', 'auto_start_listening'):
            self.key_listener.start()
        else:
            self.main_window.show()

    def create_tray_icon(self):
        """
        Create the system tray icon and its context menu.
        """
        self._load_tray_icons()
        self.mic_state = None  # (connected: bool, device_name: str|None)

        self.tray_icon = QSystemTrayIcon(self.mic_connected_icon, self.app)

        tray_menu = QMenu()

        show_action = QAction('WhisperWriter Main Menu', self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        settings_action = QAction('Open Settings', self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)

        exit_action = QAction('Exit', self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Poll microphone availability and reflect it in the tray.
        # Use a longer interval when connected (10s) to avoid excessive
        # PowerShell process spawning. Faster (5s) when disconnected.
        self.mic_timer = QTimer(self.app)
        self.mic_timer.timeout.connect(self.check_microphone_status)
        self.mic_timer.start(10000)
        self.check_microphone_status()

    def _is_dark_theme(self):
        """Detect whether Windows is using a dark theme via the registry."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            return value == 0  # 0 = dark, 1 = light
        except Exception:
            return True  # default to dark

    def _load_tray_icons(self):
        """Load the theme-appropriate tray icons."""
        theme = 'dark' if self._is_dark_theme() else 'light'
        self.mic_connected_icon = QIcon(os.path.join('assets', f'tray_mic_connected_{theme}.png'))
        self.mic_disconnected_icon = QIcon(os.path.join('assets', f'tray_mic_disconnected_{theme}.png'))
        self.mic_pending_icon = QIcon(os.path.join('assets', f'tray_mic_pending_{theme}.png'))
        self.mic_recording_icon = QIcon(os.path.join('assets', f'tray_mic_recording_{theme}.png'))

    def check_microphone_status(self):
        """
        Detect the microphone connection state.

        Three states:
        - connected: AudioEndpoint PnP status is 'OK' — mic is ready
        - pending: BT fConnected is True but audio endpoint is still
          'Unknown' — headset is on and BT-connected but audio not ready
        - disconnected: BT fConnected is False — headset is off

        The BT-level fConnected check is done by the background worker
        (_bt_reconnect_worker) which updates self.bt_connected. This method
        just reads that flag plus the PnP audio endpoint status.
        """
        device_name = None
        try:
            dev = sd.query_devices(kind='input')
            if dev and dev.get('max_input_channels', 0) > 0:
                device_name = dev.get('name')
        except Exception:
            pass

        # Check the main audio endpoint status
        audio_ok = self._is_pnp_device_ok(device_name) if device_name else False

        # If audio was OK last time but isn't now, reset bt_connected
        # immediately so we don't briefly show 'pending' with stale BT state
        prev_state = self.mic_state[0] if self.mic_state else None
        if prev_state == 'connected' and not audio_ok:
            self.bt_connected = False

        if audio_ok:
            state = 'connected'
        elif getattr(self, 'bt_connected', False):
            state = 'pending'
        else:
            state = 'disconnected'

        new_state = (state, device_name)
        if new_state == self.mic_state:
            return  # no change

        self.mic_state = new_state

        if state == 'connected':
            is_recording = self.result_thread and self.result_thread.isRunning()
            if not is_recording:
                self.tray_icon.setIcon(self.mic_connected_icon)
            self.tray_icon.setToolTip(f"WhisperWriter — Mic: {device_name}")
            # Slow down polling when connected — no need to check often
            self.mic_timer.setInterval(10000)
        elif state == 'pending':
            self.tray_icon.setIcon(self.mic_pending_icon)
            self.tray_icon.setToolTip("WhisperWriter — Headset connected, waiting for audio...")
            # Poll moderately while waiting for audio
            self.mic_timer.setInterval(5000)
        else:
            self.tray_icon.setIcon(self.mic_disconnected_icon)
            self.tray_icon.setToolTip("WhisperWriter — No microphone detected")
            # Poll moderately when disconnected
            self.mic_timer.setInterval(5000)
            # Start/restart the BT worker whenever we're not fully connected.
            # The worker updates self.bt_connected and tries to trigger reconnection.
            # It stops itself once we reach 'connected', so we need to start it again
            # on the next disconnect.
            if not getattr(self, '_bt_worker_running', False):
                self._trigger_bt_reconnect()

    def _is_pnp_device_ok(self, device_name):
        """
        Check whether the AudioEndpoint PnP device matching device_name has
        Status 'OK' (connected) vs 'Unknown' (disconnected). Uses a compiled
        C helper (pnp_status.exe) for minimal overhead vs PowerShell.
        """
        if not device_name:
            return False
        try:
            exe = os.path.join('src', 'pnp_status.exe')
            result = subprocess.run(
                [exe, device_name],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout.strip() == 'OK'
        except Exception:
            return False

    def cleanup(self):
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()

    def exit_app(self):
        """
        Exit the application.
        """
        self.cleanup()
        QApplication.quit()

    def restart_app(self):
        """Restart the application to apply the new settings."""
        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_settings_closed(self):
        """
        If settings is closed without saving on first run, initialize the components with default values.
        """
        if not os.path.exists(os.path.join('src', 'config.yaml')):
            QMessageBox.information(
                self.settings_window,
                'Using Default Values',
                'Settings closed without saving. Default values are being used.'
            )
            self.initialize_components()

    def on_activation(self):
        """
        Called when the activation key combination is pressed.
        """
        if self.result_thread and self.result_thread.isRunning():
            recording_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
            if recording_mode == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif recording_mode == 'continuous':
                self.stop_result_thread()
            return

        # If the mic appears disconnected, try to trigger reconnection first
        if self.mic_state and self.mic_state[0] != 'connected':
            if not self._try_reconnect_mic():
                ConfigManager.console_print("Microphone not available — cannot start recording.")
                return

        self.start_result_thread()

    def _try_reconnect_mic(self):
        """
        Attempt to trigger the Bluetooth headset audio profile to reconnect.
        Calls BluetoothGetDeviceInfo which has been observed to trigger the
        audio profile to connect faster. Returns True if the mic becomes
        available, False otherwise.
        """
        ConfigManager.console_print("Mic disconnected — attempting to reconnect...")
        self._trigger_bt_reconnect()

        # Wait a few seconds and re-check
        for _ in range(5):
            time.sleep(1)
            try:
                dev = sd.query_devices(kind='input')
                if dev and dev.get('max_input_channels', 0) > 0:
                    if self._is_pnp_device_ok(dev.get('name')):
                        ConfigManager.console_print(f"Mic reconnected: {dev.get('name')}")
                        self.mic_state = ('connected', dev.get('name'))
                        self.tray_icon.setIcon(self.mic_recording_icon)
                        self.tray_icon.setToolTip(f"WhisperWriter — Mic: {dev.get('name')}")
                        return True
            except Exception:
                pass

        ConfigManager.console_print("Mic reconnection failed.")
        return False

    def _trigger_bt_reconnect(self):
        """
        Start background thread that monitors BT connection status and
        tries to trigger audio profile reconnection. Updates self.bt_connected
        so check_microphone_status can detect the 'pending' state.
        """
        import threading
        self.bt_connected = False
        self._bt_worker_running = True
        threading.Thread(target=self._bt_reconnect_worker, daemon=True).start()

    def _bt_reconnect_worker(self):
        """Background worker that repeatedly tries to trigger BT reconnection."""
        import ctypes
        import ctypes.wintypes as wintypes

        ConfigManager.console_print("BT reconnection worker started...")

        # Get headset BT address from PnP registry
        headset_address = self._get_headset_bt_address()
        if not headset_address:
            return

        # Load Bluetooth API
        try:
            bthprops = ctypes.WinDLL(r'C:\Windows\System32\bthprops.cpl', use_last_error=True)
        except Exception:
            return

        # Define structures
        class SYSTEMTIME(ctypes.Structure):
            _fields_ = [
                ("wYear", wintypes.WORD), ("wMonth", wintypes.WORD),
                ("wDayOfWeek", wintypes.WORD), ("wDay", wintypes.WORD),
                ("wHour", wintypes.WORD), ("wMinute", wintypes.WORD),
                ("wSecond", wintypes.WORD), ("wMilliseconds", wintypes.WORD),
            ]

        class BLUETOOTH_DEVICE_INFO(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("Address", ctypes.c_ulonglong),
                ("ulClassofDevice", wintypes.ULONG),
                ("fConnected", wintypes.BOOL),
                ("fRemembered", wintypes.BOOL),
                ("fAuthenticated", wintypes.BOOL),
                ("stLastSeen", SYSTEMTIME),
                ("stLastUsed", SYSTEMTIME),
                ("szName", wintypes.WCHAR * 248),
            ]

        class BLUETOOTH_FIND_RADIO_PARAMS(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD)]

        class BLUETOOTH_RADIO_INFO(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("address", ctypes.c_ulonglong),
                ("szName", wintypes.WCHAR * 248),
                ("ulClassofDevice", wintypes.ULONG),
                ("lmpSubversion", wintypes.USHORT),
                ("lmpVersion", wintypes.USHORT),
            ]

        bthprops.BluetoothFindFirstRadio.restype = ctypes.c_void_p
        bthprops.BluetoothFindFirstRadio.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        bthprops.BluetoothFindNextRadio.restype = wintypes.BOOL
        bthprops.BluetoothFindNextRadio.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        bthprops.BluetoothFindRadioClose.restype = wintypes.BOOL
        bthprops.BluetoothFindRadioClose.argtypes = [ctypes.c_void_p]
        bthprops.BluetoothGetDeviceInfo.restype = wintypes.DWORD
        bthprops.BluetoothGetDeviceInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        bthprops.BluetoothSetServiceState.restype = wintypes.DWORD
        bthprops.BluetoothSetServiceState.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]

        # Service GUIDs (little-endian byte representation)
        # HFP: 0000111E-0000-1000-8000-00805F9B34FB
        HFP_GUID = bytes([0x1E,0x11,0x00,0x00, 0x00,0x00, 0x10,0x00, 0x80,0x00, 0x00,0x80,0x5F,0x9B,0x34,0xFB])
        # HSP: 00001108-0000-1000-8000-00805F9B34FB
        HSP_GUID = bytes([0x08,0x11,0x00,0x00, 0x00,0x00, 0x10,0x00, 0x80,0x00, 0x00,0x80,0x5F,0x9B,0x34,0xFB])
        # A2DP: 0000110B-0000-1000-8000-00805F9B34FB
        A2DP_GUID = bytes([0x0B,0x11,0x00,0x00, 0x00,0x00, 0x10,0x00, 0x80,0x00, 0x00,0x80,0x5F,0x9B,0x34,0xFB])

        # Find radio
        params = BLUETOOTH_FIND_RADIO_PARAMS()
        params.dwSize = ctypes.sizeof(BLUETOOTH_FIND_RADIO_PARAMS)
        radio_info = BLUETOOTH_RADIO_INFO()
        radio_info.dwSize = ctypes.sizeof(BLUETOOTH_RADIO_INFO)
        radio_handle = bthprops.BluetoothFindFirstRadio(ctypes.byref(params), ctypes.byref(radio_info))
        if not radio_handle:
            return

        # Keep running until we're fully connected (audio OK).
        # This handles multiple disconnect/reconnect cycles without needing
        # to restart the worker each time.
        while True:
            # Stop if we're fully connected
            if self.mic_state and self.mic_state[0] == 'connected':
                self.bt_connected = True
                break

            # Call BluetoothGetDeviceInfo — this refreshes the device state
            # and has been observed to trigger the audio profile to connect
            device = BLUETOOTH_DEVICE_INFO()
            device.dwSize = ctypes.sizeof(BLUETOOTH_DEVICE_INFO)
            device.Address = headset_address
            result = bthprops.BluetoothGetDeviceInfo(radio_handle, ctypes.byref(device))

            if result == 0:
                self.bt_connected = bool(device.fConnected)
                if device.fConnected != getattr(self, '_last_bt_debug', None):
                    ConfigManager.console_print(f"BT fConnected={bool(device.fConnected)}")
                    self._last_bt_debug = device.fConnected
                if device.fConnected:
                    # BT is connected — repeatedly try to force audio profiles
                    # to connect by calling SetServiceState each iteration
                    for guid_bytes in [HFP_GUID, HSP_GUID, A2DP_GUID]:
                        guid_buf = (ctypes.c_ubyte * 16)(*guid_bytes)
                        bthprops.BluetoothSetServiceState(
                            radio_handle, ctypes.byref(device), guid_buf, 1)
            else:
                self.bt_connected = False

            time.sleep(3)

        bthprops.BluetoothFindRadioClose(radio_handle)
        self._bt_worker_running = False

    def _get_headset_bt_address(self):
        """
        Get the Bluetooth address of the default input device's associated
        Bluetooth device from PnP device InstanceId. Works for any Bluetooth
        headset, not just a specific model.

        The sounddevice name (e.g. 'Headset (PLT_E50)') may not exactly match
        the Bluetooth PnP device name (e.g. 'PLT_E50'), so we extract the
        part in parentheses and also try the full name.
        """
        try:
            # Get the default input device name first
            dev = sd.query_devices(kind='input')
            if not dev or dev.get('max_input_channels', 0) <= 0:
                return None
            mic_name = dev.get('name', '')

            # Extract the device name from parentheses if present
            # e.g. 'Headset (PLT_E50)' -> 'PLT_E50'
            search_name = mic_name
            if '(' in mic_name and ')' in mic_name:
                search_name = mic_name[mic_name.index('(') + 1:mic_name.index(')')]

            # Use the C helper to get the InstanceId
            exe = os.path.join('src', 'pnp_status.exe')
            result = subprocess.run(
                [exe, '--instanceid', search_name, 'Bluetooth'],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            line = result.stdout.strip()
            if 'DEV_' in line:
                parts = line.split('DEV_')
                if len(parts) > 1:
                    addr_str = parts[1].split('\\')[0].split('_')[0]
                    try:
                        return int(addr_str, 16)
                    except ValueError:
                        pass
        except Exception:
            pass
        return None

    def on_deactivation(self):
        """
        Called when the activation key combination is released.
        """
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()

    def start_result_thread(self):
        """
        Start the result thread to record audio and transcribe it.
        """
        if self.result_thread and self.result_thread.isRunning():
            return

        self.result_thread = ResultThread(self.local_model)
        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
            self.status_window.closeSignal.connect(self.stop_result_thread)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()
        self._update_tray_for_recording(True)

    def stop_result_thread(self):
        """
        Stop the result thread.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()
        self._update_tray_for_recording(False)

    def on_transcription_complete(self, result):
        """
        When the transcription is complete, type the result and start listening for the activation key again.
        """
        if result:
            self.last_transcription = result
        self.input_simulator.typewrite(result)

        if ConfigManager.get_config_value('misc', 'noise_on_completion'):
            AudioPlayer(os.path.join('assets', 'beep.wav')).play(block=True)

        self._update_tray_for_recording(False)

        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start()

    def _update_tray_for_recording(self, recording):
        """Switch tray icon between recording and connected states."""
        if not hasattr(self, 'tray_icon'):
            return
        if recording and self.mic_state and self.mic_state[0] == 'connected':
            self.tray_icon.setIcon(self.mic_recording_icon)
        elif self.mic_state and self.mic_state[0] == 'connected':
            self.tray_icon.setIcon(self.mic_connected_icon)

    def on_repaste(self):
        """
        Re-insert the last transcribed text.
        """
        if self.result_thread and self.result_thread.isRunning():
            return
        if self.last_transcription:
            self.input_simulator.release_held_modifiers()
            time.sleep(0.05)
            self.input_simulator.typewrite(self.last_transcription)

    def run(self):
        """
        Start the application.
        """
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = WhisperWriterApp()
    app.run()
