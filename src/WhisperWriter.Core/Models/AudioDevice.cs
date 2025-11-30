namespace WhisperWriter.Core.Models;

/// <summary>
/// Represents an audio input device.
/// </summary>
public sealed record AudioDevice
{
    /// <summary>
    /// The device index/ID.
    /// </summary>
    public int DeviceIndex { get; init; }

    /// <summary>
    /// The friendly name of the device.
    /// </summary>
    public string Name { get; init; } = string.Empty;

    /// <summary>
    /// The number of input channels.
    /// </summary>
    public int Channels { get; init; }

    /// <summary>
    /// Whether this is the default device.
    /// </summary>
    public bool IsDefault { get; init; }

    public override string ToString() => IsDefault ? $"{Name} (Default)" : Name;
}
