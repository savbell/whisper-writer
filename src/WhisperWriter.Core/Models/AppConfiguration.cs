using WhisperWriter.Core.Enums;

namespace WhisperWriter.Core.Models;

/// <summary>
/// Root configuration for the application.
/// </summary>
public sealed class AppConfiguration
{
    public ModelOptions Model { get; set; } = new();
    public RecordingOptions Recording { get; set; } = new();
    public PostProcessingOptions PostProcessing { get; set; } = new();
    public MiscellaneousOptions Misc { get; set; } = new();
}

/// <summary>
/// Configuration for transcription model settings.
/// </summary>
public sealed class ModelOptions
{
    /// <summary>
    /// Whether to use the API instead of a local model.
    /// </summary>
    public bool UseApi { get; set; } = true;

    /// <summary>
    /// Common settings for both API and local models.
    /// </summary>
    public CommonModelSettings Common { get; set; } = new();

    /// <summary>
    /// API-specific settings.
    /// </summary>
    public ApiModelSettings Api { get; set; } = new();

    /// <summary>
    /// Local model-specific settings.
    /// </summary>
    public LocalModelSettings Local { get; set; } = new();
}

/// <summary>
/// Common settings shared between API and local models.
/// </summary>
public sealed class CommonModelSettings
{
    /// <summary>
    /// Language code (ISO-639-1) for transcription.
    /// </summary>
    public string? Language { get; set; }

    /// <summary>
    /// Temperature for transcription (0.0 to 1.0).
    /// </summary>
    public double Temperature { get; set; } = 0.0;

    /// <summary>
    /// Initial prompt to condition the transcription.
    /// </summary>
    public string? InitialPrompt { get; set; }
}

/// <summary>
/// API-specific model settings.
/// </summary>
public sealed class ApiModelSettings
{
    /// <summary>
    /// The model to use for transcription.
    /// </summary>
    public string Model { get; set; } = "whisper-1";

    /// <summary>
    /// The base URL for the API.
    /// </summary>
    public string BaseUrl { get; set; } = "https://api.openai.com/v1";

    /// <summary>
    /// The API key for authentication.
    /// </summary>
    public string? ApiKey { get; set; }
}

/// <summary>
/// Local model-specific settings.
/// </summary>
public sealed class LocalModelSettings
{
    /// <summary>
    /// The model size to use (tiny, small, base, medium, large).
    /// </summary>
    public string Model { get; set; } = "base";

    /// <summary>
    /// The device to use (auto, cuda, cpu).
    /// </summary>
    public string Device { get; set; } = "auto";

    /// <summary>
    /// The compute type for quantization.
    /// </summary>
    public string ComputeType { get; set; } = "default";

    /// <summary>
    /// Whether to condition on previous text.
    /// </summary>
    public bool ConditionOnPreviousText { get; set; } = true;

    /// <summary>
    /// Whether to use VAD filter.
    /// </summary>
    public bool VadFilter { get; set; } = false;

    /// <summary>
    /// Custom path to the model.
    /// </summary>
    public string? ModelPath { get; set; }
}

/// <summary>
/// Recording-related settings.
/// </summary>
public sealed class RecordingOptions
{
    /// <summary>
    /// The activation key combination.
    /// </summary>
    public string ActivationKey { get; set; } = "ctrl+shift+space";

    /// <summary>
    /// The recording mode.
    /// </summary>
    public RecordingMode RecordingMode { get; set; } = RecordingMode.VoiceActivityDetection;

    /// <summary>
    /// The audio device index to use (-1 for default).
    /// </summary>
    public int SoundDevice { get; set; } = -1;

    /// <summary>
    /// The sample rate in Hz.
    /// </summary>
    public int SampleRate { get; set; } = 16000;

    /// <summary>
    /// Duration of silence before stopping recording (in milliseconds).
    /// </summary>
    public int SilenceDuration { get; set; } = 900;

    /// <summary>
    /// Minimum recording duration in milliseconds.
    /// </summary>
    public int MinDuration { get; set; } = 100;
}

/// <summary>
/// Post-processing settings for transcribed text.
/// </summary>
public sealed class PostProcessingOptions
{
    /// <summary>
    /// Delay between key presses when typing (in seconds).
    /// </summary>
    public double WritingKeyPressDelay { get; set; } = 0.005;

    /// <summary>
    /// Whether to remove trailing periods from transcriptions.
    /// </summary>
    public bool RemoveTrailingPeriod { get; set; } = false;

    /// <summary>
    /// Whether to add a trailing space after transcriptions.
    /// </summary>
    public bool AddTrailingSpace { get; set; } = true;

    /// <summary>
    /// Whether to convert transcriptions to lowercase.
    /// </summary>
    public bool RemoveCapitalization { get; set; } = false;

    /// <summary>
    /// The input method for typing.
    /// </summary>
    public InputMethod InputMethod { get; set; } = InputMethod.SharpHook;
}

/// <summary>
/// Miscellaneous settings.
/// </summary>
public sealed class MiscellaneousOptions
{
    /// <summary>
    /// Whether to print transcriptions to the terminal.
    /// </summary>
    public bool PrintToTerminal { get; set; } = true;

    /// <summary>
    /// Whether to hide the status window.
    /// </summary>
    public bool HideStatusWindow { get; set; } = false;

    /// <summary>
    /// Whether to play a sound on completion.
    /// </summary>
    public bool NoiseOnCompletion { get; set; } = false;

    /// <summary>
    /// Whether to start minimized to tray.
    /// </summary>
    public bool StartMinimized { get; set; } = false;
}
