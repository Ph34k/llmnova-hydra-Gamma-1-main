
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    @abstractmethod
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None, ids: List[str] = None):
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name: str, embedding_function, persist_directory: str = "./chroma_db"):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
        except ImportError:
            print("Error: chromadb not installed.")
            self.client = None

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None, ids: List[str] = None):
        if self.client:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if self.client:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            return results
        return []
