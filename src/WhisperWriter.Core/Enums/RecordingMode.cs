namespace WhisperWriter.Core.Enums;

/// <summary>
/// Defines the different recording modes for the application.
/// </summary>
public enum RecordingMode
{
    /// <summary>
    /// Continuously records and transcribes until the activation key is pressed again.
    /// Auto-restarts after each transcription.
    /// </summary>
    Continuous,

    /// <summary>
    /// Records until voice activity stops, then waits for the next key press.
    /// </summary>
    VoiceActivityDetection,

    /// <summary>
    /// Toggle recording on/off with each key press.
    /// </summary>
    PressToToggle,

    /// <summary>
    /// Record while the key is held down, stop when released.
    /// </summary>
    HoldToRecord
}
