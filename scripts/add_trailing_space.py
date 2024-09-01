from post_processing_base import PostProcessor
from typing import Dict


class Processor(PostProcessor):
    def process(self, transcription: Dict) -> Dict:
        text = transcription.get('processed', transcription.get('raw_text', ''))
        processed_text = text + ' ' if text else ''
        transcription['processed'] = processed_text
        return transcription
