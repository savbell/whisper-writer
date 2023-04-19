import tkinter as tk
import threading
from PIL import Image, ImageTk

class StatusWindow(threading.Thread):
    def __init__(self, status_dict):
        threading.Thread.__init__(self)
        self.status_dict = status_dict
        self.window_created = threading.Event()
        
    def schedule_check(self, func):
        self.window.after(100, func)

    def wait(self):
        self.window_created.wait()

    def run(self):
        self.window = tk.Tk()
        self.window.title('Status')
        self.window.configure(bg='#B0C4DE')
        self.window.attributes('-topmost', 1)
        self.window.overrideredirect(1)  # Remove the top bar with menu items

        # Calculate the position for the bottom center of the screen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x_coordinate = int((screen_width - 200) / 2)
        y_coordinate = int(screen_height - 100 - 20)  # 20 pixels above the taskbar
        self.window.geometry(f'350x50+{x_coordinate}+{y_coordinate}')
        
        self.label = tk.Label(self.window, text="", font=("Indie Flower", 14), bg="#B0C4DE")
        self.label.place(x=220, y=25, anchor="center")

        # Load and display the icons
        self.microphone_image = Image.open('microphone.png')
        self.microphone_image = self.microphone_image.resize((32, 32), Image.ANTIALIAS)
        self.microphone_photo = ImageTk.PhotoImage(self.microphone_image)
        
        self.pencil_image = Image.open('pencil.png')
        self.pencil_image = self.pencil_image.resize((32, 32), Image.ANTIALIAS)
        self.pencil_photo = ImageTk.PhotoImage(self.pencil_image)

        self.icon_label = tk.Label(self.window, image=self.microphone_photo, bg="#B0C4DE")
        self.icon_label.place(x=100, y=25, anchor="center")

        self.check_status()
        self.window_created.set()
        self.window.mainloop()

    def check_status(self):
        status = self.status_dict['status']

        if status in ('idle', 'error'):
            self.window.quit()
            self.window.destroy()
        else:
            if status == 'recording':
                self.icon_label.config(image=self.microphone_photo)
            elif status == 'transcribing':
                self.icon_label.config(image=self.pencil_photo)

            self.label.config(text=status.capitalize()+'...')
            self.window.after(100, self.check_status)
