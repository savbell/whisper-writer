using Microsoft.Extensions.Logging;
using NAudio.Wave;
using WhisperWriter.Core.Interfaces;
using WhisperWriter.Core.Models;

namespace WhisperWriter.Infrastructure.Audio;

/// <summary>
/// Audio recording service using NAudio.
/// </summary>
public sealed class NAudioRecorderService : IAudioRecorderService
{
    private readonly ILogger<NAudioRecorderService> _logger;
    private readonly IConfigurationService _configService;
    private WaveInEvent? _waveIn;
    private MemoryStream? _recordingStream;
    private WaveFileWriter? _waveWriter;
    private DateTime _recordingStartTime;
    private bool _disposed;

    // Voice activity detection
    private readonly object _vadLock = new();
    private DateTime _lastVoiceActivity;
    private bool _isSpeaking;
    private const double VadThreshold = 0.01; // RMS threshold for voice detection

    public event EventHandler<AudioDataEventArgs>? AudioDataAvailable;
    public event EventHandler<VoiceActivityEventArgs>? VoiceActivityChanged;

    public bool IsRecording => _waveIn != null;

    public NAudioRecorderService(
        ILogger<NAudioRecorderService> logger,
        IConfigurationService configService)
    {
        _logger = logger;
        _configService = configService;
    }

    public IReadOnlyList<AudioDevice> GetAvailableDevices()
    {
        var devices = new List<AudioDevice>();

        for (var i = 0; i < WaveInEvent.DeviceCount; i++)
        {
            var capabilities = WaveInEvent.GetCapabilities(i);
            devices.Add(new AudioDevice
            {
                DeviceIndex = i,
                Name = capabilities.ProductName,
                Channels = capabilities.Channels,
                IsDefault = i == 0
            });
        }

        return devices;
    }

    public void StartRecording(int deviceIndex = -1)
    {
        if (_disposed)
        {
            throw new ObjectDisposedException(nameof(NAudioRecorderService));
        }

        if (_waveIn != null)
        {
            _logger.LogWarning("Recording already in progress");
            return;
        }

        var config = _configService.Configuration.Recording;

        _recordingStream = new MemoryStream();
        _waveIn = new WaveInEvent
        {
            DeviceNumber = deviceIndex >= 0 ? deviceIndex : config.SoundDevice,
            WaveFormat = new WaveFormat(config.SampleRate, 16, 1)
        };

        _waveWriter = new WaveFileWriter(_recordingStream, _waveIn.WaveFormat);
        _waveIn.DataAvailable += OnDataAvailable;
        _waveIn.RecordingStopped += OnRecordingStopped;

        _recordingStartTime = DateTime.UtcNow;
        _lastVoiceActivity = DateTime.UtcNow;
        _isSpeaking = false;

        _waveIn.StartRecording();
        _logger.LogInformation("Recording started on device {Device} at {SampleRate}Hz",
            _waveIn.DeviceNumber, config.SampleRate);
    }

    public AudioData StopRecording()
    {
        if (_waveIn == null || _recordingStream == null || _waveWriter == null)
        {
            throw new InvalidOperationException("Not currently recording");
        }

        _waveIn.StopRecording();
        _waveWriter.Flush();

        var duration = (DateTime.UtcNow - _recordingStartTime).TotalSeconds;
        var sampleRate = _waveIn.WaveFormat.SampleRate;
        var channels = _waveIn.WaveFormat.Channels;

        // Get the WAV data
        var data = _recordingStream.ToArray();

        // Cleanup
        _waveWriter.Dispose();
        _waveWriter = null;
        _recordingStream.Dispose();
        _recordingStream = null;
        _waveIn.Dispose();
        _waveIn = null;

        _logger.LogInformation("Recording stopped. Duration: {Duration:F2}s, Size: {Size} bytes",
            duration, data.Length);

        return new AudioData(data, sampleRate, channels, duration);
    }

    private void OnDataAvailable(object? sender, WaveInEventArgs e)
    {
        if (_waveWriter == null) return;

        _waveWriter.Write(e.Buffer, 0, e.BytesRecorded);

        // Calculate RMS for voice activity detection
        var rms = CalculateRms(e.Buffer, e.BytesRecorded);
        var nowSpeaking = rms > VadThreshold;

        lock (_vadLock)
        {
            if (nowSpeaking)
            {
                _lastVoiceActivity = DateTime.UtcNow;
                if (!_isSpeaking)
                {
                    _isSpeaking = true;
                    VoiceActivityChanged?.Invoke(this, new VoiceActivityEventArgs(true));
                }
            }
            else if (_isSpeaking)
            {
                var silenceDuration = DateTime.UtcNow - _lastVoiceActivity;
                var silenceThreshold = TimeSpan.FromMilliseconds(
                    _configService.Configuration.Recording.SilenceDuration);

                if (silenceDuration > silenceThreshold)
                {
                    _isSpeaking = false;
                    VoiceActivityChanged?.Invoke(this, new VoiceActivityEventArgs(false, silenceDuration));
                }
            }
        }

        AudioDataAvailable?.Invoke(this, new AudioDataEventArgs(e.Buffer, e.BytesRecorded));
    }

    private void OnRecordingStopped(object? sender, StoppedEventArgs e)
    {
        if (e.Exception != null)
        {
            _logger.LogError(e.Exception, "Recording stopped due to error");
        }
    }

    private static double CalculateRms(byte[] buffer, int bytesRecorded)
    {
        // Convert bytes to 16-bit samples and calculate RMS
        var sampleCount = bytesRecorded / 2;
        double sum = 0;

        for (var i = 0; i < bytesRecorded; i += 2)
        {
            var sample = BitConverter.ToInt16(buffer, i);
            var normalized = sample / 32768.0;
            sum += normalized * normalized;
        }

        return Math.Sqrt(sum / sampleCount);
    }

    public void Dispose()
    {
        if (_disposed) return;

        _waveIn?.StopRecording();
        _waveWriter?.Dispose();
        _recordingStream?.Dispose();
        _waveIn?.Dispose();

        _disposed = true;
    }
}
