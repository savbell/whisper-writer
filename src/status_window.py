import gc
import os
import queue
import tkinter as tk
import threading
from PIL import Image, ImageTk

class StatusWindow(threading.Thread):
    def __init__(self, status_queue):
        threading.Thread.__init__(self)
        self.status_queue = status_queue
        
    def schedule_check(self, func):
        if hasattr(self, 'window'):
            self.window.after(100, func)

    def handle_close_button(self):
        if hasattr(self, 'recording_thread'):
            self.recording_thread.stop()
        self.status_queue.put(('cancel', ''))

    def run(self):
        self.window = tk.Tk()
        self.window.title('Status')
        self.window.configure(bg='#B0C4DE')
        self.window.attributes('-topmost', 1)
        self.window.overrideredirect(1)  # Remove the top bar with menu items

        # Calculate the position for the bottom center of the screen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x_coordinate = int((screen_width - 250) / 2)
        y_coordinate = int(screen_height - 100 - 20)  # 20 pixels above the taskbar
        self.window.geometry(f'250x65+{x_coordinate}+{y_coordinate}')
        
        # Add the text
        title_label = tk.Label(self.window, text='WhisperWriter', font=('Indie Flower', 12, 'bold'), bg='#B0C4DE')
        title_label.place(x=125, y=10, anchor='center')
        self.label = tk.Label(self.window, text='', font=('Indie Flower', 14), bg='#B0C4DE')
        self.label.place(x=140, y=40, anchor='center')

        # Load and display the icons
        self.microphone_image = Image.open(os.path.join('assets', 'microphone.png'))
        self.microphone_image = self.microphone_image.resize((32, 32), Image.ANTIALIAS)
        self.microphone_photo = ImageTk.PhotoImage(self.microphone_image)
        
        self.pencil_image = Image.open(os.path.join('assets', 'pencil.png'))
        self.pencil_image = self.pencil_image.resize((32, 32), Image.ANTIALIAS)
        self.pencil_photo = ImageTk.PhotoImage(self.pencil_image)

        self.icon_label = tk.Label(self.window, image=self.microphone_photo, bg='#B0C4DE')
        self.icon_label.place(x=50, y=40, anchor='center')

        # Close button
        self.close_button = tk.Button(self.window, text='X', font=('Arial', 12, 'bold'), bg='#B0C4DE', 
                                      command=self.handle_close_button, bd=0, highlightthickness=0, relief='flat')
        self.close_button.place(x=235, y=15, anchor='center')

        self.process_queue()
        self.window.mainloop()

    def process_queue(self):
        try:
            status, text = self.status_queue.get_nowait()
            if status in ('idle', 'error', 'cancel'):
                self.window.quit()
                self.window.destroy()
                gc.collect()
            elif status == 'recording' and hasattr(self, 'window'):
                self.icon_label.config(image=self.microphone_photo)
                self.label.config(text=text)
            elif status == 'transcribing' and hasattr(self, 'window'):
                self.icon_label.config(image=self.pencil_photo)
                self.label.config(text=text)
            self.window.after(100, self.process_queue)
        except queue.Empty:
            self.window.after(100, self.process_queue)
