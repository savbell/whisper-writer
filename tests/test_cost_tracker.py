import os
import json
import unittest
from datetime import datetime
from src.cost_tracker import CostTracker

class TestCostTracker(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.test_log_file = "test_usage_costs.json"
        self.cost_tracker = CostTracker(self.test_log_file)

    def tearDown(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_whisper_cost_calculation(self):
        """Test Whisper API cost calculations."""
        # Test 5-minute audio
        cost = self.cost_tracker.log_whisper_usage(duration_seconds=300)
        self.assertAlmostEqual(cost, 0.03, places=4)  # $0.03 for 5 minutes

        # Test 1-hour audio
        cost = self.cost_tracker.log_whisper_usage(duration_seconds=3600)
        self.assertAlmostEqual(cost, 0.36, places=4)  # $0.36 for 1 hour

        # Test rounding to nearest second
        cost = self.cost_tracker.log_whisper_usage(duration_seconds=59.6)
        self.assertAlmostEqual(cost, 0.006, places=4)  # Should round to 60 seconds = $0.006

    def test_gpt_cost_calculation(self):
        """Test GPT API cost calculations."""
        # Test with GPT-4o model
        cost = self.cost_tracker.log_gpt_usage(
            model="gpt-4o-2024-08-06",
            input_tokens=500_000,  # 500K tokens
            output_tokens=200_000,  # 200K tokens
            original_text="Test input",
            enhanced_text="Test output"
        )
        # Expected: $1.25 for input (500K × $2.50/1M) + $2.00 for output (200K × $10.00/1M)
        self.assertAlmostEqual(cost, 3.25, places=4)

    def test_usage_logging(self):
        """Test that usage data is properly logged to file."""
        # Log some usage
        self.cost_tracker.log_whisper_usage(duration_seconds=300)
        self.cost_tracker.log_gpt_usage(
            model="gpt-4o-2024-08-06",
            input_tokens=1000,
            output_tokens=500,
            original_text="Test",
            enhanced_text="Enhanced test"
        )

        # Verify log file exists and contains valid JSON
        self.assertTrue(os.path.exists(self.test_log_file))
        with open(self.test_log_file, 'r') as f:
            data = json.load(f)
            self.assertTrue('whisper_usage' in data)
            self.assertTrue('gpt_usage' in data)
            self.assertTrue('total_cost' in data)

    def test_usage_summary(self):
        """Test usage summary generation."""
        # Log multiple entries
        self.cost_tracker.log_whisper_usage(duration_seconds=300)  # 5 minutes
        self.cost_tracker.log_whisper_usage(duration_seconds=600)  # 10 minutes
        self.cost_tracker.log_gpt_usage(
            model="gpt-4o-2024-08-06",
            input_tokens=100_000,
            output_tokens=50_000,
            original_text="Test 1",
            enhanced_text="Enhanced 1"
        )
        self.cost_tracker.log_gpt_usage(
            model="gpt-4o-2024-08-06",
            input_tokens=200_000,
            output_tokens=75_000,
            original_text="Test 2",
            enhanced_text="Enhanced 2"
        )

        # Get summary
        summary = self.cost_tracker.get_usage_summary()

        # Verify summary calculations
        self.assertEqual(summary['whisper_usage']['num_transcriptions'], 2)
        self.assertEqual(summary['whisper_usage']['total_duration_seconds'], 900)
        self.assertEqual(summary['gpt_usage']['num_enhancements'], 2)
        self.assertEqual(summary['gpt_usage']['total_input_tokens'], 300_000)
        self.assertEqual(summary['gpt_usage']['total_output_tokens'], 125_000)

    def test_detailed_usage(self):
        """Test detailed usage report generation."""
        # Log some usage
        self.cost_tracker.log_whisper_usage(duration_seconds=300)
        self.cost_tracker.log_gpt_usage(
            model="gpt-4o-2024-08-06",
            input_tokens=1000,
            output_tokens=500,
            original_text="Original",
            enhanced_text="Enhanced"
        )

        # Get detailed report with text
        detailed = self.cost_tracker.get_detailed_usage(include_text=True)
        self.assertTrue('original_text' in detailed['recent_gpt_usage'][0])
        self.assertTrue('enhanced_text' in detailed['recent_gpt_usage'][0])

        # Get detailed report without text
        detailed = self.cost_tracker.get_detailed_usage(include_text=False)
        self.assertFalse('original_text' in detailed['recent_gpt_usage'][0])
        self.assertFalse('enhanced_text' in detailed['recent_gpt_usage'][0])

if __name__ == '__main__':
    unittest.main()