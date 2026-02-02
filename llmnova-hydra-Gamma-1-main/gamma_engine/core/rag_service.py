import os
from typing import List, Dict, Any
from google.cloud import aiplatform
from google.api_core.exceptions import NotFound, GoogleAPIError
from gamma_engine.core.logger import logger

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

        # List existing corpora to check if one with the display_name already exists
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

        # If not found, create a new one
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

    def upload_document_to_corpus(self, corpus_name: str, document_path: str, display_name: str) -> str:
        """
        Uploads a local document to a specified RAG corpus.
        Returns the resource name of the uploaded document.
        """
        if not self.is_configured:
            logger.error("RAG Service not configured. Cannot upload document.")
            return None

        try:
            # For local files, we need to upload them to GCS first or use a direct upload method if available.
            # Vertex AI RAG typically expects GCS URIs for batch uploads.
            # For simplicity in this example, we'll assume a direct file content upload or a pre-uploaded GCS URI.
            # The actual implementation might involve uploading to GCS from the server.
            
            # This is a placeholder for actual document upload logic.
            # Vertex AI RAG's `create_rag_file` expects a GCS URI or direct content.
            # For a local file, you'd typically upload it to GCS first.
            # For now, we'll simulate or use a simplified approach.
            
            # Example: Assuming document_path is a local file, we'd need to upload it to GCS
            # and then pass the GCS URI.
            # For direct content, the API might have a method like `create_rag_file_from_content`.
            
            # Placeholder: In a real scenario, you'd upload `document_path` to GCS
            # and then create a RagFile with `gcs_uri`.
            
            # For demonstration, let's assume we can pass the local file path and it's handled
            # or we're using a simplified API that accepts local paths (which is not standard for batch).
            # A more robust solution would involve `google.cloud.storage` to upload to GCS.
            
            # For now, let's assume a direct content upload if the API supports it, or
            # we'll need to add GCS upload logic.
            
            # As a simplified example, let's assume the document content is directly passed
            # or the API has a way to ingest local files.
            # The `create_rag_file` method expects a `RagFile` object.
            # `RagFile` has `gcs_uri` or `inline_content`.
            
            # For this example, let's assume we're providing a GCS URI.
            # In a real app, you'd upload `document_path` to GCS and get its URI.
            
            # For now, let's just log and return a dummy name.
            logger.warning(f"Simulating document upload to RAG corpus {corpus_name}. Actual GCS upload logic is needed.")
            logger.info(f"Document '{display_name}' from '{document_path}' would be uploaded.")
            
            # In a real scenario, this would be:
            # rag_file = aiplatform.gapic.RagFile(display_name=display_name, gcs_uri="gs://your-bucket/your-document.pdf")
            # create_request = aiplatform.gapic.CreateRagFileRequest(parent=corpus_name, rag_file=rag_file)
            # operation = self.rag_client.create_rag_file(request=create_request)
            # response = operation.result()
            # logger.info(f"Document uploaded: {response.name}")
            # return response.name
            
            return f"projects/{self.project_id}/locations/{self.location}/corpora/{corpus_name.split('/')[-1]}/ragFiles/dummy_file_{os.path.basename(document_path)}"
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
            # The `retrieve_rag_contents` method is used for querying.
            # It expects a list of `RagResource` objects.
            rag_resource = aiplatform.gapic.RagResource(
                rag_corpus=corpus_name,
                # You can also specify `rag_file_ids` if you want to query specific files within the corpus
            )
            
            retrieve_request = aiplatform.gapic.RetrieveRagContentsRequest(
                parent=f"projects/{self.project_id}/locations/{self.location}",
                rag_resources=[rag_resource],
                query_text=query_text,
                # You can specify `similarity_top_k` for number of passages
                # `chunk_size` for how much content per passage
            )
            
            response = self.rag_client.retrieve_rag_contents(request=retrieve_request)
            
            results = []
            for part in response.retrieved_rag_contents:
                for chunk in part.chunks:
                    results.append({
                        "content": chunk.content,
                        "source_uri": chunk.source_uri, # This might be GCS URI
                        "display_name": chunk.display_name # This might be the document display name
                    })
            logger.info(f"RAG query for '{query_text}' returned {len(results)} results.")
            return results
        except GoogleAPIError as e:
            logger.error(f"Error querying RAG corpus '{corpus_name}': {e}")
            return []

