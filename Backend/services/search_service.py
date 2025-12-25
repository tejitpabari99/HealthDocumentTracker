"""
Search service layer for AI-powered document search operations.

Provides methods for:
- Query refinement with Azure OpenAI
- Document search with Azure AI Search
- Answer generation with Azure OpenAI
- SAS URL generation for secure document access
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import json
import os
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from Backend.config import (
    get_blob_service_client,
    get_search_client,
    get_openai_client,
    AZURE_STORAGE_CONTAINER_NAME_RAW,
)
from Backend.utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service class for AI-powered search operations."""
    
    @staticmethod
    def refine_query_with_openai(user_query: str) -> str:
        """
        Refine user query using Azure OpenAI to expand search terms.
        
        Args:
            user_query: Original user query
            
        Returns:
            JSON string with refined search phrases and filters
            
        Raises:
            Exception: If query refinement fails
        """
        try:
            logger.info(f"Refining query with OpenAI", extra={
                'custom_dimensions': {'query_length': len(user_query)}
            })
            openai_client = get_openai_client()
            
            system_query = """You are a query-expansion assistant. Input: a user's question. Output: a JSON with two fields:
        - "search_phrases": [list of concise search phrases and synonyms to use, prioritized]
        - "search_filters": { optional filters like "lab", "date_range" }
        Example:
        Input: "What are my iron levels?"
        Output:
        {
        "search_phrases": ["ferritin", "serum ferritin", "iron", "transferrin saturation", "Fe", "ferritin level"],
        "search_filters": {}
        }
        """
            
            refine_response = openai_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4'),
                messages=[
                    {"role": "system", "content": system_query},
                    {"role": "user", "content": user_query}
                ]
            )
            
            refined_query = refine_response.choices[0].message.content.strip()
            logger.debug(f"Query refined successfully: {refined_query[:100]}...")
            return refined_query
            
        except Exception as e:
            logger.error(f"Failed to refine query: {str(e)}", exc_info=True)
            raise Exception(f"Failed to refine query: {str(e)}")
    
    @staticmethod
    def search_documents(refined_query: str, user_id: Optional[str] = None, top: int = 1) -> Tuple[str, str, str, Optional[str]]:
        """
        Search indexed documents using Azure AI Search.
        
        Args:
            refined_query: Refined search query (JSON string or plain text)
            user_id: User ID to filter documents (optional, currently not used due to index schema)
            top: Number of top results to return
            
        Returns:
            Tuple of (extracted_text, blob_uri, file_name, document_id)
            
        Raises:
            Exception: If search fails
        """
        try:
            logger.info(f"Searching documents in Azure AI Search", extra={
                'custom_dimensions': {'top': top, 'user_id': user_id}
            })
            search_client = get_search_client()

            # Build filter for user_id if provided
            filter_expression = None
            if user_id:
                filter_expression = f"UserId eq '{user_id}'"
            
            search_results = search_client.search(
                search_text=refined_query,
                filter=filter_expression,
                select=["ExtractedText", "BlobUri", "FileName", "DocumentId"],
                top=top
            )
            
            extracted_text = ""
            blob_uri = ""
            file_name = ""
            document_id = None
            
            for result in search_results:
                extracted_text = result.get("ExtractedText", "")
                blob_uri = result.get("BlobUri", "")
                file_name = result.get("FileName", "")
                document_id = result.get("DocumentId", "")
                break
            
            if extracted_text:
                logger.info(f"Document found: {file_name}", extra={
                    'custom_dimensions': {'text_length': len(extracted_text), 'document_id': document_id}
                })
            else:
                logger.warning("No documents found in search results")
            
            return extracted_text, blob_uri, file_name, document_id
            
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}", exc_info=True)
            raise Exception(f"Failed to search documents: {str(e)}")
    
    @staticmethod
    def generate_answer_with_openai(user_query: str, extracted_text: str, blob_uri: str) -> Dict[str, Any]:
        """
        Generate formatted answer using Azure OpenAI based on search results.
        
        Args:
            user_query: Original user query
            extracted_text: Text extracted from relevant documents
            blob_uri: URI of the source document
            
        Returns:
            Dictionary with answer components (analyte_used, value, unit, answer_text, document_link)
            
        Raises:
            Exception: If answer generation fails
        """
        try:
            logger.info("Generating answer with OpenAI")
            openai_client = get_openai_client()
            
            answer_system_prompt = """You are a medical information extraction assistant. You will be given:
            1. A user's question.
            2. A set of text passages extracted from medical reports.

            Your job is to return the single value from the passages that best answers the user's question.

            Rules:
            - Use only the information provided in the passages.
            - If the value for the exact lab test the user asked for is not present, return the closest clinically related marker.
            - For iron-related questions:
                - Ferritin, Transferrin Saturation (TSAT), TIBC, and Serum Iron are all acceptable substitutes.
            - Do NOT hallucinate values that are not explicitly present.
            - Return null fields if no clinically related value is present at all.
            - Provide the name of the analyte you used, its value, its unit, and the best document reference.
            - Always return JSON ONLY following this schema:

            {
            "analyte_used": string | null,
            "value": string | null,
            "unit": string | null,
            "answer_text": string | null,
            "document_link": string | null
        }"""
            
            extracts = f"""{{
            {{
                "Text": {extracted_text},
                "Document link": {blob_uri}
            }}
        }}"""
            
            answer_user_prompt = f"""
        Question: {user_query}
        Extracts: {extracts}
        """
            
            answer_response = openai_client.chat.completions.create(
                model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4'),
                messages=[
                    {"role": "system", "content": answer_system_prompt},
                    {"role": "user", "content": answer_user_prompt}
                ]
            )
            
            formatted_answer = answer_response.choices[0].message.content.strip()
            answer_data = json.loads(formatted_answer)
            logger.info("Answer generated successfully", extra={
                'custom_dimensions': {'has_value': bool(answer_data.get('value'))}
            })
            return answer_data
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    @staticmethod
    def generate_sas_url(blob_uri: str, container_name: str = AZURE_STORAGE_CONTAINER_NAME_RAW, 
                        expiry_hours: int = 1) -> Optional[str]:
        """
        Generate a SAS URL for secure blob access.
        
        Args:
            blob_uri: The blob URI
            container_name: The container name
            expiry_hours: Number of hours until SAS token expires
            
        Returns:
            SAS URL or None if generation fails
        """
        try:
            logger.debug(f"Generating SAS URL for blob")
            blob_service_client = get_blob_service_client()
            
            # Extract blob name from URI
            blob_parts = blob_uri.split('/')
            blob_name = blob_parts[-1] if blob_parts else None
            
            if not blob_name:
                logger.warning("Could not extract blob name from URI")
                return None
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=blob_service_client.account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=blob_service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            sas_url = f"{blob_uri}?{sas_token}"
            logger.debug("SAS URL generated successfully")
            return sas_url
            
        except Exception as e:
            logger.error(f"Error generating SAS token: {str(e)}", exc_info=True)
            return blob_uri  # Return original URI if SAS generation fails
    
    @staticmethod
    def perform_search(user_query: str, user_id: Optional[str] = None, 
                      device_type: Optional[str] = None, 
                      app_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform complete search operation: refine query, search documents, generate answer.
        
        Args:
            user_query: Original user query
            user_id: User ID for tracking (optional)
            device_type: Device type for tracking (optional)
            app_version: App version for tracking (optional)
            
        Returns:
            Dictionary with search results and metadata
            
        Raises:
            Exception: If search operation fails
        """
        try:
            logger.info(f"Starting search operation", extra={
                'custom_dimensions': {
                    'user_id': user_id,
                    'query': user_query,
                    'device_type': device_type,
                    'app_version': app_version
                }
            })
            search_start_time = datetime.utcnow()
            
            # Step 1: Refine query
            refined_query = SearchService.refine_query_with_openai(user_query)
            logger.debug(f"Refined query: {refined_query[:200]}...")
            
            # Step 2: Search documents (with user_id filter)
            extracted_text, blob_uri, file_name, document_id = SearchService.search_documents(refined_query, user_id)
            logger.info(f"Found document: {file_name}, document_id: {document_id}")
            
            # Step 3: Generate answer
            answer_data = SearchService.generate_answer_with_openai(user_query, extracted_text, blob_uri)
            
            # Step 4: Generate SAS URL
            document_link = answer_data.get("document_link")
            sas_url = None
            if document_link:
                sas_url = SearchService.generate_sas_url(document_link)
            
            # Calculate duration
            search_end_time = datetime.utcnow()
            search_duration_ms = int((search_end_time - search_start_time).total_seconds() * 1000)
            
            logger.info(f"Search operation completed successfully", extra={
                'custom_dimensions': {
                    'user_id': user_id,
                    'duration_ms': search_duration_ms,
                    'has_answer': bool(answer_data.get('value'))
                }
            })
            
            # Format response
            answer_text = answer_data.get("answer_text") or "No answer could be generated from the documents."
            
            return {
                "answer_text": answer_text,
                "answer_data": answer_data,
                "document_sas_url": sas_url,
                "refined_query": refined_query,
                "search_duration_ms": search_duration_ms,
                "extracted_text": extracted_text,
                "blob_uri": blob_uri,
                "file_name": file_name,
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Search operation failed: {str(e)}", extra={
                'custom_dimensions': {'user_id': user_id, 'query': user_query}
            }, exc_info=True)
            raise Exception(f"Search operation failed: {str(e)}")
