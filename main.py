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

    def run(self):
        self.result = self._target(*self._args, **self._kwargs)

status_queue = queue.Queue()

def on_shortcut():
    global status_queue

    status_queue.put(('recording', 'Recording...'))
    recording_thread = ResultThread(target=record_and_transcribe, args=(status_queue,))
    status_window = StatusWindow(status_queue)
    status_window.start()
    recording_thread.start()

    def check_status_and_close():
        status = status_queue.get()
        if status[0] == 'idle':
            status_window.window.quit()
            status_window.window.destroy()
        else:
            status_window.schedule_check(check_status_and_close)

    status_window.schedule_check(check_status_and_close)
    recording_thread.join()

    transcribed_text = recording_thread.result

    if transcribed_text:
        pyautogui.write(transcribed_text)


keyboard.add_hotkey('ctrl+alt+space', on_shortcut)  # You can choose your preferred key combination
print('Script activated. Press Ctrl+Alt+Space to start recording and transcribing. Press Ctrl+C to quit.')
keyboard.wait()  # Keep the script running to listen for the shortcut