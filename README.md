# <img src="./assets/ww-logo.png" alt="WhisperWriter icon" width="25" height="25"> WhisperWriter

![version](https://img.shields.io/badge/version-1.0.0-blue)

<p align="center">
    <img src="./assets/ww-demo-image.gif" alt="WhisperWriter demo gif">
</p>

WhisperWriter is a small speech-to-text app that uses [OpenAI's Whisper model](https://openai.com/research/whisper) to auto-transcribe recordings from a user's microphone.

Once started, the script runs in the background and waits for a keyboard shortcut to be pressed (`ctrl+alt+space` by default, but this can be changed in the [Configuration Options](#configuration-options)). When the shortcut is pressed, the app starts recording from your microphone. It will continue recording until you stop speaking or there is a long enough pause in your speech. While it is recording, a small status window is displayed that shows the current stage of the transcription process. Once the transcription is complete, the transcribed text will be automatically written to the active window.

The transcription can either be done locally through the [Whisper Python package](https://pypi.org/project/openai-whisper/) or through a request to [OpenAI's API](https://platform.openai.com/docs/guides/speech-to-text). By default, the app will use the API, but you can change this in the [Configuration Options](#configuration-options). If you choose to use the API, you will need to provide your OpenAI API key in a `.env` file. If you choose to transcribe using a local model, you will need to install the command-line tool [ffmpeg](https://ffmpeg.org/) and potentially [Rust](https://www.rust-lang.org/) as well.

**Fun fact:** Almost the entirety of this project was pair-programmed with [ChatGPT-4](https://openai.com/product/gpt-4) and [GitHub Copilot](https://github.com/features/copilot) using VS Code. Practically every line, including most of this README, was written by AI. After the initial prototype was finished, WhisperWriter was used to write a lot of the prompts as well!

## Prerequisites
Before you can run this app, you'll need to have the following software installed:

- Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
- Python 3.11: [https://www.python.org/downloads/](https://www.python.org/downloads/)
  - The [Whisper Python package](https://github.com/openai/whisper) is only compatible with Python versions >=3.7.

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

### 4. Switch between a local model and the OpenAI API:
To switch between running Whisper locally and using the OpenAI API, you need to modify the `src\config.json` file:

- If you prefer using the OpenAI API, set `"use_api"` to `true`. You will also need to set up your OpenAI API key in the next step.
- If you prefer using a local Whisper model, set `"use_api"` to `false`. You may also want to change the device that the model uses; see the [Model Options](#model-options). Make sure you followed the [prerequisite steps](#prerequisites) and installed ffmpeg and Rust if necessary.

```
{
    "use_api": true,    // Change this value to false to run Whisper locally
    ...
}
```

### 5. If using the OpenAI API, configure the environment variables:

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

### 6. Run the Python code:

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

## Versioning

We use [Semantic Versioning](https://semver.org/) for this project. For the available versions, see the [tags on this repository](https://github.com/savbell/whisper-writer/tags). 

The version format is `MAJOR.MINOR.PATCH`, where: 

- `MAJOR` versions indicate potentially incompatible changes,
- `MINOR` versions indicate the addition of functionality in a backwards-compatible manner, and
- `PATCH` versions indicate backwards-compatible bug fixes.

For detailed changes, please check the [CHANGELOG.md](CHANGELOG.md) file in this repository.

## Known Issues

As of version 1.0.0, the following issues are known:

- **Numba Deprecation Warning**: When running the Whisper model locally, a [numba depreciation warning](https://numba.readthedocs.io/en/stable/reference/deprecation.html#deprecation-of-object-mode-fall-back-behaviour-when-using-jit) is displayed. This is an issue with the Whisper Python package and will be fixed in a future release. The warning can be safely ignored.

- **FP16 Not Supported on CPU Warning**: A warning may show if you are running the local model on your CPU rather than a GPU using CUDA. This can be safely ignored.

Please note that this is not an exhaustive list and new issues can emerge over time. You can see all reported issues and their current status in our [Issue Tracker](https://github.com/savbell/whisper-writer/issues). If you encounter a problem not listed here, please [open a new issue](https://github.com/savbell/whisper-writer/issues/new) with a detailed description and reproduction steps, if possible.

## License
This project is licensed under the GNU General Public License. See the [LICENSE](LICENSE) file for details.