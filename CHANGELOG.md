# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
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
