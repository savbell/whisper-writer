# <img src="./assets/ww-logo.png" alt="WhisperWriter icon" width="25" height="25"> WhisperWriter
WhisperWriter is a small speech-to-text app that uses [OpenAI's Whisper model](https://openai.com/research/whisper) to auto-transcribe recordings from a user's microphone.

The transcription can either be done locally through the [Whisper Python package](https://pypi.org/project/openai-whisper/) or through a request to [OpenAI's API](https://platform.openai.com/docs/guides/speech-to-text). By default, the app will use the API, but you can change this in the [Configuration Options](#configuration-options). If you choose to use the API, you will need to provide your OpenAI API key in a `.env` file. If you choose to transcribe using a local model, you will need to install the command-line tool [ffmpeg](https://ffmpeg.org/) and potentially [Rust](https://www.rust-lang.org/) as well.

## How to Use
WhisperWriter runs in the background and waits for a keyboard shortcut to be pressed. By default, the shortcut is `ctrl+alt+space`, but you can change this by modifying the `activation_key` line in `src\config.json`. See the full [Configuration Options](#configuration-options).

When the shortcut is pressed, WhisperWriter starts recording from your microphone. It will continue recording until you stop speaking or there is a long enough pause in your speech. While it is recording, the app displays a small status window on your screen showing the current status of the transcription process. Once the transcription is complete, the transcribed text will be automatically written to the active window.

## Prerequisites
Before you can run this app, you'll need to have the following software installed:

- Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
- Python 3.10: [https://www.python.org/downloads/](https://www.python.org/downloads/)
  - The [Whisper Python package](https://github.com/openai/whisper) is only compatible with Python versions >=3.7, <3.11. **Update:** 3.11 compatability seems to be coming in the next release, so this may be updated soon.

If you are running a local model, you will also need to install the command-line tool [ffmpeg](https://ffmpeg.org/) and add it to your PATH:
```
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```
If you are running into issues, you may need to install Rust. See [Whisper Setup](https://github.com/openai/whisper#setup).

## Installation
To set up and run the project, follow these steps:

### 1. Clone the repository:

```
git clone https://github.com/savbell/whisper-writer
cd whisper-writer
```


### 2. Create a virtual environment and activate it:

```
python -m venv venv

# For Linux and macOS:
source venv/bin/activate

# For Windows:
venv\Scripts\activate
```

### 3. Install the required packages:

```
pip install -r requirements.txt
```

### 4. If using the OpenAI API, configure the environment variables:

Copy the ".env.example" file to a new file named ".env":
```
# For Linux and macOS
cp .env.example .env

# For Windows
copy .env.example .env
```
Open the ".env" file and add in your OpenAI API key:
```
OPENAI_API_KEY=<your_openai_key_here>
```

### 5. Run the Python code:

```
python run.py
```

## Configuration Options

WhisperWriter uses a configuration file to customize its behaviour. To set up the configuration, modify the `src\config.json` file:

```json
{
    "use_api": true,
    "api_options": {
        "model": "whisper-1",
        "language": null,
        "temperature": 0.0,
        "initial_prompt": null
    },
    "local_model_options": {
        "model": "base",
        "device": null,
        "language": null,
        "temperature": 0.0,
        "initial_prompt": null,
        "condition_on_previous_text": true,
        "verbose": false
    },
    "activation_key": "ctrl+alt+space",
    "silence_duration": 900,
    "writing_key_press_delay": 0.005,
    "remove_trailing_period": false,
    "add_trailing_space": true,
    "remove_capitalization": false,
    "print_to_terminal": true
}
```
### Model Options
- `use_api`: Set to `true` to use the OpenAI API for transcription. Set to `false` to use a local Whisper model. (Default: `true`)
- `api_options`: Contains options for the OpenAI API. See the [API reference](https://platform.openai.com/docs/api-reference/audio/create?lang=python) for more details.
  - `model`: The model to use for transcription. Currently only `whisper-1` is available. (Default: `"whisper-1"`)
  - `language`: The language code for the transcription in [ISO-639-1 format](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). (Default: `null`)
  - `temperature`: Controls the randomness of the transcription output. Lower values (e.g., 0.0) make the output more focused and deterministic. (Default: `0.0`)
  - `initial_prompt`: A string used as an initial prompt to condition the transcription. Set to null for no initial prompt. (Default: `null`)
- `local_model_options`: Contains options for the local Whisper model. See the [function definition](https://github.com/openai/whisper/blob/main/whisper/transcribe.py#L52-L108) for more details.
  - `model`: The model to use for transcription. See [available models and languages](https://github.com/openai/whisper#available-models-and-languages). (Default: `"base"`)
  - `device`: The device to run the local Whisper model on. Options include `cuda` for NVIDIA GPUs, `cpu` for CPU-only processing, or `null` to let the system automatically choose the best available device. (Default: `null`)
  - `language`: The language code for the transcription in [ISO-639-1 format](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). (Default: `null`)
  - `temperature`: Controls the randomness of the transcription output. Lower values (e.g., 0.0) make the output more focused and deterministic. (Default: `0.0`)
  - `initial_prompt`: A string used as an initial prompt to condition the transcription. Set to null for no initial prompt. (Default: `null`)
  - `conditin_on_previous_text`: Set to `true` to use the previously transcribed text as a prompt for the next transcription request. (Default: `true`)
  - `verbose`: Set to `true` for more detailed transcription output. (Default: `false`)
### Customization Options
- `activation_key`: The keyboard shortcut to activate the recording and transcribing process. (Default: `"ctrl+alt+space"`)
- `silence_duration`: The duration in milliseconds to wait for silence before stopping the recording. (Default: `900`)
- `writing_key_press_delay`: The delay in seconds between each key press when writing the transcribed text. (Default: `0.005`)
- `remove_trailing_period`: Set to `true` to remove the trailing period from the transcribed text. (Default: `false`)
- `add_trailing_space`: Set to `true` to add a trailing space to the transcribed text. (Default: `true`)
- `remove_capitalization`: Set to `true` to convert the transcribed text to lowercase. (Default: `false`)
- `print_to_terminal`: Set to `true` to print the script status and transcribed text to the terminal. (Default: `true`)

If any of the configuration options are invalid or not provided, the program will use the default values.

## License
This project is licensed under the GNU General Public License. See the [LICENSE](LICENSE) file for details.