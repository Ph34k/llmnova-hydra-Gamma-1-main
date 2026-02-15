import os
import shutil
import unittest
from unittest.mock import MagicMock, patch
import sys

# Ensure gamma_engine is in path
sys.path.append(os.path.join(os.getcwd(), 'llmnova-hydra-Gamma-1-main'))

# Mock local RAG dependencies before importing LocalRAGProvider
# We need to mock 'chromadb' and 'sentence_transformers' to avoid ImportError in LocalRAGProvider
# which checks for their existence.
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.utils"] = MagicMock()
sys.modules["chromadb.utils.embedding_functions"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()

# Patch ingestion modules
sys.modules["gamma_engine.core.ingestion.vector_store"] = MagicMock()
sys.modules["gamma_engine.core.ingestion.embeddings"] = MagicMock()
sys.modules["gamma_engine.core.ingestion.loaders"] = MagicMock()
sys.modules["gamma_engine.core.ingestion.processors"] = MagicMock()

from gamma_engine.core.rag.local import LocalRAGProvider

class TestLocalRAG(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        sys.modules["chromadb"].reset_mock()

        # Setup common return values
        self.mock_vector_store = MagicMock()
        self.mock_embedder = MagicMock()
        self.mock_loader = MagicMock()

    @patch("gamma_engine.core.rag.local.ChromaVectorStore")
    @patch("gamma_engine.core.rag.local.SentenceTransformerEmbeddings")
    def test_initialization(self, mock_embed_cls, mock_store_cls):
        mock_embed_cls.return_value = self.mock_embedder
        mock_store_cls.return_value = self.mock_vector_store

        with patch.object(LocalRAGProvider, 'is_configured', True):
            # Since HAS_LOCAL_RAG_DEPS is a module-level constant that was evaluated at import time,
            # patching it via string 'gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS' is tricky if already imported.
            # However, for this test, we are mocking the classes that LocalRAGProvider uses.

            # Re-reload module to apply HAS_LOCAL_RAG_DEPS patch if needed, or just rely on mocked imports above.
            # Because we mocked sys.modules["chromadb"], ImportError won't happen, so HAS_LOCAL_RAG_DEPS should be True.

            provider = LocalRAGProvider()
            # If initialization succeeds, it means deps were found (mocked)
            self.assertTrue(provider.is_configured)
            mock_embed_cls.assert_called_once()
            mock_store_cls.assert_called_once()

    @patch("gamma_engine.core.rag.local.ChromaVectorStore")
    @patch("gamma_engine.core.rag.local.SentenceTransformerEmbeddings")
    @patch("gamma_engine.core.rag.local.LoaderFactory")
    @patch("gamma_engine.core.rag.local.TextProcessor")
    def test_upload_document(self, mock_processor, mock_factory, mock_embed_cls, mock_store_cls):
        # Setup logic mocks
        mock_embed_cls.return_value = self.mock_embedder
        self.mock_embedder.model = MagicMock()
        mock_store_cls.return_value = self.mock_vector_store

        mock_loader = MagicMock()
        mock_loader.load.return_value = "Test Content"
        mock_factory.get_loader.return_value = mock_loader

        mock_processor.chunk_text.return_value = ["Test Content"]

        provider = LocalRAGProvider()
        provider.upload_document_to_corpus("test_corpus", "test.txt", "doc1")

        # Verify pipeline calls
        mock_factory.get_loader.assert_called_with("test.txt")
        mock_loader.load.assert_called_with("test.txt")
        mock_processor.chunk_text.assert_called()
        self.mock_vector_store.add_texts.assert_called()

    @patch("gamma_engine.core.rag.local.ChromaVectorStore")
    @patch("gamma_engine.core.rag.local.SentenceTransformerEmbeddings")
    def test_query(self, mock_embed_cls, mock_store_cls):
        mock_embed_cls.return_value = self.mock_embedder
        self.mock_embedder.model = MagicMock()
        mock_store_cls.return_value = self.mock_vector_store

        # Mock search results
        self.mock_vector_store.similarity_search.return_value = {
            'documents': [['Result Content']],
            'metadatas': [[{'source': 'doc1'}]]
        }

        provider = LocalRAGProvider()
        results = provider.query_rag_corpus("test_corpus", "query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['content'], 'Result Content')
        self.mock_vector_store.similarity_search.assert_called_with("query", k=5)

if __name__ == "__main__":
    unittest.main()
