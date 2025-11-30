using WhisperWriter.Core.Models;

namespace WhisperWriter.Core.Interfaces;

/// <summary>
/// Interface for text post-processing.
/// </summary>
public interface ITextPostProcessor
{
    /// <summary>
    /// Processes the transcribed text according to the configured options.
    /// </summary>
    /// <param name="text">The text to process.</param>
    /// <param name="options">The post-processing options.</param>
    /// <returns>The processed text.</returns>
    string Process(string text, PostProcessingOptions options);
}
