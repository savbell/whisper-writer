# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.1] - 2025-02-21

All changes in this release are from [Thomas Frank's](https://github.com/TomFrankly) fork of the project.

### Added
- Support for newer Whisper models, such as distil-large-v3 and large-v3-turbo
- Support for Vosk models
- Support for additional transcription APIs and models:
  - Deepgram (nova-3, nova-2)
  - Groq (whisper-large-v3-turbo, distil-whisper-large-v3-en, whisper-large-v3)
- LLM Cleanup and LLM Instruction modes
  - Two new activation modes, which will each send the transcript to a chosen LLM provider/model with custom system instructions.
  - Ideal use: Use one as a "cleanup" mode, and the other as an "instruction" mode.
  - In addition to system instructions in the settings, you can add a text file and have its content appeneded as additional instructions.
- LLM model providers
  - OpenAI (ChatGPT)
  - Anthropic (Claude)
  - Google (Gemini)
  - Groq (all models)
  - Ollama (local LLM processing - I recommend "airat/karen-the-editor-v2-strict" for cleanup and "llama3.2" for instruction)
- Text (Clipboard) Cleanup Feature
  - Another activation key that will send the current clipboard text to a LLM provider/model with custom system instructions.
  - Ideal use: Use this to clean up text that's already been printed into the current application.
- Find and Replace Feature
  - Set a TXT or JSON file where you can set your own custom find and replace values.
  - Use a TXT file for simple find and replace operations. Each line should have a comma separated find and replace value, e.g. "find,replace".
  - Use a JSON file to get regex support and the ability to do text transformation on regex capture groups (see examples directory).
- More graceful degradation for lower-powered computers
  - If you don't have an NVIDIA GPU or don't want to install CUDA tools, you can use your CPU with smaller models, or use API providers for transcription.
- Clipboard Input and Threshold
  - If the transcript contains more characters than the Clipboard Threshold, it will be pasted into the current application. This will replace the default behavior of simulating keyboard input, which can be unreliable.
- Setting to pause currently playing audio during recording

### Changed
- Updated Python support to 3.12
- Updated dependencies
- Updated sound device property with dropdown, showing available input devices
- Modernized build system using hatchling
- Clicking "X" to exit Settings no longer closes the app
- Increased the default font size in Settings, added scrollable sections for longer tabs

### Fixed
- Fixed bug that would activate recording when only modifier keys were pressed
- Fixed bug that didn't allow for non-Space keys to be used when setting hotkeys

### Security
- Switched to using keyring to store API keys
- Added an explicit "Continuous API" checkbox in recording settings. Must be checked to use Continuous mode while using any remote API.
- Added a "Continuous Timeout" setting in recording settings. After this many seconds of silence, continuous mode will automatically deactivate.
- Set Recording status window to pulse when continuous mode is activated and a remote API is being used.

## [Previous Unreleased Changes by savbell and other contributors]
### Added
- New settings window to configure WhisperWriter.
- New main window to either start the keyboard listener or open the settings window.
- New continuous recording mode ([Issue #40](https://github.com/savbell/whisper-writer/issues/40)).
- New option to play a sound when transcription finishes ([Issue #40](https://github.com/savbell/whisper-writer/issues/40)).

### Changed
- Migrated status window from using `tkinter` to `PyQt5`.
- Migrated from using JSON to using YAML to store configuration settings.
- Upgraded to latest versions of `openai` and `faster-whisper`, including support for local API ([Issue #32](https://github.com/savbell/whisper-writer/issues/32)).

### Removed
- No longer using `keyboard` package to listen for key presses.

## [1.0.1] - 2024-01-28
### Added
- New message to identify whether Whisper was being called using the API or running locally.
- Additional hold-to-talk ([PR #28](https://github.com/savbell/whisper-writer/pull/28)) and press-to-toggle recording methods ([Issue #21](https://github.com/savbell/whisper-writer/issues/21)).
- New configuration options to:
  - Choose recording method (defaulting to voice activity detection).
  - Choose which sound device and sample rate to use.
  - Hide the status window ([PR #28](https://github.com/savbell/whisper-writer/pull/28)).

### Changed
- Migrated from `whisper` to `faster-whisper` ([Issue #11](https://github.com/savbell/whisper-writer/issues/11)).
- Migrated from `pyautogui` to `pynput` ([PR #10](https://github.com/savbell/whisper-writer/pull/10)).
- Migrated from `webrtcvad` to `webrtcvad-wheels` ([PR #17](https://github.com/savbell/whisper-writer/pull/17)).
- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.
- Changed to using a local model rather than the API by default.
- Revamped README.md, including new Roadmap, Contributing, and Credits sections.

### Fixed
- Local model is now only loaded once at start-up, rather than every time the activation key combo was pressed.
- Default configuration now auto-chooses compute type for the local model to avoid warnings.
- Graceful degradation to CPU if CUDA isn't available ([PR #30](https://github.com/savbell/whisper-writer/pull/30)).
- Removed long prefix of spaces in transcription ([PR #19](https://github.com/savbell/whisper-writer/pull/19)).

## [1.0.0] - 2023-05-29
### Added
- Initial release of WhisperWriter.
- Added CHANGELOG.md.
- Added Versioning and Known Issues to README.md.

### Changed
- Updated Whisper Python package; the local model is now compatible with Python 3.11.

[Unreleased]: https://github.com/savbell/whisper-writer/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/savbell/whisper-writer/releases/tag/v1.0.0...v1.0.1
[1.0.0]: https://github.com/savbell/whisper-writer/releases/tag/v1.0.0