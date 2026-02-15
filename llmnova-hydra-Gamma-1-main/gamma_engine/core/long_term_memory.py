
import logging
from typing import Any, Dict, List, Optional
import datetime
from gamma_engine.core.config import settings
from gamma_engine.core.rag_service import get_rag_provider

logger = logging.getLogger(__name__)

# Singleton cache for RAG Provider to prevent per-session model reloading
_rag_provider_instance = None

def get_shared_rag_provider():
    global _rag_provider_instance
    if _rag_provider_instance is None:
        _rag_provider_instance = get_rag_provider(settings.rag_provider)
    return _rag_provider_instance

class LongTermMemory:
    """
    Manages the agent's long-term memory (L3) or semantic memory.
    This layer stores structured knowledge using the configured RAG Provider.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        # Use shared singleton provider based on global settings
        self.rag_provider = get_shared_rag_provider()
        self.corpus_name = f"ltm-{session_id}"

        # Ensure corpus exists
        if self.rag_provider and self.rag_provider.is_configured:
            self.rag_provider.create_or_get_corpus(self.corpus_name)
            logger.info(f"LongTermMemory initialized with RAG corpus: {self.corpus_name}")
        else:
            logger.warning("LongTermMemory: RAG Provider not available. Memory will be ephemeral.")

    def add_knowledge(self, content: str, source: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Adds new knowledge to the long-term memory via RAG ingestion.
        """
        if not content: return

        timestamp = datetime.datetime.now().isoformat()
        full_content = f"Source: {source} | Time: {timestamp}\n{content}"

        if self.rag_provider and self.rag_provider.is_configured:
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp:
                temp.write(full_content)
                temp_path = temp.name

            try:
                self.rag_provider.upload_document_to_corpus(self.corpus_name, temp_path, f"fact-{timestamp}")
                logger.info(f"Knowledge persisted to LTM: {content[:50]}...")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            logger.warning("LTM not configured, knowledge lost.")

    def retrieve_knowledge(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves relevant knowledge from long-term memory based on a query.
        """
        if self.rag_provider and self.rag_provider.is_configured:
            # Fixed: parameter name n_results vs num_results
            return self.rag_provider.query_rag_corpus(self.corpus_name, query, num_results=n_results)
        return []

    def clear(self) -> None:
        """Clears all knowledge (Not easily supported by all RAG providers, so we log warning)."""
        logger.warning("Clear LTM not fully supported by all RAG backends.")
