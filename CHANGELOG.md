# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Added
- New message to identify whether Whisper was being called using the API or running locally.
- New configuration options to choose which sound device and sample rate to use.
- Push to talk
- New configuration option to enable/disable push to talk
- New configuration option to hide status window

### Changed
- Migrated from `whisper` to `faster-whisper` (Issue #11).
- Migrated from `pyautogui` to `pynput` (PR #10).
- Migrated from `webrtcvad` to `webrtcvad-wheels` (PR #17).
- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.
- Changed to using a local model rather than the API by default.
- Revamped README.md, including new Roadmap, Contributing, and Credits sections.

### Fixed
- Local model is now only loaded once at start-up, rather than every time the activation key combo was pressed.
- Default configuration now auto-chooses compute type for the local model to avoid warnings.

## [1.0.0] - 2023-05-29
### Added
- Initial release of WhisperWriter.
- Added CHANGELOG.md.
- Added Versioning and Known Issues to README.md.

### Changed
- Updated Whisper Python package; the local model is now compatible with Python 3.11.

[Unreleased]: https://github.com/savbell/whisper-writer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/savbell/whisper-writer/releases/tag/v1.0.0
