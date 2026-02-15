from gamma_engine.core.rag.vertex import VertexRAGProvider
from gamma_engine.core.rag.local import LocalRAGProvider
from gamma_engine.core.rag.base import RAGProvider

# Backward compatibility alias
RAGService = VertexRAGProvider

def get_rag_provider(provider_type: str = "vertex", **kwargs) -> RAGProvider:
    """Factory function to get the appropriate RAG provider."""
    if provider_type.lower() == "local":
        return LocalRAGProvider(**kwargs)
    else:
        # Default to Vertex for backward compatibility
        return VertexRAGProvider(**kwargs)
