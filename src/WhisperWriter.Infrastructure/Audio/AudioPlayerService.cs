using Microsoft.Extensions.Logging;
using NAudio.Wave;
using WhisperWriter.Core.Interfaces;

namespace WhisperWriter.Infrastructure.Audio;

/// <summary>
/// Audio playback service using NAudio.
/// </summary>
public sealed class AudioPlayerService : IAudioPlayerService
{
    private readonly ILogger<AudioPlayerService> _logger;
    private WaveOutEvent? _waveOut;
    private AudioFileReader? _audioFileReader;
    private bool _disposed;

    public AudioPlayerService(ILogger<AudioPlayerService> logger)
    {
        _logger = logger;
    }

    public async Task PlayAsync(string filePath)
    {
        if (_disposed)
        {
            throw new ObjectDisposedException(nameof(AudioPlayerService));
        }

        if (!File.Exists(filePath))
        {
            _logger.LogWarning("Audio file not found: {FilePath}", filePath);
            return;
        }

        Stop();

        try
        {
            _audioFileReader = new AudioFileReader(filePath);
            _waveOut = new WaveOutEvent();
            _waveOut.Init(_audioFileReader);

            var completionSource = new TaskCompletionSource<bool>();
            _waveOut.PlaybackStopped += (_, _) => completionSource.TrySetResult(true);

            _waveOut.Play();
            await completionSource.Task;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error playing audio file: {FilePath}", filePath);
        }
        finally
        {
            Stop();
        }
    }

    public Task PlayCompletionSoundAsync()
    {
        // Try to find the beep sound in common locations
        var possiblePaths = new[]
        {
            Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Assets", "beep.wav"),
            Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "beep.wav"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "WhisperWriter", "beep.wav")
        };

        foreach (var path in possiblePaths)
        {
            if (File.Exists(path))
            {
                return PlayAsync(path);
            }
        }

        _logger.LogWarning("Completion sound file not found");
        return Task.CompletedTask;
    }

    public void Stop()
    {
        _waveOut?.Stop();
        _waveOut?.Dispose();
        _waveOut = null;

        _audioFileReader?.Dispose();
        _audioFileReader = null;
    }

    public void Dispose()
    {
        if (_disposed) return;
        Stop();
        _disposed = true;
    }
}
