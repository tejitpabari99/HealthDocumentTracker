"""
Document service layer for Cosmos DB and document processing operations.

Provides methods for:
- Document upload orchestration (blob upload, OCR, search indexing)
- Document CRUD operations in Cosmos DB
- Document deletion from all Azure services
- SAS URL generation for document access
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import os
import io
from werkzeug.datastructures import FileStorage
from azure.cosmos import exceptions
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from azure.search.documents.models import IndexingResult
from Backend.config import (
    get_cosmos_database,
    get_blob_service_client,
    get_search_client,
    get_documents_container,
    AZURE_STORAGE_CONTAINER_NAME_RAW
)
from Backend.models.document import Document, DocumentCreate, DocumentUpdate
from Backend.utils.ocr_utils import extract_text_with_ocr
from Backend.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentService:
    """Service class for Document operations in Cosmos DB."""
    
    @staticmethod
    def create_document(document_data: DocumentCreate) -> Dict[str, Any]:
        """
        Create a new document in Cosmos DB.
        
        Args:
            document_data: DocumentCreate model with document information
            
        Returns:
            Created document as dictionary
            
        Raises:
            Exception: If document creation fails
        """
        try:
            logger.info(f"Creating document for user: {document_data.userId}", extra={
                'custom_dimensions': {'user_id': document_data.userId, 'filename': document_data.originalFileName}
            })
            container = get_documents_container()
            
            # Generate unique IDs
            doc_id = f"doc-{uuid.uuid4()}"
            document_id = f"doc-{uuid.uuid4()}"
            current_time = datetime.utcnow().isoformat() + "Z"
            
            # Create document
            doc = {
                "id": doc_id,
                "userId": document_data.userId,
                "documentId": document_id,
                "reportId": document_data.reportId,
                "schemaVersion": "1.0",
                "originalFileName": document_data.originalFileName,
                "displayName": document_data.displayName,
                "contentType": document_data.contentType,
                "fileSize": document_data.fileSize,
                "blobUri": document_data.blobUri,
                "blobName": document_data.blobName,
                "blobContainer": document_data.blobContainer,
                "thumbnailUri": document_data.thumbnailUri,
                "blobUploadDurationMs": document_data.blobUploadDurationMs,
                "searchDocumentIds": document_data.searchDocumentIds,
                "totalPages": document_data.totalPages,
                "searchUploadDurationMs": document_data.searchUploadDurationMs,
                "uploadedAt": current_time,
                "status": "active",
                "type": "document"
            }
            
            # Insert into Cosmos DB
            created_doc = container.create_item(body=doc)
            logger.info(f"Document created successfully: {doc_id}", extra={
                'custom_dimensions': {'document_id': doc_id, 'user_id': document_data.userId}
            })
            return created_doc
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create document: {str(e)}", extra={
                'custom_dimensions': {'user_id': document_data.userId}
            }, exc_info=True)
            raise Exception(f"Failed to create document: {str(e)}")
    
    @staticmethod
    def create_document_with_id(document_data: DocumentCreate, doc_id: str) -> Dict[str, Any]:
        """
        Create a new document in Cosmos DB with a specific ID.
        
        Args:
            document_data: DocumentCreate model with document information
            doc_id: The specific document ID to use
            
        Returns:
            Created document as dictionary
            
        Raises:
            Exception: If document creation fails
        """
        try:
            logger.info(f"Creating document with ID {doc_id} for user: {document_data.userId}", extra={
                'custom_dimensions': {'user_id': document_data.userId, 'filename': document_data.originalFileName, 'document_id': doc_id}
            })
            container = get_documents_container()
            
            current_time = datetime.utcnow().isoformat() + "Z"
            
            # Create document with specified ID
            doc = {
                "id": doc_id,
                "userId": document_data.userId,
                "documentId": doc_id,
                "reportId": document_data.reportId,
                "schemaVersion": "1.0",
                "originalFileName": document_data.originalFileName,
                "displayName": document_data.displayName,
                "contentType": document_data.contentType,
                "fileSize": document_data.fileSize,
                "blobUri": document_data.blobUri,
                "blobName": document_data.blobName,
                "blobContainer": document_data.blobContainer,
                "thumbnailUri": document_data.thumbnailUri,
                "blobUploadDurationMs": document_data.blobUploadDurationMs,
                "searchDocumentIds": document_data.searchDocumentIds,
                "totalPages": document_data.totalPages,
                "searchUploadDurationMs": document_data.searchUploadDurationMs,
                "uploadedAt": current_time,
                "status": "active",
                "type": "document"
            }
            
            # Insert into Cosmos DB
            created_doc = container.create_item(body=doc)
            logger.info(f"Document created successfully: {doc_id}", extra={
                'custom_dimensions': {'document_id': doc_id, 'user_id': document_data.userId}
            })
            return created_doc
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create document: {str(e)}", extra={
                'custom_dimensions': {'user_id': document_data.userId}
            }, exc_info=True)
            raise Exception(f"Failed to create document: {str(e)}")
    
    @staticmethod
    def get_document(document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: The document ID to retrieve
            
        Returns:
            Document as dictionary or None if not found
        """
        try:
            container = get_documents_container()
            
            # Query for document by documentId (since we can't use documentId as partition key)
            query = "SELECT * FROM c WHERE c.id = @documentId AND c.type = 'document'"
            parameters = [{"name": "@documentId", "value": document_id}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to retrieve document: {str(e)}")
    
    @staticmethod
    def list_documents_by_user(user_id: str, limit: int = 100, status: str = "active") -> Dict[str, Any]:
        """
        List all documents for a specific user.
        
        Args:
            user_id: The user ID to filter by
            limit: Maximum number of documents to return
            status: Filter by status (default: "active")
            
        Returns:
            Dictionary with documents list and count
        """
        try:
            container = get_documents_container()
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @userId 
                AND c.type = 'document' 
                AND c.status = @status 
                ORDER BY c.uploadedAt DESC
            """
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@status", "value": status}
            ]
            
            # Execute query
            query_iterable = container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=limit
            )
            
            documents = []
            for item in query_iterable:
                documents.append(item)
                if len(documents) >= limit:
                    break
            
            return {
                "documents": documents,
                "count": len(documents),
                "userId": user_id
            }
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to list documents: {str(e)}")
    
    @staticmethod
    def update_document(document_id: str, update_data: DocumentUpdate) -> Optional[Dict[str, Any]]:
        """
        Update document information (PATCH operation).
        
        Args:
            document_id: The document ID to update
            update_data: DocumentUpdate model with fields to update
            
        Returns:
            Updated document or None if document not found
        """
        try:
            container = get_documents_container()
            
            # Get existing document
            existing_doc = DocumentService.get_document(document_id)
            if not existing_doc:
                return None
            
            # Update only provided fields
            if update_data.displayName is not None:
                existing_doc["displayName"] = update_data.displayName
            if update_data.status is not None:
                existing_doc["status"] = update_data.status
            
            # Replace item in Cosmos DB
            updated_doc = container.replace_item(item=existing_doc["id"], body=existing_doc)
            return updated_doc
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to update document: {str(e)}")
    
    @staticmethod
    def delete_document(document_id: str) -> bool:
        """
        Delete a document from Cosmos DB (soft delete by setting status to 'deleted').
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            True if deleted successfully, False if document not found
        """
        try:
            container = get_documents_container()
            
            # Get existing document
            existing_doc = DocumentService.get_document(document_id)
            if not existing_doc:
                return False
            
            # Soft delete by updating status
            existing_doc["status"] = "deleted"
            container.replace_item(item=existing_doc["id"], body=existing_doc)
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to delete document: {str(e)}")
    
    @staticmethod
    def hard_delete_document(document_id: str) -> bool:
        """
        Permanently delete a document from Cosmos DB.
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            True if deleted successfully, False if document not found
        """
        try:
            container = get_documents_container()
            
            # Get existing document to find its partition key
            existing_doc = DocumentService.get_document(document_id)
            if not existing_doc:
                return False
            
            # Delete item from Cosmos DB
            container.delete_item(item=existing_doc["id"], partition_key=existing_doc["userId"])
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to hard delete document: {str(e)}")
    
    @staticmethod
    def get_document_by_report_id(report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by report ID.
        
        Args:
            report_id: The report ID to search for
            
        Returns:
            Document as dictionary or None if not found
        """
        try:
            container = get_documents_container()
            
            query = "SELECT * FROM c WHERE c.reportId = @reportId AND c.type = 'document'"
            parameters = [{"name": "@reportId", "value": report_id}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to query document by report ID: {str(e)}")
    
    @staticmethod
    def upload_document_full_process(file: FileStorage, user_id: str, file_content: bytes) -> Dict[str, Any]:
        """
        Complete document upload process: blob upload, OCR, search indexing, Cosmos DB creation.
        
        Args:
            file: The uploaded file object
            user_id: User ID who is uploading the document
            file_content: The file content as bytes
            
        Returns:
            Dictionary with upload results and document metadata
            
        Raises:
            Exception: If upload process fails at any stage
        """
        from werkzeug.utils import secure_filename
        
        logger.info(f"Starting document upload process for user: {user_id}", extra={
            'custom_dimensions': {'user_id': user_id, 'filename': file.filename}
        })
        
        # Secure the filename and generate unique blob name
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        content_type = file.content_type or 'application/octet-stream'
        
        # Get blob service client
        blob_service_client = get_blob_service_client()
        
        # Get or create container
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME_RAW)
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists
        
        # Upload file to blob storage
        logger.debug(f"Uploading to blob storage: {unique_filename}")
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_STORAGE_CONTAINER_NAME_RAW,
            blob=unique_filename
        )
        
        file_stream = io.BytesIO(file_content)
        blob_client.upload_blob(file_stream, overwrite=True)
        blob_url = blob_client.url
        logger.info(f"Blob uploaded successfully: {unique_filename}", extra={
            'custom_dimensions': {'blob_name': unique_filename, 'user_id': user_id}
        })
        
        # Determine OCR method based on file size
        file_size_mb = len(file_content) / (1024 * 1024)
        use_blob_url = file_size_mb > 4
        
        # Generate SAS URL for Document Intelligence if needed
        blob_url_with_sas = None
        if use_blob_url:
            try:
                sas_token = generate_blob_sas(
                    account_name=blob_service_client.account_name,
                    container_name=AZURE_STORAGE_CONTAINER_NAME_RAW,
                    blob_name=unique_filename,
                    account_key=blob_service_client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=1)
                )
                blob_url_with_sas = f"{blob_url}?{sas_token}"
            except Exception as sas_error:
                print(f"Warning: Failed to generate SAS token: {str(sas_error)}")
                use_blob_url = False
        
        # Extract text using OCR
        logger.info(f"Starting OCR extraction, method: {'blob_url' if use_blob_url else 'direct_content'}")
        pages_data = extract_text_with_ocr(
            file_content,
            content_type,
            original_filename,
            blob_url_with_sas if use_blob_url else None
        )
        
        # Handle OCR failure
        if not pages_data:
            logger.error("OCR extraction failed - no pages extracted", extra={
                'custom_dimensions': {'filename': original_filename, 'user_id': user_id}
            })
            try:
                blob_client.delete_blob()
            except Exception as delete_error:
                print(f"Warning: Failed to delete blob after OCR failure: {str(delete_error)}")
            
            raise Exception("OCR extraction failed - no text could be extracted from the document")
        
        # Generate report ID and document ID for this upload
        report_id = str(uuid.uuid4())
        cosmos_doc_id = f"doc-{uuid.uuid4()}"
        upload_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Index pages in Azure AI Search
        search_documents = []
        total_text_length = 0
        
        for page_data in pages_data:
            page_document_id = str(uuid.uuid4())
            page_text = page_data.get('text', '')
            page_number = page_data.get('page_number', 1)
            
            if not page_text.strip():
                continue
            
            total_text_length += len(page_text)
            
            search_document = {
                "id": page_document_id,
                "UserId": user_id,
                "DocumentId": cosmos_doc_id,
                "ReportId": report_id,
                "PageNumber": page_number,
                "ExtractedText": page_text,
                "BlobUri": blob_url,
                "ContentType": content_type,
                "FileName": original_filename,
                "UploadedAt": upload_timestamp
            }
            
            search_documents.append(search_document)
        
        # Upload to Azure AI Search
        uploaded_pages = 0
        search_document_ids = []
        
        logger.info(f"Indexing {len(search_documents)} pages to Azure AI Search")
        if not search_documents:
            logger.warning("No search documents to upload - all pages empty")
            # All pages were empty - delete blob
            try:
                blob_client.delete_blob()
            except Exception as delete_error:
                print(f"Warning: Failed to delete blob after empty pages: {str(delete_error)}")
            
            raise Exception("No text content found - all pages were empty")
        
        try:
            search_client = get_search_client()
            result = search_client.upload_documents(documents=search_documents)
            uploaded_pages = len(search_documents)
            search_document_ids = [doc["id"] for doc in search_documents]
            logger.info(f"Uploaded {uploaded_pages} pages to Azure AI Search", extra={
                'custom_dimensions': {'report_id': report_id, 'pages': uploaded_pages, 'user_id': user_id}
            })
        except Exception as search_error:
            logger.error(f"Failed to upload to Azure AI Search: {str(search_error)}", extra={
                'custom_dimensions': {'report_id': report_id, 'user_id': user_id}
            }, exc_info=True)
            # Continue - document is in blob storage but not indexed
        
        # Create document entry in Cosmos DB with pre-generated ID
        try:
            display_name = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            
            document_create = DocumentCreate(
                userId=user_id,
                reportId=report_id,
                originalFileName=original_filename,
                displayName=display_name,
                contentType=content_type,
                fileSize=len(file_content),
                blobUri=blob_url,
                blobName=unique_filename,
                blobContainer=AZURE_STORAGE_CONTAINER_NAME_RAW,
                searchDocumentIds=search_document_ids,
                totalPages=uploaded_pages
            )
            
            # Use the pre-generated cosmos_doc_id
            created_doc = DocumentService.create_document_with_id(document_create, cosmos_doc_id)
            logger.info(f"Document upload process completed successfully", extra={
                'custom_dimensions': {
                    'document_id': cosmos_doc_id,
                    'user_id': user_id,
                    'pages': uploaded_pages,
                    'report_id': report_id
                }
            })
            
        except Exception as cosmos_error:
            logger.error(f"Failed to create document in Cosmos DB: {str(cosmos_error)}", extra={
                'custom_dimensions': {'user_id': user_id, 'report_id': report_id}
            }, exc_info=True)
        
        return {
            'blob_name': unique_filename,
            'original_filename': original_filename,
            'blob_url': blob_url,
            'report_id': report_id,
            'pages_uploaded': uploaded_pages,
            'container': AZURE_STORAGE_CONTAINER_NAME_RAW,
            'extracted_text_length': total_text_length,
            'ocr_method': 'blob_url' if use_blob_url else 'direct_content',
            'document_id': cosmos_doc_id,
            'file_size_mb': round(file_size_mb, 2)
        }
    
    @staticmethod
    def delete_document_full_process(document_id: str) -> Dict[str, Any]:
        """
        Complete document deletion: remove from Cosmos DB, Azure AI Search, and Blob Storage.
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            Dictionary with deletion results for each service
            
        Raises:
            Exception: If document not found or deletion fails
        """
        logger.info(f"Starting document deletion process: {document_id}")
        
        # Get document from Cosmos DB
        document = DocumentService.get_document(document_id)
        if not document:
            logger.warning(f"Document not found for deletion: {document_id}")
            raise Exception("Document not found")
        
        # Extract required information
        search_ids = document.get('searchDocumentIds', [])
        blob_name = document.get('blobName', '')
        blob_container = document.get('blobContainer', AZURE_STORAGE_CONTAINER_NAME_RAW)
        
        if not blob_name:
            raise Exception("Document does not have blob information")
        
        # Track deletion results
        search_deleted_count = 0
        search_delete_failed_ids = []
        blob_deleted = False
        cosmos_deleted = False
        errors = []
        
        # Delete from Azure AI Search
        if search_ids:
            try:
                search_client = get_search_client()
                documents_to_delete = [{"id": search_id.strip()} for search_id in search_ids if search_id.strip()]
                
                if documents_to_delete:
                    result: list[IndexingResult] = search_client.delete_documents(documents=documents_to_delete)
                    if any(r.status_code != 200 for r in result):
                        failed_ids = [documents_to_delete[i]['id'] for i, r in enumerate(result) if r.status_code != 200]
                        search_delete_failed_ids.extend(failed_ids)
                        errors.append(f"Failed to delete some documents from Azure AI Search: {failed_ids}")
                        logger.warning(f"Some search documents failed to delete: {failed_ids}")
                    search_deleted_count = len(documents_to_delete)
                    logger.info(f"Deleted {search_deleted_count} documents from Azure AI Search")
            except Exception as search_error:
                error_msg = f"Failed to delete from Azure AI Search: {str(search_error)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                search_delete_failed_ids.extend(search_ids)
        
        # Delete from Azure Blob Storage
        try:
            blob_service_client = get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=blob_container,
                blob=blob_name
            )
            blob_client.delete_blob()
            blob_deleted = True
            logger.info(f"Deleted blob from Azure Storage: {blob_name}")
        except Exception as blob_error:
            error_msg = f"Failed to delete from Azure Blob Storage: {str(blob_error)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
        
        # Delete from Cosmos DB
        try:
            cosmos_deleted = DocumentService.hard_delete_document(document_id)
            if cosmos_deleted:
                logger.info(f"Deleted document from Cosmos DB: {document_id}")
            else:
                errors.append("Failed to delete from Cosmos DB: Document not found")
                logger.warning(f"Document not found in Cosmos DB: {document_id}")
        except Exception as cosmos_error:
            error_msg = f"Failed to delete from Cosmos DB: {str(cosmos_error)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
        
        logger.info(f"Document deletion process completed", extra={
            'custom_dimensions': {
                'document_id': document_id,
                'success': cosmos_deleted and blob_deleted,
                'errors_count': len(errors)
            }
        })
        
        return {
            'document_id': document_id,
            'search_deleted_count': search_deleted_count,
            'search_delete_failed_ids': search_delete_failed_ids,
            'blob_deleted': blob_deleted,
            'cosmos_deleted': cosmos_deleted,
            'errors': errors,
            'success': cosmos_deleted and blob_deleted and (not search_ids or search_deleted_count > 0)
        }
