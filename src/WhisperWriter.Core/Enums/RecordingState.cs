namespace WhisperWriter.Core.Enums;

/// <summary>
/// Represents the current state of the recording process.
/// </summary>
public enum RecordingState
{
    /// <summary>
    /// Not currently recording or processing.
    /// </summary>
    Idle,

    /// <summary>
    /// Currently recording audio from the microphone.
    /// </summary>
    Recording,

    /// <summary>
    /// Processing/transcribing the recorded audio.
    /// </summary>
    Transcribing,

    /// <summary>
    /// Typing the transcribed text.
    /// </summary>
    Typing
}
