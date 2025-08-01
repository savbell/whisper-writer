# WhisperWit

A modern, intelligent speech-to-text application powered by OpenAI's Whisper and GPT models.

## Recent Updates

- **Improved Language Detection**: Enhanced automatic language detection using Whisper's native capabilities
- **Better Microphone Handling**: Added support for slower microphones with improved audio buffering
- **Faster Response Time**: Optimized recording stop mechanism for quicker response
- **Enhanced UI**: Improved metrics display with cleaner visualization
- **Performance Improvements**: Reduced VAD aggressiveness for better speech detection

## Features

- Real-time speech transcription with improved response time
- Word-by-word live display with clean metrics visualization
- Robust multi-language support with native Whisper language detection
- GPT-powered text enhancement with language-specific handling
- Detailed cost tracking and usage metrics
- Customizable keyboard shortcuts
- Dark mode interface
- Local or API-based transcription
- Optimized microphone handling for various hardware

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whisper-writer-v2.git
cd whisper-writer-v2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key (if using API mode):
   - Create a `.env` file in the project root
   - Add your API key: `OPENAI_API_KEY=your-key-here`

## Usage

1. Start WhisperWit:
```bash
python run.py
```

2. Press `Ctrl+Shift+Space` (default) to start recording
3. Speak clearly into your microphone
4. Release the key combination to stop recording (now with faster response)
5. Watch as your speech is transcribed in real-time

## Configuration

WhisperWit can be configured through the settings window:

- Choose between local or API-based transcription
- Language detection is now automatic and more accurate
- Adjust recording settings for your microphone
- Customize keyboard shortcuts
- Configure post-processing options
- Fine-tune voice activity detection settings

### Recording Modes

- **Hold to Record**: Press and hold for quick recordings
- **Press to Toggle**: Click once to start, once to stop
- **Voice Activity**: Automatically stops after speech ends

### Performance Tips

- For slower microphones, the system now automatically adjusts buffering
- Voice detection has been optimized for better accuracy
- Quick response time when stopping recording
- Automatic language detection works best with clear speech

## Requirements

- Python 3.8 or higher
- FFmpeg
- PyQt5
- OpenAI API key (for API mode)
- CUDA-capable GPU (optional, for faster local processing)

## Technical Details

- Improved voice activity detection (VAD) with optimized parameters
- Enhanced audio buffer management for better microphone support
- Native Whisper language detection integration
- Responsive recording controls with 10ms polling
- Real-time metrics display with clean visualization

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Known Issues

- Some microphones may need additional configuration for optimal performance
- Language detection may require clear speech for best results
