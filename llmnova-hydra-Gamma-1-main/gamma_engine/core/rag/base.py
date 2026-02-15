from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class RAGProvider(ABC):
    """
    Abstract Base Class for RAG Providers (e.g., Vertex AI, Local ChromaDB).
    This interface unifies the retrieval logic for the agent.
    """

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider is fully configured and ready."""
        pass

    @abstractmethod
    def create_or_get_corpus(self, display_name: str) -> Optional[str]:
        """
        Creates a new corpus/collection or retrieves an existing one.
        Returns the corpus identifier (e.g., name, ID).
        """
        pass

    @abstractmethod
    def upload_document_to_corpus(self, corpus_name: str, file_path: str, display_name: str) -> Optional[str]:
        """
        Uploads a document to the specified corpus.
        Returns the document identifier.
        """
        pass

    @abstractmethod
    def query_rag_corpus(self, corpus_name: str, query_text: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Queries the corpus for relevant information.
        Returns a list of retrieved passages.
        """
        pass
