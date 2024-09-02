from post_processing_base import PostProcessor
from typing import Dict

# The 'transcription' dictionary typically contains:
# - 'raw_text': The unprocessed transcription text.
# - 'processed': The post-processed transcription text.
# - 'is_utterance_end': Boolean indicating if this is the end of an utterance.
# - 'language': Detected or specified language of the audio.
# - 'error': Any error message (None if no error occurred).


class Processor(PostProcessor):
    def process(self, transcription: Dict) -> Dict:
        text = transcription['processed']
        processed_text = text + ' ' if text else ''
        transcription['processed'] = processed_text
        return transcription
