
import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), 'llmnova-hydra-Gamma-1-main'))

# Mock Dependencies for Integration
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.utils"] = MagicMock()
sys.modules["chromadb.utils.embedding_functions"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.aiplatform"] = MagicMock()

# Import core components to verify
from gamma_engine.core.rag.local import LocalRAGProvider
from gamma_engine.core.training.base import LocalTrainer
from fastapi.testclient import TestClient
from gamma_server import app

class TestFullSystem(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.rag = LocalRAGProvider() # Using mock internally
        self.trainer = LocalTrainer()

    def test_01_system_status(self):
        """Step 1: Verify System Status (Frontend Dashboard Data)"""
        print("\n[Step 1] Checking System Status API...")
        response = self.client.get("/api/system/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print(f" -> System Status: {data['status']}, CPU: {data['cpu_percent']}%")
        self.assertEqual(data['status'], 'online')

    @patch("gamma_engine.core.rag.local.chromadb.PersistentClient")
    @patch("gamma_engine.core.rag.local.embedding_functions.SentenceTransformerEmbeddingFunction")
    def test_02_rag_ingestion_query(self, mock_emb, mock_client):
        """Step 2 & 3: Simulate RAG Ingestion and Query"""
        print("\n[Step 2] Simulating RAG Ingestion...")
        # Mock client behavior
        mock_col = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_col

        with patch("gamma_engine.core.rag.local.HAS_LOCAL_RAG_DEPS", True):
            provider = LocalRAGProvider()
            with patch("gamma_engine.core.rag.local.extract_text_from_file", return_value="Hydra Legacy Content"):
                provider.upload_document_to_corpus("test_corpus", "legacy.txt", "hydra_doc")
                mock_col.add.assert_called()
                print(" -> Document ingested successfully.")

            print("\n[Step 3] Simulating RAG Query...")
            mock_col.query.return_value = {
                'ids': [['1']], 'distances': [[0.1]], 'metadatas': [[{'source': 'hydra_doc'}]],
                'documents': [['Hydra Legacy Content']]
            }
            results = provider.query_rag_corpus("test_corpus", "legacy")
            self.assertEqual(len(results), 1)
            print(f" -> Query returned: {results[0]['content']}")

    def test_04_training_trigger(self):
        """Step 4: Simulate Training Job Trigger"""
        print("\n[Step 4] Triggering Mock Training Job...")
        metrics = self.trainer.train("dataset.csv", "llama-2", "output/model")
        self.assertEqual(metrics['status'], 'mock_success')
        print(f" -> Training Job Completed. Metrics: {metrics}")

if __name__ == "__main__":
    unittest.main()
