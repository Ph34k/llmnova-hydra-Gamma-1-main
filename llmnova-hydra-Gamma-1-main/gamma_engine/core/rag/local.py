import os
import shutil
from typing import List, Dict, Any, Optional

from gamma_engine.core.logger import logger
from gamma_engine.core.rag.base import RAGProvider

# New Modular Ingestion Components
from gamma_engine.core.ingestion.loaders import LoaderFactory
from gamma_engine.core.ingestion.processors import TextProcessor, SemanticProcessor
from gamma_engine.core.ingestion.embeddings import SentenceTransformerEmbeddings
from gamma_engine.core.ingestion.vector_store import ChromaVectorStore

class LocalRAGProvider(RAGProvider):
    """
    RAG Provider implementation using ChromaDB and Sentence Transformers.
    Refactored to use the new modular Ingestion Pipeline.
    """
    def __init__(self, persistence_path: str = "./chroma_db", collection_name: str = "gamma_knowledge_base"):
        self.persistence_path = persistence_path
        self.collection_name = collection_name
        self._is_configured = False

        try:
            # Initialize Pipeline Components
            self.embedder = SentenceTransformerEmbeddings()
            if self.embedder.model:
                self.vector_store = ChromaVectorStore(
                    collection_name=collection_name,
                    embedding_function=self.embedder.model.encode, # Pass raw embedding fn
                    persist_directory=persistence_path
                )
                self._is_configured = True
                logger.info(f"Local RAG Provider (Modular) initialized at {self.persistence_path}")
            else:
                self._is_configured = False
                logger.warning("Embedding model failed to load.")

        except Exception as e:
            logger.error(f"Failed to initialize Local RAG Provider: {e}")
            self._is_configured = False

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def create_or_get_corpus(self, display_name: str) -> Optional[str]:
        # Chroma handles get_or_create internally
        return display_name

    def upload_document_to_corpus(self, corpus_name: str, file_path: str, display_name: str) -> Optional[str]:
        if not self.is_configured:
            return None

        try:
            # 1. Load
            loader = LoaderFactory.get_loader(file_path)
            raw_text = loader.load(file_path)

            # 2. Process / Chunk
            chunks = TextProcessor.chunk_text(raw_text, chunk_size=500, overlap=50)

            # 3. Store
            ids = [f"{display_name}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": display_name, "chunk_index": i} for i in range(len(chunks))]

            self.vector_store.add_texts(
                texts=chunks,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Document '{display_name}' ({len(chunks)} chunks) ingested via pipeline.")
            return display_name

        except Exception as e:
            logger.error(f"Ingestion pipeline error for '{display_name}': {e}")
            return None

    def query_rag_corpus(self, corpus_name: str, query_text: str, num_results: int = 5) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []

        try:
            results = self.vector_store.similarity_search(query_text, k=num_results)

            # Reformat Chroma output
            formatted_results = []
            if 'documents' in results and results['documents']:
                docs = results['documents'][0]
                metas = results['metadatas'][0] if 'metadatas' in results else []

                for i, doc in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    formatted_results.append({
                        "content": doc,
                        "source_uri": meta.get('source', 'unknown'),
                        "display_name": meta.get('source', 'unknown'),
                        "vector_score": 0.0 # Placeholder
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Query error: {e}")
            return []
