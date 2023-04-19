import queue
import threading
import keyboard
import pyautogui
from transcription import record_and_transcribe
from status_window import StatusWindow

class ResultThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ResultThread, self).__init__(*args, **kwargs)
        self.result = None
        self.stop_recording = False

    def run(self):
        self.result = self._target(*self._args, stop_recording_flag=lambda: self.stop_recording, **self._kwargs)
        
    def stop(self):
        self.stop_recording = True

status_queue = queue.Queue()

def clear_status_queue():
    while not status_queue.empty():
        try:
            status_queue.get_nowait()
        except queue.Empty:
            break

def on_shortcut():
    global status_queue
    clear_status_queue()

    status_queue.put(('recording', 'Recording...'))
    recording_thread = ResultThread(target=record_and_transcribe, args=(status_queue,))
    status_window = StatusWindow(status_queue)
    status_window.recording_thread = recording_thread
    status_window.start()
    recording_thread.start()
    
    recording_thread.join()

    if status_window.is_alive():
        status_queue.put(('cancel', ''))

    transcribed_text = recording_thread.result

    if transcribed_text:
        pyautogui.write(transcribed_text)


keyboard.add_hotkey('ctrl+alt+space', on_shortcut)  # You can choose your preferred key combination
print('Script activated. Press Ctrl+Alt+Space to start recording and transcribing. Press Ctrl+C on the terminal window to quit.')
keyboard.wait()  # Keep the script running to listen for the shortcut