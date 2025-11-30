namespace WhisperWriter.Core.Interfaces;

/// <summary>
/// Interface for input simulation services.
/// </summary>
public interface IInputSimulatorService
{
    /// <summary>
    /// Types the specified text character by character.
    /// </summary>
    /// <param name="text">The text to type.</param>
    /// <param name="delayBetweenKeys">Delay between key presses in milliseconds.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task TypeTextAsync(string text, int delayBetweenKeys = 5, CancellationToken cancellationToken = default);

    /// <summary>
    /// Types the specified text immediately (no delays).
    /// </summary>
    /// <param name="text">The text to type.</param>
    void TypeText(string text);
}
