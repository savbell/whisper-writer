using WhisperWriter.Core.Interfaces;
using WhisperWriter.Core.Models;

namespace WhisperWriter.Infrastructure;

/// <summary>
/// Text post-processor implementation.
/// </summary>
public sealed class TextPostProcessor : ITextPostProcessor
{
    public string Process(string text, PostProcessingOptions options)
    {
        if (string.IsNullOrEmpty(text))
        {
            return text;
        }

        var result = text.Trim();

        // Remove trailing period
        if (options.RemoveTrailingPeriod && result.EndsWith('.'))
        {
            result = result.TrimEnd('.');
        }

        // Convert to lowercase
        if (options.RemoveCapitalization)
        {
            result = result.ToLowerInvariant();
        }

        // Add trailing space
        if (options.AddTrailingSpace && !string.IsNullOrEmpty(result))
        {
            result += " ";
        }

        return result;
    }
}
