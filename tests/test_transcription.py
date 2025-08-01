import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from src.transcription import transcribe_api, enhance_transcription
from src.cost_tracker import CostTracker

class TestTranscription(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.mock_audio_data = np.zeros(16000, dtype=np.int16)  # 1 second of silence
        self.mock_text = "This is a test transcription."

    @patch('src.transcription.OpenAI')
    @patch('src.transcription.cost_tracker')
    def test_transcribe_api(self, mock_cost_tracker, mock_openai):
        """Test the Whisper API transcription with cost tracking."""
        # Mock OpenAI client response
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="Test transcription")
        mock_openai.return_value = mock_client

        # Perform transcription
        result = transcribe_api(self.mock_audio_data)

        # Verify OpenAI API was called correctly
        mock_client.audio.transcriptions.create.assert_called_once()
        
        # Verify cost tracking was called
        mock_cost_tracker.log_whisper_usage.assert_called_once()
        args = mock_cost_tracker.log_whisper_usage.call_args[1]
        self.assertEqual(args['duration_seconds'], 1.0)  # 1 second of audio
        self.assertEqual(args['model'], 'whisper-1')

        # Verify result
        self.assertEqual(result, "Test transcription")

    @patch('src.transcription.OpenAI')
    @patch('src.transcription.cost_tracker')
    def test_enhance_transcription(self, mock_cost_tracker, mock_openai):
        """Test GPT enhancement with cost tracking."""
        # Mock OpenAI client response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Enhanced test transcription"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Perform enhancement
        result = enhance_transcription(self.mock_text)

        # Verify OpenAI API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify cost tracking was called
        mock_cost_tracker.log_gpt_usage.assert_called_once()
        args = mock_cost_tracker.log_gpt_usage.call_args[1]
        self.assertEqual(args['model'], 'gpt-4o-2024-08-06')
        self.assertTrue(args['input_tokens'] > 0)
        self.assertTrue(args['output_tokens'] > 0)
        self.assertEqual(args['original_text'], self.mock_text)
        self.assertEqual(args['enhanced_text'], "Enhanced test transcription")

        # Verify result
        self.assertEqual(result, "Enhanced test transcription")

    @patch('src.transcription.OpenAI')
    @patch('src.transcription.cost_tracker')
    def test_enhancement_disabled(self, mock_cost_tracker, mock_openai):
        """Test that enhancement is skipped when disabled in config."""
        with patch('src.transcription.ConfigManager') as mock_config:
            # Mock config to disable enhancement
            mock_config.get_config_section.return_value = {'enhance_with_gpt': False}
            
            # Perform enhancement
            result = enhance_transcription(self.mock_text)

            # Verify no API calls or cost tracking
            mock_openai.assert_not_called()
            mock_cost_tracker.log_gpt_usage.assert_not_called()

            # Verify original text is returned unchanged
            self.assertEqual(result, self.mock_text)

    @patch('src.transcription.OpenAI')
    @patch('src.transcription.cost_tracker')
    def test_error_handling(self, mock_cost_tracker, mock_openai):
        """Test error handling in transcription and enhancement."""
        # Mock OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        # Test enhancement error handling
        result = enhance_transcription(self.mock_text)
        
        # Verify no cost tracking on error
        mock_cost_tracker.log_gpt_usage.assert_not_called()
        
        # Verify original text is returned on error
        self.assertEqual(result, self.mock_text)

if __name__ == '__main__':
    unittest.main()