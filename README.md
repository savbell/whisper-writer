# WhisperWriter
WhisperWriter is a small app that uses OpenAI's Whisper API to auto-transcribe recordings from a user's microphone. The app is written in Python and uses the `keyboard`, `pyautogui`, `sounddevice`, `webrtcvad`, `openai`, and `tkinter` libraries.

## Prerequisites
Before you can run this app, you'll need to have the following software installed:

- Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
- Python 3.6 or later: [https://www.python.org/downloads/](https://www.python.org/downloads/)

You will also need to have an OpenAI API key. If you don't have one, you can sign up for the OpenAI API here: [https://beta.openai.com/signup/](https://beta.openai.com/signup/)

## Installation
To set up and run the project, follow these steps:

1. **Clone the repository:**
```
git clone https://github.com/savbell/whisper-writer
cd whisper-writer
```


2. **Create a virtual environment and activate it:**
```
python -m venv venv
source venv/bin/activate # For Linux and macOS
venv\Scripts\activate # For Windows
```


3. **Install the required packages:**
```
pip install -r requirements.txt
```


4. **Configure the environment variables:**

- Copy the ".env.example" file to a new file named ".env":
```
cp .env.example .env # For Linux and macOS
copy .env.example .env # For Windows
```
- Open the ".env" file and add in your OpenAI API key:
```
OPENAI_API_KEY=<your_openai_key_here>
```


5. **Run the Python code:**
```
python main.py
```

## How to Use
WhisperWriter runs in the background and waits for a keyboard shortcut to be pressed. By default, the shortcut is `ctrl+alt+space`, but you can change it to any other combination you prefer by modifying the `keyboard.add_hotkey` line in `main.py`.

When the shortcut is pressed, WhisperWriter starts recording from your microphone. It will continue recording until you stop speaking or there is a long enough pause in your speech. While it is recording, the app displays a small status window on your screen showing the current status of the transcription process.

Once the transcription is complete, the transcribed text will be automatically written to the active window.

## License
This project is licensed under the GNU General Public License. See the [LICENSE](LICENSE) file for details.