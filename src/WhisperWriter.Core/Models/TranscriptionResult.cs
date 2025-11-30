namespace WhisperWriter.Core.Models;

/// <summary>
/// Represents the result of a transcription operation.
/// </summary>
public sealed record TranscriptionResult
{
    /// <summary>
    /// The transcribed text.
    /// </summary>
    public string Text { get; init; } = string.Empty;

    /// <summary>
    /// The detected language code.
    /// </summary>
    public string? Language { get; init; }

    /// <summary>
    /// The duration of the audio in seconds.
    /// </summary>
    public double? Duration { get; init; }

    /// <summary>
    /// Whether the transcription was successful.
    /// </summary>
    public bool Success { get; init; }

    /// <summary>
    /// Error message if the transcription failed.
    /// </summary>
    public string? ErrorMessage { get; init; }

    /// <summary>
    /// Creates a successful result.
    /// </summary>
    public static TranscriptionResult Successful(string text, string? language = null, double? duration = null)
    {
        return new TranscriptionResult
        {
            Text = text,
            Language = language,
            Duration = duration,
            Success = true
        };
    }

    /// <summary>
    /// Creates a failed result.
    /// </summary>
    public static TranscriptionResult Failed(string errorMessage)
    {
        return new TranscriptionResult
        {
            Success = false,
            ErrorMessage = errorMessage
        };
    }
}
