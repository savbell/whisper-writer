from post_processing_base import PostProcessor

class Processor(PostProcessor):
    def process(self, text: str) -> str:
        return text.capitalize()
