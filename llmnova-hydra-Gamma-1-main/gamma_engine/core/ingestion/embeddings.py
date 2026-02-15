
from abc import ABC, abstractmethod
from typing import List, Optional

class EmbeddingService(ABC):
    @abstractmethod
    def embed_text(self, texts: List[str]) -> List[List[float]]:
        pass

class SentenceTransformerEmbeddings(EmbeddingService):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            print("Error: sentence-transformers not installed.")
            self.model = None

    def embed_text(self, texts: List[str]) -> List[List[float]]:
        if self.model:
            return self.model.encode(texts).tolist()
        return []

class OpenAIEmbeddings(EmbeddingService):
    def __init__(self, model: str = "text-embedding-ada-002", api_key: str = None):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            print("Error: openai not installed.")
            self.client = None

    def embed_text(self, texts: List[str]) -> List[List[float]]:
        if self.client:
            response = self.client.embeddings.create(input=texts, model=self.model)
            return [d.embedding for d in response.data]
        return []
