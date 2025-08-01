# Installing WhisperWit Chrome Extension (Development)

## Quick Install
1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the `whisperwit-extension` folder

## First-Time Setup
1. Click the WhisperWit icon in Chrome toolbar
2. Enter your OpenAI API key
3. Select your preferred language
4. Click "Save Settings"
5. When recording for the first time:
   - Click the Record button
   - Chrome will show a microphone permission prompt
   - Click "Allow" to grant microphone access
   - If you don't see the prompt, click the camera/microphone icon in the address bar

Note: The extension needs microphone access to record audio. You can:
- Manage permissions in Chrome's site settings
- Click the lock/info icon in the address bar
- Go to chrome://settings/content/microphone

## Testing
1. Go to any website with a text field
2. Click into the text field
3. Click the WhisperWit icon
4. Click "Record" and speak
5. Click "Stop" when done
6. Your text should appear in the field

## Troubleshooting

### Recording Issues
- Make sure your microphone is working in Chrome settings
- Allow microphone access when prompted by Chrome
- Try refreshing the page if recording won't start
- Check Chrome's audio input settings

### API Issues
- Verify your OpenAI API key is correct
- Check your API key has access to Whisper API
- Make sure you have sufficient API credits
- Check your internet connection

### Text Insertion Issues
- Click into the text field before stopping recording
- Refresh the page if text insertion fails
- Try a different text field if one doesn't work
- Make sure the page allows text input

### General Issues
- Reload the extension from chrome://extensions/
- Check Chrome console for error messages
- Make sure you're on a supported website
- Try disabling other extensions temporarily

## Development
- Edit files in the extension folder
- Click the refresh icon on `chrome://extensions/`
- Changes will be applied immediately
- Check Chrome DevTools for errors (right-click extension icon -> Inspect)