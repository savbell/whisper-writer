using Microsoft.Extensions.Logging;
using SharpHook;
using SharpHook.Native;
using WhisperWriter.Core.Interfaces;

namespace WhisperWriter.Infrastructure.Input;

/// <summary>
/// Input simulator service using SharpHook for cross-platform support.
/// </summary>
public sealed class SharpHookInputSimulatorService : IInputSimulatorService
{
    private readonly ILogger<SharpHookInputSimulatorService> _logger;
    private readonly EventSimulator _simulator;

    public SharpHookInputSimulatorService(ILogger<SharpHookInputSimulatorService> logger)
    {
        _logger = logger;
        _simulator = new EventSimulator();
    }

    public async Task TypeTextAsync(string text, int delayBetweenKeys = 5, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(text)) return;

        _logger.LogDebug("Typing text with {Length} characters", text.Length);

        foreach (var c in text)
        {
            cancellationToken.ThrowIfCancellationRequested();

            TypeCharacter(c);

            if (delayBetweenKeys > 0)
            {
                await Task.Delay(delayBetweenKeys, cancellationToken);
            }
        }
    }

    public void TypeText(string text)
    {
        if (string.IsNullOrEmpty(text)) return;

        _logger.LogDebug("Typing text immediately: {Length} characters", text.Length);

        foreach (var c in text)
        {
            TypeCharacter(c);
        }
    }

    private void TypeCharacter(char c)
    {
        // Use UioHook's text entry simulation for Unicode support
        _simulator.SimulateTextEntry(c.ToString());
    }

    /// <summary>
    /// Simulates a key press and release.
    /// </summary>
    public void PressKey(KeyCode keyCode, bool shift = false, bool ctrl = false, bool alt = false)
    {
        // Press modifiers
        if (ctrl) _simulator.SimulateKeyPress(KeyCode.VcLeftControl);
        if (shift) _simulator.SimulateKeyPress(KeyCode.VcLeftShift);
        if (alt) _simulator.SimulateKeyPress(KeyCode.VcLeftAlt);

        // Press and release key
        _simulator.SimulateKeyPress(keyCode);
        _simulator.SimulateKeyRelease(keyCode);

        // Release modifiers
        if (alt) _simulator.SimulateKeyRelease(KeyCode.VcLeftAlt);
        if (shift) _simulator.SimulateKeyRelease(KeyCode.VcLeftShift);
        if (ctrl) _simulator.SimulateKeyRelease(KeyCode.VcLeftControl);
    }
}
