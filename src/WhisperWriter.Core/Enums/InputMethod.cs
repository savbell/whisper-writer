namespace WhisperWriter.Core.Enums;

/// <summary>
/// Defines the method used to simulate keyboard input.
/// </summary>
public enum InputMethod
{
    /// <summary>
    /// Use SharpHook for cross-platform input simulation.
    /// </summary>
    SharpHook,

    /// <summary>
    /// Use platform-specific native methods.
    /// </summary>
    Native,

    /// <summary>
    /// Use ydotool on Linux systems.
    /// </summary>
    Ydotool,

    /// <summary>
    /// Use dotool on Linux systems.
    /// </summary>
    Dotool
}
