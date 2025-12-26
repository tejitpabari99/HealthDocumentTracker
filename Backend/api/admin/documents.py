"""
Admin Document API Endpoints

Provides administrative access to document management across all users.
Allows viewing and deleting documents for any user.
"""
from flask import Blueprint, request, jsonify
from Backend.services.document_service import DocumentService
from Backend.utils.logger import get_logger

logger = get_logger(__name__)

# Create Blueprint
admin_documents_bp = Blueprint('admin_documents', __name__)

@admin_documents_bp.route('/admin/documents', methods=['GET'])
def get_all_documents():
    """
    Get all documents across all users or for a specific user.
    
    Query Parameters:
        userId: (optional) Filter documents by user ID
        limit: (optional) Maximum number of documents to return (default: 100)
        status: (optional) Filter by status (default: "active")
    
    Returns: JSON with list of documents
    """
    try:
        user_id = request.args.get('userId')
        limit = request.args.get('limit', 100, type=int)
        status = request.args.get('status', 'active')
        
        # Validate limit
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'limit must be between 1 and 1000'}), 400
        
        if user_id:
            # Get documents for specific user
            logger.info(f"Admin listing documents for user: {user_id}")
            result = DocumentService.list_documents_by_user(user_id, limit=limit, status=status)
        else:
            # Get all documents
            logger.info("Admin listing all documents")
            result = DocumentService.list_all_documents(limit=limit, status=status)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Admin failed to list documents: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to list documents: {str(e)}'}), 500

@admin_documents_bp.route('/admin/documents', methods=['DELETE'])
def delete_all_user_documents():
    """
    Delete all documents from all Azure services.
    
    Query Parameters:
        userId: (optional) User ID whose documents should be deleted. If not provided, deletes ALL documents.
    
    Returns: JSON with deletion results
    """
    try:
        user_id = request.args.get('userId')
        
        if user_id:
            logger.info(f"Admin deleting all documents for user: {user_id}")
            result = DocumentService.delete_all_documents_by_user(user_id)
        else:
            logger.warning("Admin deleting ALL documents across all users")
            result = DocumentService.delete_all_documents()
        
        if result['success']:
            message = f'Successfully deleted all documents' + (f' for user {user_id}' if user_id else ' across all users')
            logger.info(message)
            response = {
                'message': message,
                'documents_deleted': result['documents_deleted'],
                'cosmos_deleted': result['cosmos_deleted'],
                'blobs_deleted': result['blobs_deleted'],
                'search_entries_deleted': result['search_entries_deleted']
            }
            if user_id:
                response['userId'] = user_id
            return jsonify(response), 200
        else:
            logger.warning(f"Partial deletion", extra={
                'custom_dimensions': {'errors': result['errors'], 'user_id': user_id}
            })
            response = {
                'message': 'Partial deletion completed',
                'warning': 'Some documents could not be fully deleted',
                'documents_deleted': result['documents_deleted'],
                'cosmos_deleted': result['cosmos_deleted'],
                'blobs_deleted': result['blobs_deleted'],
                'search_entries_deleted': result['search_entries_deleted'],
                'errors': result['errors']
            }
            if user_id:
                response['userId'] = user_id
            return jsonify(response), 207  # Multi-Status
        
    except Exception as e:
        logger.error(f"Admin failed to delete documents for user: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to delete documents: {str(e)}'}), 500
