import threading
import keyboard
import pyautogui
from transcription import record_and_transcribe
from status_window import StatusWindow

status_dict = {'status': 'idle', 
               'transcription': ''}

def on_shortcut():
    global status_dict

    status_dict['status'] = 'recording'
    status_dict['transcription'] = ''
    recording_thread = threading.Thread(target=record_and_transcribe, args=(status_dict,))
    status_window = StatusWindow(status_dict)
    status_window.start()
    recording_thread.start()
    status_window.wait()
    def check_status_and_close():
        if status_dict['status'] == 'idle':
            status_window.window.quit()
            status_window.window.destroy()
        else:
            status_window.schedule_check(check_status_and_close)

    status_window.schedule_check(check_status_and_close)
    recording_thread.join()

    transcribed_text = status_dict['transcription']

    if transcribed_text:
        pyautogui.write(transcribed_text)


keyboard.add_hotkey('ctrl+alt+space', on_shortcut)  # You can choose your preferred key combination
print('Script activated. Press Ctrl+Alt+Space to start recording and transcribing. Press Ctrl+C to quit.')
keyboard.wait()  # Keep the script running to listen for the shortcut