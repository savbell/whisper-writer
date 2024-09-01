from post_processing_base import PostProcessor
from typing import Dict


class Processor(PostProcessor):
    def process(self, transcription: Dict) -> Dict:
        text = transcription['processed']
        processed_text = text + ' ' if text else ''
        transcription['processed'] = processed_text
        return transcription
