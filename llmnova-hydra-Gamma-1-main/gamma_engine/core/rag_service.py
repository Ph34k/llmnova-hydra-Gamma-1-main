import os
from typing import List, Dict, Any
from google.cloud import aiplatform
from google.api_core.exceptions import NotFound, GoogleAPIError
from gamma_engine.core.logger import logger
from gamma_engine.tools.document_processor import extract_text_from_file

class RAGService:
    """
    Service for interacting with Google Cloud Vertex AI RAG (Retrieval-Augmented Generation).
    Manages corpus creation, document upload, and querying.
    """
    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        self.client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        self.aiplatform_client = aiplatform.gapic.IndexServiceClient(client_options=self.client_options)
        self.rag_client = aiplatform.gapic.RagServiceClient(client_options=self.client_options)
        
        if not self.project_id or not self.location:
            logger.warning("Vertex AI RAG Service is not fully configured. Please set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment variables.")
            self.is_configured = False
        else:
            self.is_configured = True
            logger.info(f"Vertex AI RAG Service initialized for project {self.project_id} in {self.location}")

    def _get_corpus_path(self, corpus_id: str) -> str:
        return self.rag_client.corpus_path(self.project_id, self.location, corpus_id)

    def create_or_get_corpus(self, display_name: str) -> str:
        """
        Creates a new RAG corpus or retrieves an existing one by display name.
        Returns the resource name of the corpus.
        """
        if not self.is_configured:
            logger.error("RAG Service not configured. Cannot create or get corpus.")
            return None

        parent = f"projects/{self.project_id}/locations/{self.location}"
        try:
            list_response = self.rag_client.list_corpora(parent=parent)
            for corpus in list_response:
                if corpus.display_name == display_name:
                    logger.info(f"Found existing RAG corpus: {corpus.name}")
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
            logger.info(f"RAG corpus created: {response.name}")
            return response.name
        except GoogleAPIError as e:
            logger.error(f"Error creating RAG corpus '{display_name}': {e}")
            return None

    def upload_document_to_corpus(self, corpus_name: str, file_path: str, display_name: str) -> str:
        """
        Uploads a local document to a specified RAG corpus by extracting its text content.
        Returns the resource name of the uploaded document.
        """
        if not self.is_configured:
            logger.error("RAG Service not configured. Cannot upload document.")
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
            logger.info(f"Document '{display_name}' uploaded to RAG corpus: {response.name}")
            return response.name
        except GoogleAPIError as e:
            logger.error(f"Error uploading document '{display_name}' to RAG corpus '{corpus_name}': {e}")
            return None

    def query_rag_corpus(self, corpus_name: str, query_text: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Queries the RAG corpus for relevant information based on the query text.
        Returns a list of retrieved passages.
        """
        if not self.is_configured:
            logger.error("RAG Service not configured. Cannot query corpus.")
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
            logger.info(f"RAG query for '{query_text}' returned {len(results)} results.")
            return results
        except GoogleAPIError as e:
            logger.error(f"Error querying RAG corpus '{corpus_name}': {e}")
            return []
