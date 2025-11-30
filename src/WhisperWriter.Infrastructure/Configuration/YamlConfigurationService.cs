using Microsoft.Extensions.Logging;
using WhisperWriter.Core.Interfaces;
using WhisperWriter.Core.Models;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace WhisperWriter.Infrastructure.Configuration;

/// <summary>
/// YAML-based configuration service implementation.
/// </summary>
public sealed class YamlConfigurationService : IConfigurationService
{
    private readonly ILogger<YamlConfigurationService> _logger;
    private readonly string _configPath;
    private readonly ISerializer _serializer;
    private readonly IDeserializer _deserializer;
    private AppConfiguration _configuration;

    public event EventHandler<ConfigurationChangedEventArgs>? ConfigurationChanged;

    public AppConfiguration Configuration => _configuration;

    public YamlConfigurationService(ILogger<YamlConfigurationService> logger, string? configPath = null)
    {
        _logger = logger;
        _configPath = configPath ?? GetDefaultConfigPath();
        _configuration = new AppConfiguration();

        _serializer = new SerializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .ConfigureDefaultValuesHandling(DefaultValuesHandling.OmitNull)
            .Build();

        _deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .IgnoreUnmatchedProperties()
            .Build();
    }

    private static string GetDefaultConfigPath()
    {
        var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var configDir = Path.Combine(appDataPath, "WhisperWriter");
        Directory.CreateDirectory(configDir);
        return Path.Combine(configDir, "config.yaml");
    }

    public async Task LoadAsync()
    {
        try
        {
            if (!File.Exists(_configPath))
            {
                _logger.LogInformation("Configuration file not found at {Path}, using defaults", _configPath);
                _configuration = new AppConfiguration();
                await SaveAsync();
                return;
            }

            var yaml = await File.ReadAllTextAsync(_configPath);
            var loaded = _deserializer.Deserialize<AppConfiguration>(yaml);

            if (loaded != null)
            {
                _configuration = loaded;
                _logger.LogInformation("Configuration loaded from {Path}", _configPath);
            }
            else
            {
                _logger.LogWarning("Failed to deserialize configuration, using defaults");
                _configuration = new AppConfiguration();
            }

            // Load API key from environment variable if not set in config
            if (string.IsNullOrEmpty(_configuration.Model.Api.ApiKey))
            {
                _configuration.Model.Api.ApiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading configuration from {Path}", _configPath);
            _configuration = new AppConfiguration();
        }
    }

    public async Task SaveAsync()
    {
        try
        {
            var directory = Path.GetDirectoryName(_configPath);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }

            // Don't save API key to file for security
            var configToSave = CloneConfigurationWithoutSecrets(_configuration);
            var yaml = _serializer.Serialize(configToSave);
            await File.WriteAllTextAsync(_configPath, yaml);

            _logger.LogInformation("Configuration saved to {Path}", _configPath);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error saving configuration to {Path}", _configPath);
            throw;
        }
    }

    public void ResetToDefaults()
    {
        var oldConfig = _configuration;
        _configuration = new AppConfiguration();

        // Preserve API key from environment
        _configuration.Model.Api.ApiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");

        ConfigurationChanged?.Invoke(this, new ConfigurationChangedEventArgs(oldConfig, _configuration));
    }

    private static AppConfiguration CloneConfigurationWithoutSecrets(AppConfiguration config)
    {
        // Create a deep copy without sensitive data
        return new AppConfiguration
        {
            Model = new ModelOptions
            {
                UseApi = config.Model.UseApi,
                Common = new CommonModelSettings
                {
                    Language = config.Model.Common.Language,
                    Temperature = config.Model.Common.Temperature,
                    InitialPrompt = config.Model.Common.InitialPrompt
                },
                Api = new ApiModelSettings
                {
                    Model = config.Model.Api.Model,
                    BaseUrl = config.Model.Api.BaseUrl,
                    ApiKey = null // Don't save API key
                },
                Local = new LocalModelSettings
                {
                    Model = config.Model.Local.Model,
                    Device = config.Model.Local.Device,
                    ComputeType = config.Model.Local.ComputeType,
                    ConditionOnPreviousText = config.Model.Local.ConditionOnPreviousText,
                    VadFilter = config.Model.Local.VadFilter,
                    ModelPath = config.Model.Local.ModelPath
                }
            },
            Recording = new RecordingOptions
            {
                ActivationKey = config.Recording.ActivationKey,
                RecordingMode = config.Recording.RecordingMode,
                SoundDevice = config.Recording.SoundDevice,
                SampleRate = config.Recording.SampleRate,
                SilenceDuration = config.Recording.SilenceDuration,
                MinDuration = config.Recording.MinDuration
            },
            PostProcessing = new PostProcessingOptions
            {
                WritingKeyPressDelay = config.PostProcessing.WritingKeyPressDelay,
                RemoveTrailingPeriod = config.PostProcessing.RemoveTrailingPeriod,
                AddTrailingSpace = config.PostProcessing.AddTrailingSpace,
                RemoveCapitalization = config.PostProcessing.RemoveCapitalization,
                InputMethod = config.PostProcessing.InputMethod
            },
            Misc = new MiscellaneousOptions
            {
                PrintToTerminal = config.Misc.PrintToTerminal,
                HideStatusWindow = config.Misc.HideStatusWindow,
                NoiseOnCompletion = config.Misc.NoiseOnCompletion,
                StartMinimized = config.Misc.StartMinimized
            }
        };
    }
}
