import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class CostTracker:
    def __init__(self, log_file: str = "usage_costs.json"):
        """Initialize the cost tracker."""
        self.log_file = log_file
        self.usage_data = self._load_usage_data()
        
        # API costs in USD
        self.api_costs = {
            "whisper-1": {
                "audio": 0.006 / 60  # $0.006 per minute, stored as cost per second for precise calculation
            },
            "gpt-4o-2024-08-06": {
                "input": 2.50 / 1_000_000,   # $2.50 per 1M input tokens
                "output": 10.00 / 1_000_000  # $10.00 per 1M output tokens
            },
            "gpt-4-turbo-preview": {
                "input": 10.00 / 1_000_000,
                "output": 30.00 / 1_000_000
            },
            "gpt-4": {
                "input": 30.00 / 1_000_000,
                "output": 60.00 / 1_000_000
            },
            "gpt-3.5-turbo": {
                "input": 0.50 / 1_000_000,
                "output": 1.50 / 1_000_000
            }
        }

    def _load_usage_data(self) -> Dict:
        """Load existing usage data from file."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._initialize_usage_data()
        return self._initialize_usage_data()

    def _initialize_usage_data(self) -> Dict:
        """Initialize a new usage data structure."""
        return {
            "whisper_usage": [],
            "gpt_usage": [],
            "total_cost": 0.0,
            "last_updated": datetime.now().isoformat()
        }

    def _save_usage_data(self):
        """Save usage data to file."""
        self.usage_data["last_updated"] = datetime.now().isoformat()
        with open(self.log_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)

    def log_whisper_usage(self, duration_seconds: float, model: str = "whisper-1"):
        """
        Log Whisper API usage.
        
        Args:
            duration_seconds: Length of the audio in seconds
            model: Whisper model used
        """
        # Round to nearest second as per OpenAI billing
        duration_seconds = round(duration_seconds)
        # Calculate cost using per-second rate
        cost = duration_seconds * self.api_costs[model]["audio"]
        
        usage_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "duration_seconds": duration_seconds,
            "cost": cost
        }
        
        self.usage_data["whisper_usage"].append(usage_entry)
        self.usage_data["total_cost"] += cost
        self._save_usage_data()
        
        return cost

    def log_gpt_usage(self, 
                      model: str,
                      input_tokens: int,
                      output_tokens: int,
                      original_text: str,
                      enhanced_text: str):
        """
        Log GPT API usage.
        
        Args:
            model: GPT model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            original_text: Original text before enhancement
            enhanced_text: Enhanced text after GPT processing
        """
        input_cost = (input_tokens / 1000) * self.api_costs[model]["input"]
        output_cost = (output_tokens / 1000) * self.api_costs[model]["output"]
        total_cost = input_cost + output_cost
        
        usage_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "original_text": original_text,
            "enhanced_text": enhanced_text
        }
        
        self.usage_data["gpt_usage"].append(usage_entry)
        self.usage_data["total_cost"] += total_cost
        self._save_usage_data()
        
        return total_cost

    def get_usage_summary(self, 
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> Dict:
        """
        Get a summary of API usage and costs.
        
        Args:
            start_date: Optional start date in ISO format
            end_date: Optional end date in ISO format
        
        Returns:
            Dictionary containing usage summary
        """
        whisper_entries = self.usage_data["whisper_usage"]
        gpt_entries = self.usage_data["gpt_usage"]
        
        if start_date:
            whisper_entries = [e for e in whisper_entries 
                             if e["timestamp"] >= start_date]
            gpt_entries = [e for e in gpt_entries 
                          if e["timestamp"] >= start_date]
        
        if end_date:
            whisper_entries = [e for e in whisper_entries 
                             if e["timestamp"] <= end_date]
            gpt_entries = [e for e in gpt_entries 
                          if e["timestamp"] <= end_date]
        
        total_whisper_cost = sum(e["cost"] for e in whisper_entries)
        total_gpt_cost = sum(e["total_cost"] for e in gpt_entries)
        
        return {
            "period_start": start_date or whisper_entries[0]["timestamp"] if whisper_entries else None,
            "period_end": end_date or datetime.now().isoformat(),
            "whisper_usage": {
                "total_duration_seconds": sum(e["duration_seconds"] for e in whisper_entries),
                "total_cost": total_whisper_cost,
                "num_transcriptions": len(whisper_entries),
                "entries": whisper_entries  # Include full entries
            },
            "gpt_usage": {
                "total_input_tokens": sum(e["input_tokens"] for e in gpt_entries),
                "total_output_tokens": sum(e["output_tokens"] for e in gpt_entries),
                "total_cost": total_gpt_cost,
                "num_enhancements": len(gpt_entries),
                "entries": gpt_entries  # Include full entries
            },
            "total_cost": total_whisper_cost + total_gpt_cost,
            "last_whisper_entry": whisper_entries[-1] if whisper_entries else None,
            "last_gpt_entry": gpt_entries[-1] if gpt_entries else None
        }

    def get_detailed_usage(self,
                          limit: int = 10,
                          include_text: bool = False) -> Dict[str, List]:
        """
        Get detailed usage information for recent API calls.
        
        Args:
            limit: Number of recent entries to return
            include_text: Whether to include original/enhanced text
        
        Returns:
            Dictionary containing recent Whisper and GPT usage details
        """
        whisper_entries = self.usage_data["whisper_usage"][-limit:]
        gpt_entries = self.usage_data["gpt_usage"][-limit:]
        
        if not include_text:
            gpt_entries = [{k: v for k, v in e.items() 
                           if k not in ['original_text', 'enhanced_text']}
                          for e in gpt_entries]
        
        return {
            "recent_whisper_usage": whisper_entries,
            "recent_gpt_usage": gpt_entries
        }