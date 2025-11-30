using Microsoft.Extensions.Logging;
using SharpHook;
using SharpHook.Native;
using WhisperWriter.Core.Interfaces;
using WhisperWriter.Core.Models;

namespace WhisperWriter.Infrastructure.Keyboard;

/// <summary>
/// Keyboard listener service using SharpHook for cross-platform support.
/// </summary>
public sealed class SharpHookKeyboardListenerService : IKeyboardListenerService
{
    private readonly ILogger<SharpHookKeyboardListenerService> _logger;
    private readonly TaskPoolGlobalHook _hook;
    private HotKey _activationKey;
    private bool _disposed;

    // Track currently pressed modifier keys
    private bool _ctrlPressed;
    private bool _shiftPressed;
    private bool _altPressed;
    private bool _metaPressed;
    private bool _mainKeyPressed;

    public event EventHandler? ActivationKeyPressed;
    public event EventHandler? ActivationKeyReleased;

    public bool IsListening { get; private set; }

    public SharpHookKeyboardListenerService(ILogger<SharpHookKeyboardListenerService> logger)
    {
        _logger = logger;
        _hook = new TaskPoolGlobalHook();
        _activationKey = HotKey.Parse("ctrl+shift+space");

        _hook.KeyPressed += OnKeyPressed;
        _hook.KeyReleased += OnKeyReleased;
    }

    public void SetActivationKey(HotKey hotKey)
    {
        _activationKey = hotKey;
        _logger.LogInformation("Activation key set to: {HotKey}", hotKey);
    }

    public void Start()
    {
        if (IsListening || _disposed) return;

        _hook.RunAsync();
        IsListening = true;
        _logger.LogInformation("Keyboard listener started");
    }

    public void Stop()
    {
        if (!IsListening) return;

        _hook.Dispose();
        IsListening = false;
        _logger.LogInformation("Keyboard listener stopped");
    }

    private void OnKeyPressed(object? sender, KeyboardHookEventArgs e)
    {
        UpdateModifierState(e.Data.KeyCode, true);

        // Check if it's the main key
        var keyName = GetKeyName(e.Data.KeyCode);
        if (keyName.Equals(_activationKey.Key, StringComparison.OrdinalIgnoreCase))
        {
            // Check if all required modifiers are pressed
            if (ModifiersMatch())
            {
                _mainKeyPressed = true;
                _logger.LogDebug("Activation key pressed");
                ActivationKeyPressed?.Invoke(this, EventArgs.Empty);
            }
        }
    }

    private void OnKeyReleased(object? sender, KeyboardHookEventArgs e)
    {
        var wasMainKeyPressed = _mainKeyPressed;
        UpdateModifierState(e.Data.KeyCode, false);

        // Check if the main key was released
        var keyName = GetKeyName(e.Data.KeyCode);
        if (keyName.Equals(_activationKey.Key, StringComparison.OrdinalIgnoreCase))
        {
            if (wasMainKeyPressed)
            {
                _mainKeyPressed = false;
                _logger.LogDebug("Activation key released");
                ActivationKeyReleased?.Invoke(this, EventArgs.Empty);
            }
        }
    }

    private void UpdateModifierState(KeyCode keyCode, bool pressed)
    {
        switch (keyCode)
        {
            case KeyCode.VcLeftControl:
            case KeyCode.VcRightControl:
                _ctrlPressed = pressed;
                break;
            case KeyCode.VcLeftShift:
            case KeyCode.VcRightShift:
                _shiftPressed = pressed;
                break;
            case KeyCode.VcLeftAlt:
            case KeyCode.VcRightAlt:
                _altPressed = pressed;
                break;
            case KeyCode.VcLeftMeta:
            case KeyCode.VcRightMeta:
                _metaPressed = pressed;
                break;
        }
    }

    private bool ModifiersMatch()
    {
        return _ctrlPressed == _activationKey.Control &&
               _shiftPressed == _activationKey.Shift &&
               _altPressed == _activationKey.Alt &&
               _metaPressed == _activationKey.Meta;
    }

    private static string GetKeyName(KeyCode keyCode)
    {
        return keyCode switch
        {
            KeyCode.VcSpace => "space",
            KeyCode.VcEnter => "enter",
            KeyCode.VcEscape => "escape",
            KeyCode.VcTab => "tab",
            KeyCode.VcBackspace => "backspace",
            KeyCode.VcInsert => "insert",
            KeyCode.VcDelete => "delete",
            KeyCode.VcHome => "home",
            KeyCode.VcEnd => "end",
            KeyCode.VcPageUp => "pageup",
            KeyCode.VcPageDown => "pagedown",
            KeyCode.VcUp => "up",
            KeyCode.VcDown => "down",
            KeyCode.VcLeft => "left",
            KeyCode.VcRight => "right",
            KeyCode.VcF1 => "f1",
            KeyCode.VcF2 => "f2",
            KeyCode.VcF3 => "f3",
            KeyCode.VcF4 => "f4",
            KeyCode.VcF5 => "f5",
            KeyCode.VcF6 => "f6",
            KeyCode.VcF7 => "f7",
            KeyCode.VcF8 => "f8",
            KeyCode.VcF9 => "f9",
            KeyCode.VcF10 => "f10",
            KeyCode.VcF11 => "f11",
            KeyCode.VcF12 => "f12",
            KeyCode.VcA => "a",
            KeyCode.VcB => "b",
            KeyCode.VcC => "c",
            KeyCode.VcD => "d",
            KeyCode.VcE => "e",
            KeyCode.VcF => "f",
            KeyCode.VcG => "g",
            KeyCode.VcH => "h",
            KeyCode.VcI => "i",
            KeyCode.VcJ => "j",
            KeyCode.VcK => "k",
            KeyCode.VcL => "l",
            KeyCode.VcM => "m",
            KeyCode.VcN => "n",
            KeyCode.VcO => "o",
            KeyCode.VcP => "p",
            KeyCode.VcQ => "q",
            KeyCode.VcR => "r",
            KeyCode.VcS => "s",
            KeyCode.VcT => "t",
            KeyCode.VcU => "u",
            KeyCode.VcV => "v",
            KeyCode.VcW => "w",
            KeyCode.VcX => "x",
            KeyCode.VcY => "y",
            KeyCode.VcZ => "z",
            KeyCode.Vc0 => "0",
            KeyCode.Vc1 => "1",
            KeyCode.Vc2 => "2",
            KeyCode.Vc3 => "3",
            KeyCode.Vc4 => "4",
            KeyCode.Vc5 => "5",
            KeyCode.Vc6 => "6",
            KeyCode.Vc7 => "7",
            KeyCode.Vc8 => "8",
            KeyCode.Vc9 => "9",
            _ => keyCode.ToString().Replace("Vc", "").ToLowerInvariant()
        };
    }

    public void Dispose()
    {
        if (_disposed) return;
        Stop();
        _hook.Dispose();
        _disposed = true;
    }
}
