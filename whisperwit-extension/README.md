# WhisperWit Chrome Extension

A simple Chrome extension for real-time speech-to-text in any text field.

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `whisperwit-extension` folder

## Setup

1. Click the WhisperWit icon in your Chrome toolbar
2. Enter your OpenAI API key in the settings
3. Select your preferred language
4. Click "Save Settings"

## Usage

1. Click into any text field where you want to insert text
2. Click the WhisperWit icon in your toolbar
3. Click "Record" and start speaking
4. Click "Stop" when done
5. Your transcribed text will appear in the text field

## Features

- Real-time speech-to-text
- Supports multiple languages
- Works in any text field
- Simple, clean interface
- Secure API key storage

## Development

The extension consists of:
- `popup/`: UI files
- `background.js`: Audio recording and API handling
- `content.js`: Text field integration
- `manifest.json`: Extension configuration

## Notes

- Requires an OpenAI API key
- Uses the Whisper API for transcription
- Internet connection required
- Microphone access needed