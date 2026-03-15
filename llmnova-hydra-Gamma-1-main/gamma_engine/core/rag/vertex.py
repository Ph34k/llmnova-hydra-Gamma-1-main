import os
from typing import List, Dict, Any, Optional

from google.cloud import aiplatform
from google.api_core.exceptions import GoogleAPIError

from gamma_engine.core.logger import logger
from gamma_engine.tools.document_processor import extract_text_from_file
from gamma_engine.core.rag.base import RAGProvider

class VertexRAGProvider(RAGProvider):
    """
    RAG Provider implementation using Google Cloud Vertex AI.
    """
    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        self._is_configured = False

        if not self.project_id or not self.location:
            logger.warning("Vertex AI RAG Service is not fully configured. Please set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment variables.")
        else:
            self._is_configured = True
            try:
                self.client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
                self.aiplatform_client = aiplatform.gapic.IndexServiceClient(client_options=self.client_options)
                self.rag_client = aiplatform.gapic.RagServiceClient(client_options=self.client_options)
                logger.info(f"Vertex AI RAG Service initialized for project {self.project_id} in {self.location}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI Client: {e}")
                self._is_configured = False

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def create_or_get_corpus(self, display_name: str) -> Optional[str]:
        if not self.is_configured:
            logger.error("Vertex RAG Provider not configured.")
            return None

        parent = f"projects/{self.project_id}/locations/{self.location}"
        try:
            list_response = self.rag_client.list_corpora(parent=parent)
            for corpus in list_response:
                if corpus.display_name == display_name:
                    logger.info(f"Found existing Vertex RAG corpus: {corpus.name}")
                    return corpus.name
        except GoogleAPIError as e:
            logger.error(f"Error listing RAG corpora: {e}")
            return None

        try:
            corpus = aiplatform.gapic.Corpus(display_name=display_name)
            create_request = aiplatform.gapic.CreateCorpusRequest(parent=parent, corpus=corpus)
            operation = self.rag_client.create_corpus(request=create_request)
            logger.info(f"Creating RAG corpus: {display_name}...")
            response = operation.result()
            logger.info(f"Vertex RAG corpus created: {response.name}")
            return response.name
        except GoogleAPIError as e:
            logger.error(f"Error creating RAG corpus '{display_name}': {e}")
            return None

    def upload_document_to_corpus(self, corpus_name: str, file_path: str, display_name: str) -> Optional[str]:
        if not self.is_configured:
            logger.error("Vertex RAG Provider not configured.")
            return None

        try:
            text_content = extract_text_from_file(file_path)
            if text_content.startswith("Error:"):
                logger.error(f"Failed to extract text from {file_path}: {text_content}")
                return None

            rag_file = aiplatform.gapic.RagFile(display_name=display_name, inline_content=text_content)
            create_request = aiplatform.gapic.CreateRagFileRequest(parent=corpus_name, rag_file=rag_file)
            operation = self.rag_client.create_rag_file(request=create_request)
            response = operation.result()
            logger.info(f"Document '{display_name}' uploaded to Vertex RAG corpus: {response.name}")
            return response.name
        except GoogleAPIError as e:
            logger.error(f"Error uploading document '{display_name}' to Vertex RAG corpus '{corpus_name}': {e}")
            return None

    def query_rag_corpus(self, corpus_name: str, query_text: str, num_results: int = 5) -> List[Dict[str, Any]]:
        if not self.is_configured:
            logger.error("Vertex RAG Provider not configured.")
            return []

        try:
            rag_resource = aiplatform.gapic.RagResource(
                rag_corpus=corpus_name,
            )

            retrieve_request = aiplatform.gapic.RetrieveRagContentsRequest(
                parent=f"projects/{self.project_id}/locations/{self.location}",
                rag_resources=[rag_resource],
                query_text=query_text,
            )

            response = self.rag_client.retrieve_rag_contents(request=retrieve_request)

            results = []
            for part in response.retrieved_rag_contents:
                for chunk in part.chunks:
                    results.append({
                        "content": chunk.content,
                        "source_uri": chunk.source_uri,
                        "display_name": chunk.display_name
                    })
            logger.info(f"Vertex RAG query for '{query_text}' returned {len(results)} results.")
            return results
        except GoogleAPIError as e:
            logger.error(f"Error querying Vertex RAG corpus '{corpus_name}': {e}")
            return []
