import os
import shutil
from typing import List, Dict, Any, Optional

from gamma_engine.core.logger import logger
from gamma_engine.tools.document_processor import extract_text_from_file
from gamma_engine.core.rag.base import RAGProvider

try:
    import chromadb
    from chromadb.utils import embedding_functions
    from sentence_transformers import CrossEncoder, SentenceTransformer
    HAS_LOCAL_RAG_DEPS = True
except ImportError:
    HAS_LOCAL_RAG_DEPS = False
    logger.warning("Local RAG dependencies (chromadb, sentence-transformers) not found. Local RAG will be disabled.")


class LocalRAGProvider(RAGProvider):
    """
    RAG Provider implementation using ChromaDB and Sentence Transformers.
    Mimics legacy Hydra local RAG capabilities with added re-ranking.
    """
    def __init__(self, persistence_path: str = "./chroma_db", collection_name: str = "gamma_knowledge_base"):
        self.persistence_path = persistence_path
        self.collection_name = collection_name
        self._is_configured = False
        self.client = None
        self.collection = None
        self.embedding_fn = None
        self.reranker = None

        if HAS_LOCAL_RAG_DEPS:
            try:
                # Initialize ChromaDB Client
                self.client = chromadb.PersistentClient(path=self.persistence_path)

                # Initialize Embedding Function (bi-encoder for retrieval)
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )

                # Initialize Re-ranker (cross-encoder for precision)
                # Using a small, fast model for CPU inference
                try:
                    self.reranker = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2-v2')
                    logger.info("Local RAG: Re-ranker initialized.")
                except Exception as e:
                    logger.warning(f"Local RAG: Could not initialize re-ranker ({e}). Using retrieval only.")

                self._is_configured = True
                logger.info(f"Local RAG Provider initialized at {self.persistence_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Local RAG Provider: {e}")
                self._is_configured = False
        else:
            logger.warning("Local RAG Provider disabled due to missing dependencies.")

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def create_or_get_corpus(self, display_name: str) -> Optional[str]:
        if not self.is_configured:
            logger.error("Local RAG Provider not configured.")
            return None

        try:
            self.collection = self.client.get_or_create_collection(
                name=display_name,
                embedding_function=self.embedding_fn
            )
            logger.info(f"Local RAG collection '{display_name}' ready.")
            return display_name
        except Exception as e:
            logger.error(f"Error getting/creating local RAG collection '{display_name}': {e}")
            return None

    def upload_document_to_corpus(self, corpus_name: str, file_path: str, display_name: str) -> Optional[str]:
        if not self.is_configured:
            logger.error("Local RAG Provider not configured.")
            return None

        if not self.collection or self.collection.name != corpus_name:
             self.create_or_get_corpus(corpus_name)

        if not self.collection:
             return None

        try:
            text_content = extract_text_from_file(file_path)
            if text_content.startswith("Error:"):
                logger.error(f"Failed to extract text from {file_path}: {text_content}")
                return None

            # Improved Chunking: Split by paragraphs, then ensure chunks aren't too massive
            raw_chunks = [c.strip() for c in text_content.split('\n\n') if c.strip()]
            chunks = []
            for chunk in raw_chunks:
                if len(chunk) > 1000:
                    # Naive split for very large paragraphs
                    chunks.extend([chunk[i:i+1000] for i in range(0, len(chunk), 1000)])
                else:
                    chunks.append(chunk)

            ids = [f"{display_name}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": display_name, "chunk_index": i} for i in range(len(chunks))]

            self.collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas
            )

            logger.info(f"Document '{display_name}' ({len(chunks)} chunks) added to local RAG collection '{corpus_name}'.")
            return display_name
        except Exception as e:
            logger.error(f"Error uploading document '{display_name}' to local RAG: {e}")
            return None

    def query_rag_corpus(self, corpus_name: str, query_text: str, num_results: int = 5) -> List[Dict[str, Any]]:
        if not self.is_configured:
            logger.error("Local RAG Provider not configured.")
            return []

        if not self.collection or self.collection.name != corpus_name:
             self.create_or_get_corpus(corpus_name)

        if not self.collection:
             return []

        try:
            # 1. Retrieval (fetch more candidates than needed for re-ranking)
            initial_k = num_results * 3 if self.reranker else num_results
            results = self.collection.query(
                query_texts=[query_text],
                n_results=initial_k
            )

            documents = results['documents'][0]
            metadatas = results['metadatas'][0]

            candidates = []
            for i, doc in enumerate(documents):
                meta = metadatas[i] if metadatas else {}
                candidates.append({
                    "content": doc,
                    "source_uri": meta.get('source', 'unknown'),
                    "display_name": meta.get('source', 'unknown')
                })

            # 2. Re-ranking (if enabled)
            if self.reranker and candidates:
                pairs = [[query_text, c['content']] for c in candidates]
                scores = self.reranker.predict(pairs)

                # Attach scores
                for i, c in enumerate(candidates):
                    c['score'] = float(scores[i])

                # Sort by score descending
                candidates.sort(key=lambda x: x['score'], reverse=True)

                logger.info(f"Re-ranked {len(candidates)} candidates.")

            # 3. Limit Results
            final_results = candidates[:num_results]

            logger.info(f"Local RAG query for '{query_text}' returned {len(final_results)} results.")
            return final_results

        except Exception as e:
            logger.error(f"Error querying local RAG corpus '{corpus_name}': {e}")
            return []
