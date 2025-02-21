# <img src="./assets/ww-logo.png" alt="WhisperWriter icon" width="25" height="25"> WhisperWriter

![version](https://img.shields.io/badge/version-1.1.1-blue)

<p align="center">
    <img src="./assets/ww-demo-image-02.gif" alt="WhisperWriter demo gif" width="340" height="136">
</p>

WhisperWriter is a speech-to-text app that lets you dictate and transcribe text, entering it in any app on your computer. It can do so using local transcription models (OpenAI's Whisper models or Alpha Cephei's Vosk models), or via API-based services including OpenAI, Deepgram, and Groq.

This version of the app started as a Windows-focused fork by [Thomas Frank](https://github.com/TomFrankly). The README below has been updated to include all of the changes and updates.

## Features

WhisperWriter has three main "headliner" features:

1. **Speech-to-Text in any app**: Hit a hotkey, record your voice, and have it transcribed to the active window, wherever your blinking cursor is.
2. **LLM Cleanup and Instruction**: Hit *different* hotkeys to send the transcribed text to an LLM provider/model with custom system instructions. Two hotkey slots are provided: One for cleaning up your transcript (improving spelling, grammar, etc.), and one for sending the transcript to an LLM with custom instructions.
3. **Clipboard Cleanup**: Hit yet another hotkey to send the current clipboard text to an LLM provider/model with custom system instructions. This is ideal for cleaning up text that's already been printed into the current application.

Transcription and LLM modes **both** give you a choice between using local models or sending requests to various APIs. All API modes are **BYOK** (Bring Your Own Key). Keys are stored in the Windows Credential Manager using the `keyring` library.

Combine local transcription with local LLM models for private and free speech-to-text and AI processing.

Transcription options:

- **Local options:**
  - All `faster-whisper` models, including newer models like `distil-large-v3` and `large-v3-turbo`.
  - Selected `vosk` models.
- **API options:**
  - [OpenAI's](https://platform.openai.com/docs/guides/speech-to-text) `whisper-1` model.
  - [Deepgram's](https://developers.deepgram.com/docs/model) `nova-3` and `nova-2` models.
  - [Groq's](https://console.groq.com/docs/speech-text) `whisper-large-v3-turbo`, `distil-whisper-large-v3-en`, and `whisper-large-v3` models.

LLM options:

- **Local options:**
  - Ollama models (I recommend "airat/karen-the-editor-v2-strict" for strict text cleanup. I've found "llama3.2" to be good for more custom instructions.)
- **API options:**
  - [OpenAI](https://platform.openai.com/docs/models) (ChatGPT)
  - [Anthropic](https://docs.anthropic.com/en/docs/about-claude/models) (Claude)
  - [Google](https://ai.google.dev/gemini-api/docs/models/gemini) (Gemini)
  - [Groq](https://console.groq.com/docs/models) (all text models)

When using an API for LLM processing, specify any official model name your API key can access. Use model names as they're listed in the API provider's documentation - e.g. `gemini-1.5-flash`, `gpt-4o-mini`, `claude-3-5-sonnet-latest`, etc.

WhisperWriter includes the following recording modes:

- **Press-to-toggle** (stop recording when activation key is pressed again) **(default)**
- **Continuous mode** (auto-restart recording after pause in speech until activation key is pressed again)
- **Voice activity detection** (stop recording after pause in speech)
- **Hold-to-record** (stop recording when activation key is released)

> [!NOTE]
> When using Continuous mode, you'll need to explicitly check the "Continuous API" checkbox in the settings in order to use any API providers. This is one of several safety features I added to this mode.

Additionally, WhisperWriter has a few other tricks up its sleeve:

- **Find and Replace**: Add a `.txt` or `.json` file with custom find and replace rules.
  - Simple mode: Add a `.txt` file with a comma-separated list of `find,replace` pairs (one per line).
  - JSON mode: Add a `.json` file with an array of objects, each containing `type`, `find`, `replace`, and (optionally) `transforms` properties. Supports regular expressions and transformations on regex capture groups. See `examples/regex_find_replace_.json` for an example.
- **Expanded System Instructions**: For each LLM mode, as well as Text (Clipboard) Cleanup mode, you can add a `.txt` file with additional content that will be appended to the system instructions.
  - Example: Add a sitemap of your documentation and instruct the model to build Markdown links from the URLs when it detects you're trying to link to a page in a support response or email.
- **Clipboard Input and Threshold**: If the transcript contains more characters than the Clipboard Threshold, it will be pasted into the current application. This will replace the default behavior of simulating keyboard input, which can be unreliable.
- **Pause Audio While Recording**: You can choose to automatically pause audio while recording; it'll start playing again when you stop recording.
- **Keyring Credentials**: Keys are stored in the Windows Credential Manager using the `keyring` library.

## Installing WhisperWriter

### Prerequisites
This version of WhisperWriter officially supports Windows. Both of my test machines are running Windows 11. The previous version, 1.0.1, should officially support Linux.

As it is a Python app, this version can likely be modified to work on Linux and macOS, but it's not 100% set up for either yet.

Before you can run this app, you'll need to have the following software installed:

- Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
- Python `3.12`: [https://www.python.org/downloads/](https://www.python.org/downloads/) - *Python 3.13 currently does not work due to incompatibility with the `pynput` library.*

WhisperWriter can use one of several transcription APIs, or it can use a local Whisper or Vosk model.

If you have an NVIDIA GPU and want to run local transcription on your GPU, you'll need to install the following NVIDIA libraries:

- [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads?target_os=Windows) - *Installs cuBLAS for CUDA 12*
- [cuDNN 9 for CUDA 12](https://developer.nvidia.com/cudnn) - *I'm using the full cuDNN 9.7.1 library - specifically the Windows x86_64 on Version 10 with the exe (local) installer type.*

WhisperWriter uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for local transcription. See their README for more information and alternative installation methods.

If you don't install these CUDA tools, you can still run local transcription on your CPU, but it will be much slower. You'll likely need to stick with smaller models, like `tiny` or `base`. Of course, you can also use one of the transcription APIs. You can see some of my informal benchmarks below to see how fast various models are on my machine.

### Installation
To set up and run the project, open a command prompt, navigate to your desired install location, and run the following commands:

*Note: While installing Python, be sure to check the option to add Python to your PATH.*

#### 1. Clone the repository:

```
git clone https://github.com/savbell/whisper-writer

cd whisper-writer
```

#### 2. Create a virtual environment and activate it:

```
# "python -m venv" is used to create a virtual environment. The second "venv" is the name of the virtual environment and its directory.
python -m venv venv

# Or, if you have multiple versions of Python installed, you can specify 3.12:
python -3.12 -m venv venv
```

Next, activate the virtual environment:

```
# For Windows:
venv\Scripts\activate

# For Linux and macOS (not tested, likely broken):
source venv/bin/activate
```

#### 3. Install the required packages:

```
pip install .
```

#### 4. (NVIDIA GPU users only) Install the CUDA-compatible versions of Torch and Torchaudio:
*Note: This must be done **after** installing all the other dependencies using the command above. I'm not sure why, but I'm unable to specify the CUDA-specific versions of `torch` and `torchaudio` in the `pyproject.toml` file. This means `faster-whisper` will initially install the CPU-only versions of these libraries. By running the command below, you'll override them with the CUDA-compatible versions.*

*This command will install the latest CUDA-compatible versions of these packages, which explicitly support CUDA 12.6. However, if you have CUDA 12.8 installed in your system, they will still work.*
```
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

#### 4. Run the Python code:

```
python run.py
```

<details>
<summary>How to Launch WhisperWriter More Quickly</summary>

After you've run all the commands above once, you can launch WhisperWriter more quickly by creating a batch file. For example, you could create a file called `launcher.bat` (within the whisper-writer directory) and add the following:

```
@echo off
REM Store the directory where the batch file is located
set SCRIPT_DIR=%~dp0
REM Change directory to where this script is located
cd /d "%SCRIPT_DIR%"
REM Activate the virtual environment
call venv\Scripts\activate
REM Run the app with full path
python "%SCRIPT_DIR%run.py"
REM When the app ends, optionally pause to view output
pause
```

Then you can launch WhisperWriter by double-clicking the `launcher.bat` file.


</details>


#### 5. Configure and start WhisperWriter:
On first run, a Settings window should appear. Once configured and saved, another window will open. Press "Start" to activate the keyboard listener. Press the activation key (`ctrl+shift+space` by default) to start recording and transcribing to the active window.

## Using WhisperWriter

### Configuration Options

WhisperWriter saves changes to settings to a configuration file.

The first time you open the app, if a configuration file doesn't exist, a Settings window will appear. You can also access Settings at any time by finding WhisperWriter in the system tray and right-clicking the icon.

#### Model Options
- `use_api`: Toggle to choose whether to use the OpenAI API or a local Whisper model for transcription. (Default: `false`)
- `common`: Options common to both API and local models.
  - `language`: The language code for the transcription in [ISO-639-1 format](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes). (Default: `null`)
  - `temperature`: Controls the randomness of the transcription output. Lower values make the output more focused and deterministic. (Default: `0.0`)
  - `initial_prompt`: A string used as an initial prompt to condition the transcription. More info: [OpenAI Prompting Guide](https://platform.openai.com/docs/guides/speech-to-text/prompting). (Default: `null`)

- `api`: Configuration options for the OpenAI API. See the [OpenAI API documentation](https://platform.openai.com/docs/api-reference/audio/create?lang=python) for more information.
  - `provider`: The provider to use for transcription. Current options include `openai`, `deepgram`, and `groq`. (Default: `openai`)
  - `model`: The model to use for transcription. Supported models:
    - OpenAI: `whisper-1`
    - Deepgram: `nova-3` and `nova-2`
    - Groq: `whisper-large-v3-turbo`, `distil-whisper-large-v3-en`, and `whisper-large-v3`
  - `base_url`: The base URL for the API. Can be changed to use a local API endpoint, such as [LocalAI](https://localai.io/). (Default: `https://api.openai.com/v1`)
  - `openai_transcription_key`: Your API key for the OpenAI API. Required for OpenAI transcription. (Default: `null`)
  - `deepgram_transcription_key`: Your API key for the Deepgram API. Required for Deepgram transcription. (Default: `null`)
  - `groq_transcription_key`: Your API key for the Groq API. Required for Groq transcription. (Default: `null`)

- `local`: Configuration options for the local Whisper model.
  - `model`: The model to use for transcription. The larger models provide better accuracy but are slower. See [available models and languages](https://github.com/openai/whisper?tab=readme-ov-file#available-models-and-languages). (Default: `base`)
  - `device`: The device to run the local Whisper model on. Use `cuda` for NVIDIA GPUs, `cpu` for CPU-only processing, or `auto` to let the system automatically choose the best available device. (Default: `auto`)
  - `compute_type`: The compute type to use for the local Whisper model. [More information on quantization here](https://opennmt.net/CTranslate2/quantization.html). (Default: `default`)
  - `condition_on_previous_text`: Set to `true` to use the previously transcribed text as a prompt for the next transcription request. (Default: `true`)
  - `vad_filter`: Set to `true` to use [a voice activity detection (VAD) filter](https://github.com/snakers4/silero-vad) to remove silence from the recording. (Default: `false`)
  - `model_path`: The path to the local Whisper model. If not specified, the default model will be downloaded. (Default: `null`)

#### Recording Options
- `activation_key`: The keyboard shortcut to activate the recording and transcribing process. Separate keys with a `+`. (Default: `ctrl+shift+space` - I personally use `ctrl+alt+numpad1`)
- `llm_cleanup_key`: The keyboard shortcut to process the last transcription through LLM cleanup. Separate keys with a `+`. (Default: `null` - I personally use `ctrl+alt+numpad2`)
- `llm_instruction_key`: The keyboard shortcut to process the last transcription through LLM with custom instructions. Separate keys with a `+`. (Default: `null` - I personally use `ctrl+alt+numpad3`)
- `text_cleanup_key`: The keyboard shortcut to clean up selected text through LLM. Separate keys with a `+`. (Default: `null` - I personally use `ctrl+alt+numpad4`)
- `input_backend`: The input backend to use for detecting key presses. `auto` will try to use the best available backend. (Default: `auto`) Since I forked WhisperWriter for Windows use only (using `pynput`), I can't guarantee that `evdev` will work right now.
- `recording_mode`: The recording mode to use. Options include `continuous` (auto-restart recording after pause in speech until activation key is pressed again), `voice_activity_detection` (stop recording after pause in speech), `press_to_toggle` (stop recording when activation key is pressed again), `hold_to_record` (stop recording when activation key is released). (Default: `press_to_toggle`)
- `sound_device`: The device to be used for recording. Shows a dropdown list of available devices. (Default: `null`)
- `sample_rate`: The sample rate in Hz to use for recording. (Default: `16000`)
- `silence_duration`: The duration in milliseconds to wait for silence before stopping the recording. (Default: `900`)
- `min_duration`: The minimum duration in milliseconds for a recording to be processed. Recordings shorter than this will be discarded. (Default: `100`)
- `allow_continuous_api`: Allow continuous recording mode when using remote APIs (requires explicit opt-in for safety). (Default: `false`)
- `continuous_timeout`: Number of seconds of silence after which continuous recording will automatically stop (0 to disable) (Default: `10`)

#### Post-processing Options
- `writing_key_press_delay`: The delay in seconds between each key press when writing the transcribed text. Only used for transcribed text shorter than the `clipboard_threshold` value. (Default: `0.005`)
- `remove_trailing_period`: Set to `true` to remove the trailing period from the transcribed text. (Default: `false`)
- `add_trailing_space`: Set to `true` to add a space to the end of the transcribed text. (Default: `true`)
- `remove_capitalization`: Set to `true` to convert the transcribed text to lowercase. (Default: `false`)
- `input_method`: The method to use for simulating keyboard input. (Default: `pynput`)
- `clipboard_threshold`: The number of characters at which the transcribed text will be pasted into the active window instead of being typed out. I've added code to restore the previous clipboard content after the transcription is pasted, so I generally recommend setting a low value here. I use 10. (Default: `1000`)
- `find_replace_file`: The path to a text or JSON file containing find/replace rules. See the Find and Replace section below for more information. (Default: `null`)

#### LLM Post-processing Options
- `enabled`: Set to `true` to enable LLM post-processing. (Default: `false`)
- `api_type`: The LLM API to use for post-processing. (Default: `chatgpt`)
  - `chatgpt`: Use OpenAI's ChatGPT API.
  - `claude`: Use Anthropic's Claude API.
  - `gemini`: Use Google's Gemini API.
  - `groq`: Use Groq's LLM service.
  - `ollama`: Use Ollama's local LLM. Ollama must be installed separately.
- `claude_api_key`: Your API key for the Anthropic API. Required for Claude post-processing. (Default: `null`)
- `openai_api_key`: Your API key for the OpenAI API. Required for OpenAI post-processing. (Default: `null`)
- `gemini_api_key`: Your API key for the Google Gemini API. Required for Gemini post-processing. (Default: `null`)
- `groq_api_key`: Your API key for the Groq LLM service. Required for Groq post-processing. (Default: `null`)
- `cleanup_model`: The model to use for cleanup post-processing. (Default: `gpt-4o-mini`)
- `instruction_model`: The model to use for instruction post-processing. (Default: `gpt-4o-mini`)
- `system_prompt`: The system prompt to use for post-processing. (Default: `You are a helpful assistant that cleans up transcribed text. Fix any grammar, punctuation, or formatting issues while maintaining the original meaning.`)
- `instruction_system_message`: The system message to use for instruction post-processing. (Default: `You are an AI assistant. Interpret the user's text as instructions and respond appropriately. Be concise and direct in your responses.`)
- `temperature`: The temperature to use for post-processing. (Default: `0.3`)
- `text_cleanup_system_message`: The system message to use for text (clipboard) cleanup and post-processing. (Default: `You are a helpful assistant that cleans up selected text. Fix any spelling, grammar, or formatting issues while preserving the original meaning.`)

When specifying a model, use the official model name as it's listed in the API provider's documentation - e.g. `gpt-4o-mini`, `claude-3-5-sonnet-latest`, `gemini-1.5-flash`, etc. For Ollama, you can find all model names in the [Ollama Library](https://ollama.com/library) page.

#### Miscellaneous Options
- `print_to_terminal`: Set to `true` to print the script status and transcribed text to the terminal. (Default: `true`)
- `hide_status_window`: Set to `true` to hide the status window during operation. (Default: `false`)
- `noise_on_completion`: Set to `true` to play a noise after the transcription has been typed out. (Default: `false`)
- `pause_media_while_recording`: Set to `true` to pause audio while recording. (Default: `false`)

If any of the configuration options are invalid or not provided, the program will use the default values.

Check out the [CHANGELOG](CHANGELOG.md) for more details on what's been added and changed.

## Additional Notes

### Find and Replace

WhisperWriter can use a text or JSON file to find and replace text in the transcribed text. You can set this file in the `find_replace_file` option within the **Post-processing Options** section of the Settings window.

#### Text Mode

For simple find and replace operations, you can use a text file with one `find,replace` pair per line. For example:

```
soda,coke
ground beef,hamburger meat
semi truck,18-wheeler
```

This will find all instances of "soda" and replace them with "coke", etc.

#### JSON Mode

For more complex find and replace operations, you can use a JSON file with an array of objects, each containing `type`, `find`, `replace`, and (optionally) `transforms` properties.

The `find` property supports regular expressions, and you can reference regex capture groups in the `replace` property using `$1`, `$2`, etc.

The `transforms` property allows you to apply transformations to specific regex capture groups, and supports the following functions:

- `capitalize`: Capitalize the first letter of the word.
- `upper`: Convert the entire string to uppercase.
- `lower`: Convert the entire string to lowercase.
- `strip`: Remove all whitespace from the string.
- `title`: Capitalize the first letter of each word in the string.

For example:

```json
[
  {
    "type": "regex",
    "find": "(\\d+)",
    "replace": "[$1]"
  }
]
```

This will find all instances of a number in the transcribed text and replace them with the number in square brackets.

Here's another example:

```json
[
    {
        "type": "regex",
        "find": "quote,?\\s+(.)(.+?)\\s+end\\s*quote,?",
        "replace": "\"$1$2\"",
        "transforms": [
            {
                "group": 1,
                "operations": ["capitalize"]
            }
        ]
    },
    {
        "type": "regex",
        "find": "quote,?\\s+(.+?)\\s+(un)?quote,?",
        "replace": "\"$1\""
    }
]
```

The first rule looks for the word "quote", followed by some other text, and finally the specific words "end quote".

It then replaces "quote" and "end quote" with quotation marks (`"`) and **capitalizes the first letter of the text between the quotes**.

The second rule does the same thing, looks for "quote" plus "unquote", or "quote" plus another "quote".

In this case, it won't capitalize the first letter of the quotation.

In effect, these two rules give you the ability to add quotation marks to your transcribed text, and optionally start the quote with a capital letter (by ending specifically with "end quote").

Note how the "end quote" rule is listed first. The regex engine will try to match the first rule first, and if it doesn't find a match, it will try the second rule.

As you can see, this JSON mode gives you the ability to essentially write your own "control" words that can be used in a limited way to re-format the transcribed text.

If you need more advanced processing, you can use LLM Cleanup Mode to process the transcribed text with an LLM.

### Speed Benchmarks

In the detail block below, I've included some informal benchmarks for the speed of various models on my machine.

For each, I dictated a roughly 30-second passage of text, and measured the time it took to transcribe it.

Transcription times will vary based on hardware and settings, and API-based models will vary based on the API response time.

<details>
<summary>Speed Benchmarks</summary>
Groq, distil-whisper - no API key?: (28.62 seconds - 4.24 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your applications. If your application is error-sensitive and requires multilingual support, use Whisper Large V3. If your application is less sensitive to errors and requires English only, use Distill Whisper Large V3N. If your application requires multilingual support and you need the best price for performance, use Whisper Large V3 Turbo. The following table breaks down the metrics for each model. 

Groq, distil-whisper - with API key set: (28.71 seconds - 4.28 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your applications. If your application is error-sensitive and requires multilingual support, use Whisper Large V3. If your application is less sensitive to errors and requires English only, use Distill Whisper-Lars V3N. If your application requires multilingual support and you need the best price for performance, use Whisper-Lage V3 Turbo. The following table breaks down the metrics for each model.'

Groq, distil-whisper - with API key set and upgraded to Developer account: (28.98 seconds - 1.44 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your applications. If your application is error-sensitive and requires multilingual support, use Whisper Large V3. If your application is less sensitive to errors and requires English only, use Distill Whisper Large V3N. If your application requires multilingual support and you need the best price for performance, use Whisper Large V3 Turbo. The following table breaks down the metrics for each model.

Deepgram, nova-3: (28.83 seconds - 0.76 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade offs between models to find the one most suitable for your applications. If your application is error sensitive and requires multilingual support, use whisper Large v three. If your application is less sensitive to errors and requires English only, use Distill Whisper Large v three n. If your application requires multilingual support and you need the best price per performance, use Whisper Large v three Turbo. The following table breaks down the metrics for model.

Deepgram, nova-2 (28.98 seconds - 0.92 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade offs between models to find the one most suitable for your applications. If your application is error sensitive and requires multilingual support, use Whisper large v three. If your application is less sensitive to errors and requires English only, use distill whisper large v three n. If your application requires multilingual support and you need the best price for performance, use Whisper Large v three Turbo. The following table breaks down the metrics for each model.

OpenAI, whisper-1 (28.83 seconds - 2.32 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your application. If your application is error sensitive and requires multilingual support, use Whisper Large V3. If your application is less sensitive to errors and requires English only, use Distill Whisper Large V3n. If your application requires multilingual support and you need the best price for performance, use Whisper Large V3 Turbo. The following table breaks down the metrics for each model.

Local, whisper-large-v3-turbo, CUDA (27.54 seconds - 0.90 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable to your applications. If your application is error-sensitive and requires multilingual support, use Whisper Large V3. If your application is less sensitive to errors and requires English only, use Distill Whisper Large V3N. If your application requires multilingual support and need the best price per performance, use Whisper Large V3 Turbo. The following table breaks down the metrics for each model. 

Local, distil-large-v3, CUDA (27.45 seconds - 0.82 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your applications. If your application is error-sensitive and requires multilingual support, use Whisper Large V3. If your application is less sensitive to errors and requires English-only, use Distill Whisper Large V3N. If your application requires multilingual support and you need the best price for performance, use Whisper Large V3 Turbo. The following table breaks down the metrics for each model. 

Local, distil-large-v3, CPU (27.99 seconds - 16.86 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your applications. If your application is error-sensitive and requires multilingual support, use Whisper-Large V3-3. If your application is less sensitive to errors and requires English-only, use Distill Whisper-at-Large V3N. If your application requires multilingual support and you need the best price for performance, use Whisper Large V3 Turbo. The following table breaks down the metrics for each model. 

Local, distil-small.en, CPU (27.51 seconds - 5.43 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the tradeoffs between models to find the one most suitable for your applications. If your application is error sensitive and requires multilingual support, use Whisper Large V3. If your application is less sensitive to errors and requires English only, use to still whisper large V3N. If your application requires multilingual support and you need the best price for performance, use Whisper Large V3 turbo. The metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for the metrics for. 

(Model freaked out and started repeating itself)

Local, tiny.en, CPU (28.92 seconds - 1.33 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your applications. If your application is error sensitive and requires multi-lingual support, use Whisper Large B3. If your application is less sensitive to errors and requires English only, use Distil Whisper Large B3N. If your application requires multi-lingual support and you need the best price for performance, use Whisper Large B3 Turbo. The following table breaks down the metrics for each model. 

Local, Vosk Small En, CPU (28.14 seconds - 2.23 seconds)

have you more choices is great but let's try to avoid decision process by breaking down the tradeoffs between models to find the one most suitable for your applications if your application is era sensitive and requires multilingual support use whisper large be three if your application is less sensitive to errors and requires english only used to still whisper large be three and if you have occasional cars multilingual support and you need the best price for performance use whisper large be three turbo the following table breaks down the metrics for each model 

Local, tiny.en, CUDA (29.31 seconds - 0.54 seconds)

Having more choices is great, but let's try to avoid decision paralysis by breaking down the trade-offs between models to find the one most suitable for your applications. If your application is error sensitive and requires multi-lingual support, use Whisper Large B3. If your application is less sensitive to errors and requires English only, use Distill Whisper Large B3N. If your application requires multi-lingual support and you need the best price per performance, use Whisper Large B3 Turbo. The following table breaks down the metrics for each model.
</details>



### Combination with AutoHotKey

I personally use the following activation keyboard shortcuts within WhisperWriter:

- `ctrl+alt+numpad1`: Activate transcription mode
- `ctrl+alt+numpad2`: Activate LLM cleanup mode
- `ctrl+alt+numpad3`: Activate LLM instruction mode
- `ctrl+alt+numpad4`: Activate clipboard cleanup mode

These shortcuts are very uncommon in other apps. To make the first two easier to trigger, I created the following [AutoHotkey 2.0](https://www.autohotkey.com/) script. This maps my **right** `alt` key to `ctrl+alt+numpad1`, and maps `shift` + **right** `alt` to `ctrl+alt+numpad2`. 

```
#Requires AutoHotkey v2.0-a

; ------ WhisperWriter Hotkey ------
; This binds the right alt key on my keyboard to my custom set 
; control alt numpad1 activation key for whisper writer.

RAlt::
{
    SendEvent "{Ctrl down}{Alt down}{Numpad1 down}"
    KeyWait "RAlt"  ; Wait for key to be released
    SendEvent "{Numpad1 up}{Alt up}{Ctrl up}"
}

+RAlt::
{
    SendEvent "{Ctrl down}{Alt down}{Numpad2 down}"
    KeyWait "RAlt"  ; Wait for key to be released
    SendEvent "{Numpad2 up}{Alt up}{Ctrl up}"
}
```

## Known Issues

You can see all reported issues and their current status in our [Issue Tracker](https://github.com/savbell/whisper-writer/issues). If you encounter a problem, please [open a new issue](https://github.com/savbell/whisper-writer/issues/new) with a detailed description and reproduction steps, if possible.

## Roadmap
Below are features I am planning to add in the near future:
- [x] Restructuring configuration options to reduce redundancy
- [x] Update to use the latest version of the OpenAI API
- [x] Additional post-processing options:
  - [x] Simple word replacement (e.g. "gonna" -> "going to" or "smiley face" -> "😊")
  - [x] Using GPT for instructional post-processing
- [x] Updating GUI
- [ ] Creating standalone executable file

Below are features not currently planned:
- [ ] Pipelining audio files

Implemented features can be found in the [CHANGELOG](CHANGELOG.md).

## Contributing

Contributions are welcome! I created this project for my own personal use and didn't expect it to get much attention, so I haven't put much effort into testing or making it easy for others to contribute. If you have ideas or suggestions, feel free to [open a pull request](https://github.com/savbell/whisper-writer/pulls) or [create a new issue](https://github.com/savbell/whisper-writer/issues/new). I'll do my best to review and respond as time allows.

## Credits

- [OpenAI](https://openai.com/) for creating the Whisper model and providing the API. Plus [ChatGPT](https://chat.openai.com/), which was used to write a lot of the initial code for this project.
- [Guillaume Klein](https://github.com/guillaumekln) for creating the [faster-whisper Python package](https://github.com/SYSTRAN/faster-whisper).
- All of our [contributors](https://github.com/savbell/whisper-writer/graphs/contributors)!

## License

This project is licensed under the GNU General Public License. See the [LICENSE](LICENSE) file for details.
