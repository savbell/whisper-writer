# 💬📝 WhisperWriter
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
python run.py
```

## How to Use
WhisperWriter runs in the background and waits for a keyboard shortcut to be pressed. By default, the shortcut is `ctrl+alt+space`, but you can change it to any other combination you prefer by modifying the `activation_key` line in `src\config.json`.

When the shortcut is pressed, WhisperWriter starts recording from your microphone. It will continue recording until you stop speaking or there is a long enough pause in your speech. While it is recording, the app displays a small status window on your screen showing the current status of the transcription process.

Once the transcription is complete, the transcribed text will be automatically written to the active window.

## Configuration Options

WhisperWriter uses a configuration file to customize its behaviour. To set up the configuration, modify the `src\config.json` file:

```json
{
    "activation_key": "ctrl+alt+space",
    "silence_duration": 900,
    "writing_key_press_delay": 0.008,
    "remove_trailing_period": true,
    "add_trailing_space": false,
    "remove_capitalization": false,
    "print_to_terminal": true
}
```

- `activation_key`: The keyboard shortcut to activate the recording and transcribing process. (Default: "ctrl+alt+space")
- `silence_duration`: The duration in milliseconds to wait for silence before stopping the recording. (Default: 900)
- `writing_key_press_delay`: The delay in seconds between each key press when writing the transcribed text. (Default: 0.008)
- `remove_trailing_period`: Set to true to remove the trailing period from the transcribed text. (Default: false)
- `add_trailing_space`: Set to true to add a trailing space to the transcribed text. (Default: true)
- `remove_capitalization`: Set to true to convert the transcribed text to lowercase. (Default: false)
- `print_to_terminal`: Set to true to print the script status and transcribed text to the terminal. (Default: true)

If any of the configuration options are invalid or not provided, the program will use the default values.

## License
This project is licensed under the GNU General Public License. See the [LICENSE](LICENSE) file for details.