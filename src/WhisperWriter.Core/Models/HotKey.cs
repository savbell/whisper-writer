namespace WhisperWriter.Core.Models;

/// <summary>
/// Represents a keyboard hotkey combination.
/// </summary>
public sealed class HotKey : IEquatable<HotKey>
{
    /// <summary>
    /// The main key of the hotkey.
    /// </summary>
    public string Key { get; init; } = string.Empty;

    /// <summary>
    /// Whether the Control key must be held.
    /// </summary>
    public bool Control { get; init; }

    /// <summary>
    /// Whether the Shift key must be held.
    /// </summary>
    public bool Shift { get; init; }

    /// <summary>
    /// Whether the Alt key must be held.
    /// </summary>
    public bool Alt { get; init; }

    /// <summary>
    /// Whether the Meta/Windows key must be held.
    /// </summary>
    public bool Meta { get; init; }

    /// <summary>
    /// Parses a hotkey string like "ctrl+shift+space" into a HotKey object.
    /// </summary>
    public static HotKey Parse(string hotkeyString)
    {
        if (string.IsNullOrWhiteSpace(hotkeyString))
        {
            return new HotKey { Key = "space", Control = true, Shift = true };
        }

        var parts = hotkeyString.ToLowerInvariant().Split('+');
        var hotKey = new HotKey();
        var control = false;
        var shift = false;
        var alt = false;
        var meta = false;
        var key = string.Empty;

        foreach (var part in parts)
        {
            var trimmed = part.Trim();
            switch (trimmed)
            {
                case "ctrl":
                case "control":
                    control = true;
                    break;
                case "shift":
                    shift = true;
                    break;
                case "alt":
                    alt = true;
                    break;
                case "meta":
                case "win":
                case "super":
                case "cmd":
                    meta = true;
                    break;
                default:
                    key = trimmed;
                    break;
            }
        }

        return new HotKey
        {
            Key = key,
            Control = control,
            Shift = shift,
            Alt = alt,
            Meta = meta
        };
    }

    public override string ToString()
    {
        var parts = new List<string>();
        if (Control) parts.Add("Ctrl");
        if (Shift) parts.Add("Shift");
        if (Alt) parts.Add("Alt");
        if (Meta) parts.Add("Meta");
        if (!string.IsNullOrEmpty(Key)) parts.Add(Key.ToUpperInvariant());
        return string.Join("+", parts);
    }

    public bool Equals(HotKey? other)
    {
        if (other is null) return false;
        return Key.Equals(other.Key, StringComparison.OrdinalIgnoreCase) &&
               Control == other.Control &&
               Shift == other.Shift &&
               Alt == other.Alt &&
               Meta == other.Meta;
    }

    public override bool Equals(object? obj) => Equals(obj as HotKey);

    public override int GetHashCode() => HashCode.Combine(Key.ToLowerInvariant(), Control, Shift, Alt, Meta);
}
