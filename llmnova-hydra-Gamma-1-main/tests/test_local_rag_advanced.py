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
        sys.modules["sentence_transformers"].reset_mock()

        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_client.get_or_create_collection.return_value = self.mock_collection

        # Configure query return mock
        # ChromaDB query returns: {'ids': [...], 'distances': [...], 'metadatas': [[...]], 'embeddings': None, 'documents': [[...]]}
        self.mock_collection.query.return_value = {
            'ids': [['doc1', 'doc2']],
            'distances': [[0.1, 0.2]],
            'metadatas': [[{'source': 'test_doc'}, {'source': 'test_doc_2'}]],
            'embeddings': None,
            'documents': [['This is a test content', 'Another content']]
        }

    @patch("gamma_engine.core.rag.local.chromadb.PersistentClient")
    @patch("gamma_engine.core.rag.local.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("gamma_engine.core.rag.local.CrossEncoder")
    def test_query_with_rerank(self, mock_reranker_cls, mock_emb_fn, mock_client_cls):
        # Setup mocks
        mock_client_cls.return_value = self.mock_client
        mock_reranker = MagicMock()
        mock_reranker_cls.return_value = mock_reranker
        # Mock reranker.predict to return scores where the second doc (index 1) is better than first (index 0)
        # Docs: ['This is a test content', 'Another content']
        # Scores: [0.1, 0.9] -> 'Another content' should be first after sort
        mock_reranker.predict.return_value = [0.1, 0.9]

        with patch("gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS", True):
            provider = LocalRAGProvider()
            provider.create_or_get_corpus("test_corpus")

            results = provider.query_rag_corpus("test_corpus", "test query", num_results=2)

            self.assertEqual(len(results), 2)
            # Verify Reranker was called
            mock_reranker.predict.assert_called_once()

            # Verify sorting: 'Another content' (score 0.9) should be first
            self.assertEqual(results[0]['content'], 'Another content')
            self.assertEqual(results[0]['score'], 0.9)
            self.assertEqual(results[1]['content'], 'This is a test content')
            self.assertEqual(results[1]['score'], 0.1)

    @patch("gamma_engine.core.rag.local.chromadb.PersistentClient")
    @patch("gamma_engine.core.rag.local.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch("gamma_engine.core.rag.local.extract_text_from_file")
    def test_upload_chunking(self, mock_extract, mock_emb_fn, mock_client_cls):
        mock_client_cls.return_value = self.mock_client
        # Create a text larger than 1000 chars to test splitting
        large_text = "A" * 1500
        mock_extract.return_value = large_text

        with patch("gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS", True):
            provider = LocalRAGProvider()
            provider.create_or_get_corpus("test_corpus")

            provider.upload_document_to_corpus("test_corpus", "fake.txt", "large_doc")

            self.mock_collection.add.assert_called_once()
            args, kwargs = self.mock_collection.add.call_args
            # Should be split into 2 chunks (1000 + 500)
            self.assertEqual(len(kwargs['documents']), 2)
            self.assertEqual(len(kwargs['documents'][0]), 1000)
            self.assertEqual(len(kwargs['documents'][1]), 500)

if __name__ == "__main__":
    unittest.main()
