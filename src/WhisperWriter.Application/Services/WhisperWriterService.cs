using Microsoft.Extensions.Logging;
using WhisperWriter.Core.Enums;
using WhisperWriter.Core.Interfaces;
using WhisperWriter.Core.Models;

namespace WhisperWriter.Application.Services;

/// <summary>
/// Main orchestration service for WhisperWriter.
/// Coordinates recording, transcription, and text output.
/// </summary>
public sealed class WhisperWriterService : IDisposable
{
    private readonly ILogger<WhisperWriterService> _logger;
    private readonly IConfigurationService _configService;
    private readonly IAudioRecorderService _audioRecorder;
    private readonly ITranscriptionService _transcriptionService;
    private readonly IKeyboardListenerService _keyboardListener;
    private readonly IInputSimulatorService _inputSimulator;
    private readonly IAudioPlayerService _audioPlayer;
    private readonly ITextPostProcessor _textPostProcessor;

    private RecordingState _state = RecordingState.Idle;
    private CancellationTokenSource? _cancellationTokenSource;
    private bool _disposed;

    public event EventHandler<RecordingStateChangedEventArgs>? StateChanged;
    public event EventHandler<TranscriptionCompletedEventArgs>? TranscriptionCompleted;
    public event EventHandler<ErrorOccurredEventArgs>? ErrorOccurred;

    public RecordingState State
    {
        get => _state;
        private set
        {
            if (_state != value)
            {
                var oldState = _state;
                _state = value;
                StateChanged?.Invoke(this, new RecordingStateChangedEventArgs(oldState, value));
            }
        }
    }

    public WhisperWriterService(
        ILogger<WhisperWriterService> logger,
        IConfigurationService configService,
        IAudioRecorderService audioRecorder,
        ITranscriptionService transcriptionService,
        IKeyboardListenerService keyboardListener,
        IInputSimulatorService inputSimulator,
        IAudioPlayerService audioPlayer,
        ITextPostProcessor textPostProcessor)
    {
        _logger = logger;
        _configService = configService;
        _audioRecorder = audioRecorder;
        _transcriptionService = transcriptionService;
        _keyboardListener = keyboardListener;
        _inputSimulator = inputSimulator;
        _audioPlayer = audioPlayer;
        _textPostProcessor = textPostProcessor;

        // Wire up event handlers
        _keyboardListener.ActivationKeyPressed += OnActivationKeyPressed;
        _keyboardListener.ActivationKeyReleased += OnActivationKeyReleased;
        _audioRecorder.VoiceActivityChanged += OnVoiceActivityChanged;
    }

    public async Task InitializeAsync()
    {
        await _configService.LoadAsync();

        var config = _configService.Configuration;
        var hotKey = HotKey.Parse(config.Recording.ActivationKey);
        _keyboardListener.SetActivationKey(hotKey);

        _logger.LogInformation("WhisperWriter initialized with activation key: {HotKey}", hotKey);
    }

    public void Start()
    {
        _keyboardListener.Start();
        _logger.LogInformation("WhisperWriter service started");
    }

    public void Stop()
    {
        _keyboardListener.Stop();
        StopRecording();
        _logger.LogInformation("WhisperWriter service stopped");
    }

    private void OnActivationKeyPressed(object? sender, EventArgs e)
    {
        var config = _configService.Configuration;

        switch (config.Recording.RecordingMode)
        {
            case RecordingMode.Continuous:
            case RecordingMode.VoiceActivityDetection:
            case RecordingMode.PressToToggle:
                if (State == RecordingState.Idle)
                {
                    StartRecording();
                }
                else if (State == RecordingState.Recording)
                {
                    _ = StopAndTranscribeAsync();
                }
                break;

            case RecordingMode.HoldToRecord:
                if (State == RecordingState.Idle)
                {
                    StartRecording();
                }
                break;
        }
    }

    private void OnActivationKeyReleased(object? sender, EventArgs e)
    {
        var config = _configService.Configuration;

        if (config.Recording.RecordingMode == RecordingMode.HoldToRecord && State == RecordingState.Recording)
        {
            _ = StopAndTranscribeAsync();
        }
    }

    private void OnVoiceActivityChanged(object? sender, VoiceActivityEventArgs e)
    {
        var config = _configService.Configuration;

        if (!e.IsSpeaking && State == RecordingState.Recording)
        {
            switch (config.Recording.RecordingMode)
            {
                case RecordingMode.Continuous:
                case RecordingMode.VoiceActivityDetection:
                    // Check if silence duration exceeds threshold
                    if (e.SilenceDuration.TotalMilliseconds >= config.Recording.SilenceDuration)
                    {
                        _ = StopAndTranscribeAsync(
                            restartAfter: config.Recording.RecordingMode == RecordingMode.Continuous);
                    }
                    break;
            }
        }
    }

    private void StartRecording()
    {
        if (State != RecordingState.Idle) return;

        _cancellationTokenSource = new CancellationTokenSource();
        var config = _configService.Configuration;

        try
        {
            _audioRecorder.StartRecording(config.Recording.SoundDevice);
            State = RecordingState.Recording;
            _logger.LogInformation("Recording started");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to start recording");
            ErrorOccurred?.Invoke(this, new ErrorOccurredEventArgs("Failed to start recording", ex));
            State = RecordingState.Idle;
        }
    }

    private void StopRecording()
    {
        _cancellationTokenSource?.Cancel();
        _cancellationTokenSource?.Dispose();
        _cancellationTokenSource = null;

        if (_audioRecorder.IsRecording)
        {
            _audioRecorder.StopRecording();
        }

        State = RecordingState.Idle;
    }

    private async Task StopAndTranscribeAsync(bool restartAfter = false)
    {
        if (State != RecordingState.Recording) return;

        var config = _configService.Configuration;
        AudioData? audioData = null;

        try
        {
            audioData = _audioRecorder.StopRecording();
            State = RecordingState.Transcribing;

            // Check minimum duration
            if (audioData.DurationSeconds * 1000 < config.Recording.MinDuration)
            {
                _logger.LogDebug("Recording too short ({Duration}ms), discarding",
                    audioData.DurationSeconds * 1000);
                State = RecordingState.Idle;
                audioData.Dispose();

                if (restartAfter)
                {
                    StartRecording();
                }
                return;
            }

            _logger.LogInformation("Transcribing {Duration:F2}s of audio", audioData.DurationSeconds);

            var result = await _transcriptionService.TranscribeAsync(
                audioData,
                _cancellationTokenSource?.Token ?? CancellationToken.None);

            if (result.Success && !string.IsNullOrWhiteSpace(result.Text))
            {
                // Post-process the text
                var processedText = _textPostProcessor.Process(result.Text, config.PostProcessing);

                if (config.Misc.PrintToTerminal)
                {
                    Console.WriteLine($"Transcription: {processedText}");
                }

                // Type the text
                State = RecordingState.Typing;
                var delay = (int)(config.PostProcessing.WritingKeyPressDelay * 1000);
                await _inputSimulator.TypeTextAsync(processedText, delay);

                // Play completion sound
                if (config.Misc.NoiseOnCompletion)
                {
                    await _audioPlayer.PlayCompletionSoundAsync();
                }

                TranscriptionCompleted?.Invoke(this, new TranscriptionCompletedEventArgs(processedText, result));
            }
            else if (!result.Success)
            {
                _logger.LogWarning("Transcription failed: {Error}", result.ErrorMessage);
                ErrorOccurred?.Invoke(this, new ErrorOccurredEventArgs(
                    result.ErrorMessage ?? "Transcription failed", null));
            }
        }
        catch (OperationCanceledException)
        {
            _logger.LogDebug("Transcription cancelled");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during transcription");
            ErrorOccurred?.Invoke(this, new ErrorOccurredEventArgs("Transcription error", ex));
        }
        finally
        {
            audioData?.Dispose();
            State = RecordingState.Idle;

            if (restartAfter && !(_cancellationTokenSource?.IsCancellationRequested ?? true))
            {
                StartRecording();
            }
        }
    }

    public void Dispose()
    {
        if (_disposed) return;

        Stop();
        _keyboardListener.ActivationKeyPressed -= OnActivationKeyPressed;
        _keyboardListener.ActivationKeyReleased -= OnActivationKeyReleased;
        _audioRecorder.VoiceActivityChanged -= OnVoiceActivityChanged;

        _disposed = true;
    }
}

/// <summary>
/// Event args for state changes.
/// </summary>
public sealed class RecordingStateChangedEventArgs : EventArgs
{
    public RecordingState OldState { get; }
    public RecordingState NewState { get; }

    public RecordingStateChangedEventArgs(RecordingState oldState, RecordingState newState)
    {
        OldState = oldState;
        NewState = newState;
    }
}

/// <summary>
/// Event args for transcription completed.
/// </summary>
public sealed class TranscriptionCompletedEventArgs : EventArgs
{
    public string Text { get; }
    public TranscriptionResult Result { get; }

    public TranscriptionCompletedEventArgs(string text, TranscriptionResult result)
    {
        Text = text;
        Result = result;
    }
}

/// <summary>
/// Event args for errors.
/// </summary>
public sealed class ErrorOccurredEventArgs : EventArgs
{
    public string Message { get; }
    public Exception? Exception { get; }

    public ErrorOccurredEventArgs(string message, Exception? exception)
    {
        Message = message;
        Exception = exception;
    }
}
