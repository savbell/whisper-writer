# <img src="./assets/ww-logo.png" alt="WhisperWriter icon" width="25" height="25"> WhisperWriter

![version](https://img.shields.io/badge/version-2.0.0-blue)
![.NET](https://img.shields.io/badge/.NET-8.0-purple)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<p align="center">
    <img src="./assets/ww-demo-image-02.gif" alt="WhisperWriter demo gif" width="340" height="136">
</p>

**v2.0.0 - .NET Core Rewrite**: WhisperWriter has been completely rewritten in .NET 8 with a modern architecture following SOLID principles. This version features a cross-platform UI using Avalonia, improved performance, and automatic release builds via GitHub Actions.

WhisperWriter is a speech-to-text application that uses [OpenAI's Whisper model](https://openai.com/research/whisper) to automatically transcribe recordings from your microphone and type the text into the active window.

Once started, the application runs in the background and waits for a keyboard shortcut to be pressed (`Ctrl+Shift+Space` by default). When the shortcut is pressed, the app starts recording from your microphone. There are four recording modes to choose from:

- **Continuous** (default): Recording stops after a pause in your speech, transcribes the text, and automatically starts recording again. Press the keyboard shortcut again to stop.
- **Voice Activity Detection**: Recording stops after a pause in your speech. Press the shortcut again to start a new recording.
- **Press to Toggle**: Recording stops when the keyboard shortcut is pressed again.
- **Hold to Record**: Recording continues while the keyboard shortcut is held down.

## Features

- Cross-platform support (Windows, Linux, macOS)
- OpenAI Whisper API integration using Flurl
- Modern Avalonia UI with dark theme
- YAML-based configuration
- Voice activity detection
- Multiple recording modes
- Post-processing options (remove periods, add spaces, lowercase)
- System tray integration
- Automatic release builds via GitHub Actions

## Architecture

This project follows SOLID principles with a clean architecture:

```
WhisperWriter.sln
├── WhisperWriter.Core          # Domain models, interfaces, enums
├── WhisperWriter.Infrastructure # External service implementations
│   ├── Audio                   # NAudio-based recording
│   ├── Configuration           # YAML configuration service
│   ├── Input                   # SharpHook input simulation
│   ├── Keyboard               # SharpHook keyboard listener
│   └── Transcription          # OpenAI API via Flurl
├── WhisperWriter.Application   # Application services, DI setup
├── WhisperWriter.UI           # Avalonia views and view models
└── WhisperWriter              # Entry point, app configuration
```

## Getting Started

### Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) or later
- An OpenAI API key (for API-based transcription)

### Installation

#### Option 1: Download Pre-built Release

Download the latest release for your platform from the [Releases](https://github.com/savbell/whisper-writer/releases) page.

#### Option 2: Build from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/savbell/whisper-writer
   cd whisper-writer
   ```

2. Build the solution:
   ```bash
   dotnet build --configuration Release
   ```

3. Run the application:
   ```bash
   dotnet run --project src/WhisperWriter
   ```

### Configuration

On first run, a Settings window will appear. Configure your preferences:

#### Model Options
- **Use API**: Toggle between OpenAI API or local model (API only in .NET version)
- **API Key**: Your OpenAI API key (can also be set via `OPENAI_API_KEY` environment variable)
- **Base URL**: API endpoint (default: `https://api.openai.com/v1`)
- **Model**: Whisper model to use (default: `whisper-1`)
- **Language**: ISO-639-1 language code (leave empty for auto-detect)
- **Temperature**: Controls randomness (0.0 - 1.0)
- **Initial Prompt**: Conditioning text for transcription

#### Recording Options
- **Activation Key**: Keyboard shortcut (default: `ctrl+shift+space`)
- **Recording Mode**: Choose from Continuous, Voice Activity Detection, Press to Toggle, or Hold to Record
- **Sound Device**: Select audio input device
- **Sample Rate**: Recording sample rate in Hz (default: 16000)
- **Silence Duration**: Pause duration before stopping (default: 900ms)
- **Min Duration**: Minimum recording length (default: 100ms)

#### Post-Processing Options
- **Remove Trailing Period**: Strip periods from end of transcriptions
- **Add Trailing Space**: Add space after transcriptions
- **Remove Capitalization**: Convert to lowercase
- **Key Press Delay**: Delay between typed characters (default: 0.005s)

#### Miscellaneous Options
- **Print to Terminal**: Output transcriptions to console
- **Hide Status Window**: Hide the floating status indicator
- **Play Sound on Completion**: Audio feedback when done
- **Start Minimized**: Start in system tray

Configuration is stored in `~/.config/WhisperWriter/config.yaml` (Linux/macOS) or `%APPDATA%\WhisperWriter\config.yaml` (Windows).

## Development

### Building

```bash
# Restore dependencies
dotnet restore

# Build
dotnet build

# Run tests
dotnet test

# Publish for specific platform
dotnet publish src/WhisperWriter -c Release -r win-x64 --self-contained
dotnet publish src/WhisperWriter -c Release -r linux-x64 --self-contained
dotnet publish src/WhisperWriter -c Release -r osx-x64 --self-contained
```

### Project Structure

| Project | Purpose |
|---------|---------|
| `WhisperWriter.Core` | Domain models, interfaces, and enums |
| `WhisperWriter.Infrastructure` | External service implementations |
| `WhisperWriter.Application` | Application orchestration and DI |
| `WhisperWriter.UI` | Avalonia views and view models |
| `WhisperWriter` | Entry point and configuration |

### Key Technologies

- **.NET 8**: Modern cross-platform runtime
- **Avalonia**: Cross-platform UI framework
- **Flurl**: Fluent HTTP client for API calls
- **NAudio**: Audio recording and playback
- **SharpHook**: Global keyboard hooks
- **YamlDotNet**: YAML configuration
- **CommunityToolkit.Mvvm**: MVVM framework

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Credits

- [OpenAI](https://openai.com/) for the Whisper model and API
- Original Python implementation by [savbell](https://github.com/savbell)
- [Avalonia UI](https://avaloniaui.net/) for the cross-platform UI framework

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
