
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

from gamma_engine.core.rag.local import LocalRAGProvider

class TestLocalRAG(unittest.TestCase):
    def setUp(self):
        # Reset mocks before each test
        sys.modules["chromadb"].reset_mock()
        sys.modules["chromadb.utils.embedding_functions"].reset_mock()

        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_client.get_or_create_collection.return_value = self.mock_collection

        # Configure query return mock
        # ChromaDB query returns: {'ids': [...], 'distances': [...], 'metadatas': [[...]], 'embeddings': None, 'documents': [[...]]}
        self.mock_collection.query.return_value = {
            'ids': [['doc1']],
            'distances': [[0.1]],
            'metadatas': [[{'source': 'test_doc'}]],
            'embeddings': None,
            'documents': [['This is a test content']]
        }

    @patch("gamma_engine.core.rag.local.chromadb.PersistentClient")
    @patch("gamma_engine.core.rag.local.embedding_functions.SentenceTransformerEmbeddingFunction")
    def test_initialization(self, mock_emb_fn, mock_client_cls):
        # Setup return values for the patches
        mock_client_cls.return_value = self.mock_client

        # Force HAS_LOCAL_RAG_DEPS to be True for the test context
        with patch("gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS", True):
            provider = LocalRAGProvider()
            self.assertTrue(provider.is_configured)
            mock_client_cls.assert_called_once()

    @patch("gamma_engine.core.rag.local.chromadb.PersistentClient")
    @patch("gamma_engine.core.rag.local.embedding_functions.SentenceTransformerEmbeddingFunction")
    def test_create_corpus(self, mock_emb_fn, mock_client_cls):
        mock_client_cls.return_value = self.mock_client

        with patch("gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS", True):
            provider = LocalRAGProvider()

            name = provider.create_or_get_corpus("test_corpus")
            self.assertEqual(name, "test_corpus")
            # We check if get_or_create_collection was called on the CLIENT instance
            self.mock_client.get_or_create_collection.assert_called()

    @patch("gamma_engine.core.rag.local.chromadb.PersistentClient")
    @patch("gamma_engine.core.rag.local.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("gamma_engine.core.rag.local.extract_text_from_file")
    def test_upload_document(self, mock_extract, mock_emb_fn, mock_client_cls):
        mock_client_cls.return_value = self.mock_client
        mock_extract.return_value = "This is a test content"

        with patch("gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS", True):
            provider = LocalRAGProvider()
            provider.create_or_get_corpus("test_corpus")

            # We mock open() implicitly since extract_text_from_file is mocked
            res = provider.upload_document_to_corpus("test_corpus", "fake_path.txt", "test_doc")

            self.assertEqual(res, "test_doc")
            self.mock_collection.add.assert_called_once()

    @patch("gamma_engine.core.rag.local.chromadb.PersistentClient")
    @patch("gamma_engine.core.rag.local.embedding_functions.SentenceTransformerEmbeddingFunction")
    def test_query(self, mock_emb_fn, mock_client_cls):
        mock_client_cls.return_value = self.mock_client

        with patch("gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS", True):
            provider = LocalRAGProvider()
            provider.create_or_get_corpus("test_corpus")

            results = provider.query_rag_corpus("test_corpus", "test query")

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['content'], "This is a test content")
            self.mock_collection.query.assert_called_once()

if __name__ == "__main__":
    unittest.main()
