using WhisperWriter.Core.Models;

namespace WhisperWriter.Core.Interfaces;

/// <summary>
/// Interface for keyboard listener services.
/// </summary>
public interface IKeyboardListenerService : IDisposable
{
    /// <summary>
    /// Event raised when the activation hotkey is pressed.
    /// </summary>
    event EventHandler? ActivationKeyPressed;

    /// <summary>
    /// Event raised when the activation hotkey is released.
    /// </summary>
    event EventHandler? ActivationKeyReleased;

    /// <summary>
    /// Sets the activation hotkey.
    /// </summary>
    /// <param name="hotKey">The hotkey to set.</param>
    void SetActivationKey(HotKey hotKey);

    /// <summary>
    /// Starts listening for keyboard events.
    /// </summary>
    void Start();

    /// <summary>
    /// Stops listening for keyboard events.
    /// </summary>
    void Stop();

    /// <summary>
    /// Whether the listener is currently running.
    /// </summary>
    bool IsListening { get; }
}
