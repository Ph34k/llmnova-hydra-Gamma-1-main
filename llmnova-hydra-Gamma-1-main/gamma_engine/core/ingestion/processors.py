
import re
from typing import List

class TextProcessor:
    @staticmethod
    def clean_text(text: str) -> str:
        # Basic cleaning: remove extra whitespace, normalize newlines
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        # Simple overlap chunking
        chunks = []
        if not text:
            return chunks

        cleaned = TextProcessor.clean_text(text)
        words = cleaned.split()

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunks.append(" ".join(chunk_words))

        return chunks

class SemanticProcessor(TextProcessor):
    # Future enhancement: use spacy for sentence boundary detection
    pass
