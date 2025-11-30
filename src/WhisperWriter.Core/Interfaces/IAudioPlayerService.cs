namespace WhisperWriter.Core.Interfaces;

/// <summary>
/// Interface for audio playback services.
/// </summary>
public interface IAudioPlayerService : IDisposable
{
    /// <summary>
    /// Plays a sound file.
    /// </summary>
    /// <param name="filePath">Path to the audio file.</param>
    Task PlayAsync(string filePath);

    /// <summary>
    /// Plays the completion beep sound.
    /// </summary>
    Task PlayCompletionSoundAsync();

    /// <summary>
    /// Stops any currently playing audio.
    /// </summary>
    void Stop();
}
