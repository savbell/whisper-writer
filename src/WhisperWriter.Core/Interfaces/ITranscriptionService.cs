using WhisperWriter.Core.Models;

namespace WhisperWriter.Core.Interfaces;

/// <summary>
/// Interface for transcription services (follows Interface Segregation Principle).
/// </summary>
public interface ITranscriptionService
{
    /// <summary>
    /// Transcribes audio data to text.
    /// </summary>
    /// <param name="audioData">The audio data to transcribe.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The transcription result.</returns>
    Task<TranscriptionResult> TranscribeAsync(AudioData audioData, CancellationToken cancellationToken = default);
}
