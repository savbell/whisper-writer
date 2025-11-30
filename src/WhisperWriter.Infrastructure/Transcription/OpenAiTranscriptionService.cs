using Flurl;
using Flurl.Http;
using Microsoft.Extensions.Logging;
using WhisperWriter.Core.Interfaces;
using WhisperWriter.Core.Models;

namespace WhisperWriter.Infrastructure.Transcription;

/// <summary>
/// OpenAI Whisper API transcription service using Flurl.
/// </summary>
public sealed class OpenAiTranscriptionService : ITranscriptionService
{
    private readonly ILogger<OpenAiTranscriptionService> _logger;
    private readonly IConfigurationService _configService;

    public OpenAiTranscriptionService(
        ILogger<OpenAiTranscriptionService> logger,
        IConfigurationService configService)
    {
        _logger = logger;
        _configService = configService;
    }

    public async Task<TranscriptionResult> TranscribeAsync(AudioData audioData, CancellationToken cancellationToken = default)
    {
        var config = _configService.Configuration.Model;

        if (string.IsNullOrEmpty(config.Api.ApiKey))
        {
            _logger.LogError("OpenAI API key is not configured");
            return TranscriptionResult.Failed("API key is not configured. Please set your OpenAI API key.");
        }

        try
        {
            _logger.LogDebug("Starting transcription with OpenAI API");

            var url = config.Api.BaseUrl
                .AppendPathSegment("audio")
                .AppendPathSegment("transcriptions");

            using var audioStream = audioData.GetStream();

            var request = url
                .WithHeader("Authorization", $"Bearer {config.Api.ApiKey}")
                .AllowAnyHttpStatus();

            // Build multipart form data
            var response = await request
                .PostMultipartAsync(mp =>
                {
                    mp.AddFile("file", audioStream, "audio.wav", "audio/wav");
                    mp.AddString("model", config.Api.Model);
                    mp.AddString("response_format", "json");

                    if (!string.IsNullOrEmpty(config.Common.Language))
                    {
                        mp.AddString("language", config.Common.Language);
                    }

                    if (config.Common.Temperature > 0)
                    {
                        mp.AddString("temperature", config.Common.Temperature.ToString("F2"));
                    }

                    if (!string.IsNullOrEmpty(config.Common.InitialPrompt))
                    {
                        mp.AddString("prompt", config.Common.InitialPrompt);
                    }
                }, cancellationToken);

            if (!response.ResponseMessage.IsSuccessStatusCode)
            {
                var errorBody = await response.GetStringAsync();
                _logger.LogError("OpenAI API error: {StatusCode} - {Error}",
                    response.StatusCode, errorBody);
                return TranscriptionResult.Failed($"API error: {response.StatusCode} - {errorBody}");
            }

            var result = await response.GetJsonAsync<OpenAiTranscriptionResponse>();

            if (result == null || string.IsNullOrEmpty(result.Text))
            {
                _logger.LogWarning("Empty transcription result from API");
                return TranscriptionResult.Failed("Empty transcription result");
            }

            _logger.LogInformation("Transcription successful: {Length} characters", result.Text.Length);

            return TranscriptionResult.Successful(
                result.Text,
                result.Language,
                result.Duration);
        }
        catch (FlurlHttpException ex)
        {
            _logger.LogError(ex, "HTTP error during transcription");
            var errorBody = await ex.GetResponseStringAsync();
            return TranscriptionResult.Failed($"HTTP error: {ex.StatusCode} - {errorBody}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during transcription");
            return TranscriptionResult.Failed($"Transcription error: {ex.Message}");
        }
    }
}

/// <summary>
/// Response model for OpenAI transcription API.
/// </summary>
internal sealed class OpenAiTranscriptionResponse
{
    public string Text { get; set; } = string.Empty;
    public string? Language { get; set; }
    public double? Duration { get; set; }
}
