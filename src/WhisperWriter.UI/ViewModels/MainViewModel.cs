using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using WhisperWriter.Application.Services;
using WhisperWriter.Core.Enums;

namespace WhisperWriter.UI.ViewModels;

/// <summary>
/// View model for the main window.
/// </summary>
public partial class MainViewModel : ViewModelBase
{
    private readonly WhisperWriterService _whisperService;

    [ObservableProperty]
    private string _statusText = "Ready";

    [ObservableProperty]
    private string _statusIcon = "Idle";

    [ObservableProperty]
    private bool _isRecording;

    [ObservableProperty]
    private bool _isTranscribing;

    [ObservableProperty]
    private string _lastTranscription = string.Empty;

    [ObservableProperty]
    private string _activationKeyDisplay = "Ctrl+Shift+Space";

    public MainViewModel(WhisperWriterService whisperService)
    {
        _whisperService = whisperService;

        _whisperService.StateChanged += OnStateChanged;
        _whisperService.TranscriptionCompleted += OnTranscriptionCompleted;
        _whisperService.ErrorOccurred += OnErrorOccurred;
    }

    private void OnStateChanged(object? sender, RecordingStateChangedEventArgs e)
    {
        switch (e.NewState)
        {
            case RecordingState.Idle:
                StatusText = "Ready";
                StatusIcon = "Idle";
                IsRecording = false;
                IsTranscribing = false;
                break;
            case RecordingState.Recording:
                StatusText = "Recording...";
                StatusIcon = "Recording";
                IsRecording = true;
                IsTranscribing = false;
                break;
            case RecordingState.Transcribing:
                StatusText = "Transcribing...";
                StatusIcon = "Transcribing";
                IsRecording = false;
                IsTranscribing = true;
                break;
            case RecordingState.Typing:
                StatusText = "Typing...";
                StatusIcon = "Typing";
                IsRecording = false;
                IsTranscribing = false;
                break;
        }
    }

    private void OnTranscriptionCompleted(object? sender, TranscriptionCompletedEventArgs e)
    {
        LastTranscription = e.Text;
    }

    private void OnErrorOccurred(object? sender, ErrorOccurredEventArgs e)
    {
        StatusText = $"Error: {e.Message}";
        StatusIcon = "Error";
    }

    [RelayCommand]
    private void OpenSettings()
    {
        // Will be implemented by the view
    }

    [RelayCommand]
    private void Exit()
    {
        Environment.Exit(0);
    }
}
