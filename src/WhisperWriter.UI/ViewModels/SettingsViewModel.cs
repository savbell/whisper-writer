using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using WhisperWriter.Core.Enums;
using WhisperWriter.Core.Interfaces;
using WhisperWriter.Core.Models;

namespace WhisperWriter.UI.ViewModels;

/// <summary>
/// View model for the settings window.
/// </summary>
public partial class SettingsViewModel : ViewModelBase
{
    private readonly IConfigurationService _configService;
    private readonly IAudioRecorderService _audioRecorder;

    // Model Options
    [ObservableProperty]
    private bool _useApi = true;

    [ObservableProperty]
    private string _apiKey = string.Empty;

    [ObservableProperty]
    private string _apiBaseUrl = "https://api.openai.com/v1";

    [ObservableProperty]
    private string _apiModel = "whisper-1";

    [ObservableProperty]
    private string _language = string.Empty;

    [ObservableProperty]
    private double _temperature = 0.0;

    [ObservableProperty]
    private string _initialPrompt = string.Empty;

    [ObservableProperty]
    private string _localModel = "base";

    [ObservableProperty]
    private string _localDevice = "auto";

    [ObservableProperty]
    private string _computeType = "default";

    // Recording Options
    [ObservableProperty]
    private string _activationKey = "ctrl+shift+space";

    [ObservableProperty]
    private RecordingMode _recordingMode = RecordingMode.VoiceActivityDetection;

    [ObservableProperty]
    private int _selectedDeviceIndex = -1;

    [ObservableProperty]
    private int _sampleRate = 16000;

    [ObservableProperty]
    private int _silenceDuration = 900;

    [ObservableProperty]
    private int _minDuration = 100;

    // Post-Processing Options
    [ObservableProperty]
    private double _writingKeyPressDelay = 0.005;

    [ObservableProperty]
    private bool _removeTrailingPeriod;

    [ObservableProperty]
    private bool _addTrailingSpace = true;

    [ObservableProperty]
    private bool _removeCapitalization;

    [ObservableProperty]
    private InputMethod _inputMethod = InputMethod.SharpHook;

    // Misc Options
    [ObservableProperty]
    private bool _printToTerminal = true;

    [ObservableProperty]
    private bool _hideStatusWindow;

    [ObservableProperty]
    private bool _noiseOnCompletion;

    [ObservableProperty]
    private bool _startMinimized;

    // Collections
    public ObservableCollection<AudioDevice> AudioDevices { get; } = new();
    public ObservableCollection<string> LocalModels { get; } = new() { "tiny", "base", "small", "medium", "large" };
    public ObservableCollection<string> Devices { get; } = new() { "auto", "cuda", "cpu" };
    public ObservableCollection<string> ComputeTypes { get; } = new() { "default", "float32", "float16", "int8" };
    public ObservableCollection<RecordingMode> RecordingModes { get; } = new()
    {
        RecordingMode.Continuous,
        RecordingMode.VoiceActivityDetection,
        RecordingMode.PressToToggle,
        RecordingMode.HoldToRecord
    };
    public ObservableCollection<InputMethod> InputMethods { get; } = new()
    {
        InputMethod.SharpHook,
        InputMethod.Native,
        InputMethod.Ydotool,
        InputMethod.Dotool
    };

    public SettingsViewModel(IConfigurationService configService, IAudioRecorderService audioRecorder)
    {
        _configService = configService;
        _audioRecorder = audioRecorder;

        LoadAudioDevices();
        LoadFromConfiguration();
    }

    private void LoadAudioDevices()
    {
        AudioDevices.Clear();
        AudioDevices.Add(new AudioDevice { DeviceIndex = -1, Name = "Default Device", IsDefault = true });

        foreach (var device in _audioRecorder.GetAvailableDevices())
        {
            AudioDevices.Add(device);
        }
    }

    private void LoadFromConfiguration()
    {
        var config = _configService.Configuration;

        // Model
        UseApi = config.Model.UseApi;
        ApiKey = config.Model.Api.ApiKey ?? string.Empty;
        ApiBaseUrl = config.Model.Api.BaseUrl;
        ApiModel = config.Model.Api.Model;
        Language = config.Model.Common.Language ?? string.Empty;
        Temperature = config.Model.Common.Temperature;
        InitialPrompt = config.Model.Common.InitialPrompt ?? string.Empty;
        LocalModel = config.Model.Local.Model;
        LocalDevice = config.Model.Local.Device;
        ComputeType = config.Model.Local.ComputeType;

        // Recording
        ActivationKey = config.Recording.ActivationKey;
        RecordingMode = config.Recording.RecordingMode;
        SelectedDeviceIndex = config.Recording.SoundDevice;
        SampleRate = config.Recording.SampleRate;
        SilenceDuration = config.Recording.SilenceDuration;
        MinDuration = config.Recording.MinDuration;

        // Post-Processing
        WritingKeyPressDelay = config.PostProcessing.WritingKeyPressDelay;
        RemoveTrailingPeriod = config.PostProcessing.RemoveTrailingPeriod;
        AddTrailingSpace = config.PostProcessing.AddTrailingSpace;
        RemoveCapitalization = config.PostProcessing.RemoveCapitalization;
        InputMethod = config.PostProcessing.InputMethod;

        // Misc
        PrintToTerminal = config.Misc.PrintToTerminal;
        HideStatusWindow = config.Misc.HideStatusWindow;
        NoiseOnCompletion = config.Misc.NoiseOnCompletion;
        StartMinimized = config.Misc.StartMinimized;
    }

    [RelayCommand]
    private async Task SaveAsync()
    {
        var config = _configService.Configuration;

        // Model
        config.Model.UseApi = UseApi;
        config.Model.Api.ApiKey = string.IsNullOrWhiteSpace(ApiKey) ? null : ApiKey;
        config.Model.Api.BaseUrl = ApiBaseUrl;
        config.Model.Api.Model = ApiModel;
        config.Model.Common.Language = string.IsNullOrWhiteSpace(Language) ? null : Language;
        config.Model.Common.Temperature = Temperature;
        config.Model.Common.InitialPrompt = string.IsNullOrWhiteSpace(InitialPrompt) ? null : InitialPrompt;
        config.Model.Local.Model = LocalModel;
        config.Model.Local.Device = LocalDevice;
        config.Model.Local.ComputeType = ComputeType;

        // Recording
        config.Recording.ActivationKey = ActivationKey;
        config.Recording.RecordingMode = RecordingMode;
        config.Recording.SoundDevice = SelectedDeviceIndex;
        config.Recording.SampleRate = SampleRate;
        config.Recording.SilenceDuration = SilenceDuration;
        config.Recording.MinDuration = MinDuration;

        // Post-Processing
        config.PostProcessing.WritingKeyPressDelay = WritingKeyPressDelay;
        config.PostProcessing.RemoveTrailingPeriod = RemoveTrailingPeriod;
        config.PostProcessing.AddTrailingSpace = AddTrailingSpace;
        config.PostProcessing.RemoveCapitalization = RemoveCapitalization;
        config.PostProcessing.InputMethod = InputMethod;

        // Misc
        config.Misc.PrintToTerminal = PrintToTerminal;
        config.Misc.HideStatusWindow = HideStatusWindow;
        config.Misc.NoiseOnCompletion = NoiseOnCompletion;
        config.Misc.StartMinimized = StartMinimized;

        await _configService.SaveAsync();
    }

    [RelayCommand]
    private void ResetToDefaults()
    {
        _configService.ResetToDefaults();
        LoadFromConfiguration();
    }
}
