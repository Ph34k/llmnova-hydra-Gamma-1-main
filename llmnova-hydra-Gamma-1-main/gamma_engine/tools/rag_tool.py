"""Tool for querying the RAG (Retrieval-Augmented Generation) service."""

import os
from typing import List, Dict, Any

from ..base import Tool
from ..core.rag_service import RAGService
from ..core.logger import logger

class KnowledgeBaseSearchTool(Tool):
    """
    A tool to search a RAG-powered knowledge base for relevant information.
    """

    def __init__(self, rag_service: RAGService, corpus_display_name: str = "default-gamma-corpus"):
        super().__init__(
            name="knowledge_base_search",
            description=(
                "Searches a RAG-powered knowledge base for information relevant to a query. "
                "Use this tool to retrieve detailed context from indexed documents. "
                "Returns passages of text that are most relevant to the query."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search the knowledge base with."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "The maximum number of relevant passages to retrieve. Defaults to 3."
                    }
                },
                "required": ["query"]
            }
        )
        self.rag_service = rag_service
        self.corpus_display_name = corpus_display_name
        self.corpus_name = None # Will be set after corpus is created/retrieved

    def _initialize_corpus(self):
        """Ensures the RAG corpus is created or retrieved."""
        if not self.corpus_name and self.rag_service.is_configured:
            self.corpus_name = self.rag_service.create_or_get_corpus(self.corpus_display_name)
            if not self.corpus_name:
                logger.error(f"Failed to initialize RAG corpus '{self.corpus_display_name}'. RAG tool will be disabled.")
                self.rag_service.is_configured = False # Disable if corpus init fails

    def execute(self, query: str, num_results: int = 3) -> str:
        """
        Executes the knowledge base search.

        Args:
            query: The query to search the knowledge base with.
            num_results: The maximum number of relevant passages to retrieve.

        Returns:
            A formatted string of retrieved passages or an error message.
        """
        self._initialize_corpus() # Ensure corpus is ready

        if not self.rag_service.is_configured or not self.corpus_name:
            return "Error: KnowledgeBaseSearchTool is not configured or corpus not initialized. Please check RAG service configuration."

        try:
            results = self.rag_service.query_rag_corpus(self.corpus_name, query, num_results)
            
            if not results:
                return f"No relevant information found in the knowledge base for '{query}'."

            output = [f"Information from knowledge base for '{query}':\n"]
            for i, item in enumerate(results, 1):
                output.append(f"{i}. Source: {item.get('source_uri', 'N/A')}\n   Content: {item['content']}\n")

            return "\n".join(output)
        except Exception as e:
            logger.error(f"An error occurred during knowledge base search: {e}")
            return f"An error occurred during the knowledge base search: {e}"

