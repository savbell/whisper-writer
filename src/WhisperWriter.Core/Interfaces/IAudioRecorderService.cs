using WhisperWriter.Core.Models;

namespace WhisperWriter.Core.Interfaces;

/// <summary>
/// Interface for audio recording services.
/// </summary>
public interface IAudioRecorderService : IDisposable
{
    /// <summary>
    /// Event raised when audio data is available.
    /// </summary>
    event EventHandler<AudioDataEventArgs>? AudioDataAvailable;

    /// <summary>
    /// Event raised when voice activity is detected.
    /// </summary>
    event EventHandler<VoiceActivityEventArgs>? VoiceActivityChanged;

    /// <summary>
    /// Gets available audio input devices.
    /// </summary>
    IReadOnlyList<AudioDevice> GetAvailableDevices();

    /// <summary>
    /// Starts recording audio.
    /// </summary>
    /// <param name="deviceIndex">The device index (-1 for default).</param>
    void StartRecording(int deviceIndex = -1);

    /// <summary>
    /// Stops recording and returns the recorded audio.
    /// </summary>
    /// <returns>The recorded audio data.</returns>
    AudioData StopRecording();

    /// <summary>
    /// Whether the recorder is currently recording.
    /// </summary>
    bool IsRecording { get; }
}

/// <summary>
/// Event args for audio data events.
/// </summary>
public sealed class AudioDataEventArgs : EventArgs
{
    public byte[] Data { get; }
    public int BytesRecorded { get; }

    public AudioDataEventArgs(byte[] data, int bytesRecorded)
    {
        Data = data;
        BytesRecorded = bytesRecorded;
    }
}

/// <summary>
/// Event args for voice activity events.
/// </summary>
public sealed class VoiceActivityEventArgs : EventArgs
{
    public bool IsSpeaking { get; }
    public TimeSpan SilenceDuration { get; }

    public VoiceActivityEventArgs(bool isSpeaking, TimeSpan silenceDuration = default)
    {
        IsSpeaking = isSpeaking;
        SilenceDuration = silenceDuration;
    }
}
