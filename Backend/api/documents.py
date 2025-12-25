"""
Document API Endpoints

Manages document lifecycle across Azure services.
Delegates all business logic to DocumentService.
"""
from flask import Blueprint, request, jsonify, g
from Backend.config import allowed_file, ALLOWED_EXTENSIONS
from Backend.services.document_service import DocumentService
from Backend.models.document import DocumentUpdate
from Backend.utils.logger import get_logger
from Backend.utils.middleware import require_auth

logger = get_logger(__name__)

# Create Blueprint
documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/documents', methods=['POST'])
@require_auth
def create_document():
    """
    Upload and process a document across all Azure services for the authenticated user.
    Delegates to DocumentService for all business logic.
    
    Authentication: Required (via X-User-Id header in dev, JWT in production)
    
    Expected: multipart/form-data with 'file' field
    Returns: JSON with document metadata and processing results
    """
    try:
        # Get user_id from middleware (extracted from auth)
        user_id = g.user_id
        
        logger.info(f"Document upload request received for user: {user_id}")
        
        # Check if file is present in request
        if 'file' not in request.files:
            logger.warning("No file provided in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        logger.info(f"Processing document upload: {file.filename} for user: {user_id}")
        
        # Read file content
        file.seek(0)
        file_content = file.read()
        
        # Process document upload using DocumentService
        result = DocumentService.upload_document_full_process(file, user_id, file_content)
        
        return jsonify({
            'message': 'File uploaded successfully',
            **result
        }), 201
        
    except Exception as e:
        error_message = str(e)
        
        # Handle specific error cases
        if 'OCR extraction failed' in error_message:
            logger.error(f"OCR extraction failed for document upload", exc_info=True)
            return jsonify({
                'error': 'OCR extraction failed',
                'message': 'No text could be extracted from the document. File has been removed from storage.',
                'details': 'The document may be a scanned image without text, corrupted, or in an unsupported format.'
            }), 400
        
        if 'No text content found' in error_message:
            logger.warning("No text content found in document")
            return jsonify({
                'error': 'No text content found',
                'message': 'All pages in the document were empty. File has been removed from storage.',
                'details': 'The document may contain only images without text or be blank pages.'
            }), 400
        
        logger.error(f"Document upload failed: {error_message}", exc_info=True)
        return jsonify({'error': f'Failed to upload file: {error_message}'}), 500

@documents_bp.route('/documents', methods=['GET'])
@require_auth
def list_documents():
    """
    List all documents for the authenticated user.
    
    Authentication: Required (via X-User-Id header in dev, JWT in production)
    
    Query Parameters:
        limit: (optional) Maximum number of documents to return (default: 100)
        status: (optional) Filter by status (default: "active")
    
    Returns: JSON with list of documents
    """
    try:
        # Get user_id from middleware (extracted from auth)
        user_id = g.user_id
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        status = request.args.get('status', 'active')
        
        # Validate limit
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'limit must be between 1 and 1000'}), 400
        
        # Get documents from Cosmos DB
        result = DocumentService.list_documents_by_user(user_id, limit=limit, status=status)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list documents: {str(e)}'}), 500

@documents_bp.route('/documents/<document_id>', methods=['GET'])
@require_auth
def get_document(document_id):
    """
    Get a single document by ID for the authenticated user.
    
    Authentication: Required (via X-User-Id header in dev, JWT in production)
    
    Path Parameters:
        document_id: The document ID to retrieve
    
    Returns: JSON with document details
    """
    try:
        # Get document from Cosmos DB
        document = DocumentService.get_document(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify(document), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve document: {str(e)}'}), 500

@documents_bp.route('/documents/<document_id>', methods=['PATCH'])
@require_auth
def update_document(document_id):
    """
    Update a document's information for the authenticated user.
    
    Authentication: Required (via X-User-Id header in dev, JWT in production)
    
    Path Parameters:
        document_id: The document ID to update
    
    Request Body:
        displayName: (optional) New display name
        status: (optional) New status
    
    Returns: JSON with updated document
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create update model
        update_data = DocumentUpdate(
            displayName=data.get('displayName'),
            status=data.get('status')
        )
        
        # Update document in Cosmos DB
        updated_document = DocumentService.update_document(document_id, update_data)
        
        if not updated_document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify({
            'message': 'Document updated successfully',
            'document': updated_document
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to update document: {str(e)}'}), 500

@documents_bp.route('/documents/<document_id>', methods=['DELETE'])
@require_auth
def delete_document(document_id):
    """
    Delete a document from all Azure services for the authenticated user.
    Delegates to DocumentService for all business logic.
    
    Authentication: Required (via X-User-Id header in dev, JWT in production)
    
    Path Parameters:
        document_id: The document ID from Cosmos DB
    
    Returns: JSON with deletion status for each service
    """
    try:
        logger.info(f"Document deletion request: {document_id}")
        
        # Delete document using DocumentService
        result = DocumentService.delete_document_full_process(document_id)
        
        # Determine response based on success
        if result['success']:
            logger.info(f"Document deleted successfully: {document_id}")
            return jsonify({
                'message': 'Document deleted successfully from all services',
                'document_id': result['document_id'],
                'search_deleted_count': result['search_deleted_count'],
                'blob_deleted': result['blob_deleted'],
                'cosmos_deleted': result['cosmos_deleted']
            }), 200
        elif result['cosmos_deleted'] or result['blob_deleted'] or result['search_deleted_count'] > 0:
            logger.warning(f"Partial deletion for document: {document_id}", extra={
                'custom_dimensions': {'errors': result['errors']}
            })
            return jsonify({
                'message': 'Partial deletion completed',
                'warning': 'Document was deleted from some services but not all',
                'document_id': result['document_id'],
                'search_deleted_count': result['search_deleted_count'],
                'search_delete_failed_ids': result['search_delete_failed_ids'],
                'blob_deleted': result['blob_deleted'],
                'cosmos_deleted': result['cosmos_deleted'],
                'errors': result['errors']
            }), 207  # Multi-Status
        else:
            logger.error(f"Failed to delete document: {document_id}", extra={
                'custom_dimensions': {'errors': result['errors']}
            })
            return jsonify({
                'error': 'Failed to delete document from all services',
                'document_id': result['document_id'],
                'errors': result['errors']
            }), 500
        
    except Exception as e:
        error_message = str(e)
        
        if 'Document not found' in error_message:
            logger.warning(f"Document not found for deletion: {document_id}")
            return jsonify({'error': 'Document not found'}), 404
        
        logger.error(f"Document deletion error: {error_message}", exc_info=True)
        return jsonify({'error': f'Delete operation failed: {error_message}'}), 500