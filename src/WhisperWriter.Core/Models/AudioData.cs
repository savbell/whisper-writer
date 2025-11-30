namespace WhisperWriter.Core.Models;

/// <summary>
/// Represents recorded audio data ready for transcription.
/// </summary>
public sealed class AudioData : IDisposable
{
    private bool _disposed;
    private MemoryStream? _stream;

    /// <summary>
    /// The audio data as a byte array in WAV format.
    /// </summary>
    public byte[] Data { get; }

    /// <summary>
    /// The sample rate of the audio.
    /// </summary>
    public int SampleRate { get; }

    /// <summary>
    /// The number of channels.
    /// </summary>
    public int Channels { get; }

    /// <summary>
    /// The duration of the audio in seconds.
    /// </summary>
    public double DurationSeconds { get; }

    public AudioData(byte[] data, int sampleRate, int channels, double durationSeconds)
    {
        Data = data;
        SampleRate = sampleRate;
        Channels = channels;
        DurationSeconds = durationSeconds;
    }

    /// <summary>
    /// Gets the audio data as a stream.
    /// </summary>
    public Stream GetStream()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _stream?.Dispose();
        _stream = new MemoryStream(Data);
        return _stream;
    }

    public void Dispose()
    {
        if (_disposed) return;
        _stream?.Dispose();
        _disposed = true;
    }
}
