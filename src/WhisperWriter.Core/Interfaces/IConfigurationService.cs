using WhisperWriter.Core.Models;

namespace WhisperWriter.Core.Interfaces;

/// <summary>
/// Interface for configuration management services.
/// </summary>
public interface IConfigurationService
{
    /// <summary>
    /// Gets the current configuration.
    /// </summary>
    AppConfiguration Configuration { get; }

    /// <summary>
    /// Loads the configuration from storage.
    /// </summary>
    Task LoadAsync();

    /// <summary>
    /// Saves the current configuration to storage.
    /// </summary>
    Task SaveAsync();

    /// <summary>
    /// Resets the configuration to defaults.
    /// </summary>
    void ResetToDefaults();

    /// <summary>
    /// Event raised when the configuration changes.
    /// </summary>
    event EventHandler<ConfigurationChangedEventArgs>? ConfigurationChanged;
}

/// <summary>
/// Event args for configuration changes.
/// </summary>
public sealed class ConfigurationChangedEventArgs : EventArgs
{
    public AppConfiguration OldConfiguration { get; }
    public AppConfiguration NewConfiguration { get; }

    public ConfigurationChangedEventArgs(AppConfiguration oldConfiguration, AppConfiguration newConfiguration)
    {
        OldConfiguration = oldConfiguration;
        NewConfiguration = newConfiguration;
    }
}
