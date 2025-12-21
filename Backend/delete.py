"""
Delete API endpoint for removing documents from both Azure Search and Blob Storage
"""
from flask import Blueprint, request, jsonify
from config import (
    get_blob_service_client,
    get_search_client,
    AZURE_STORAGE_CONTAINER_NAME_RAW
)

# Create Blueprint
delete_bp = Blueprint('delete', __name__)

@delete_bp.route('/documents/delete', methods=['POST'])
def delete_document():
    """
    Delete a document from both Azure AI Search and Azure Blob Storage
    
    Expected: JSON body with 'SearchIds' (list) and 'BlobId' fields
    Returns: JSON with deletion status
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        search_ids = data.get('SearchIds', [])
        blob_id = data.get('BlobId', '').strip()
        
        # Validate SearchIds
        if not search_ids:
            return jsonify({'error': 'SearchIds is required and must be a non-empty list'}), 400
        
        if not isinstance(search_ids, list):
            return jsonify({'error': 'SearchIds must be a list'}), 400
        
        # Validate BlobId
        if not blob_id:
            return jsonify({'error': 'BlobId is required'}), 400
        
        print(f"Deleting document - SearchIds: {search_ids}, BlobId: {blob_id}")
        
        # Track deletion results
        search_deleted_count = 0
        search_failed_ids = []
        blob_deleted = False
        errors = []
        
        # Delete from Azure AI Search (loop through all SearchIds)
        try:
            search_client = get_search_client()
            
            # Prepare documents for batch deletion
            documents_to_delete = [{"id": search_id.strip()} for search_id in search_ids if search_id.strip()]
            
            if documents_to_delete:
                result = search_client.delete_documents(documents=documents_to_delete)
                search_deleted_count = len(documents_to_delete)
                print(f"Deleted {search_deleted_count} documents from Azure AI Search")
            else:
                errors.append("No valid SearchIds provided after validation")
                
        except Exception as search_error:
            error_msg = f"Failed to delete from Azure AI Search: {str(search_error)}"
            print(error_msg)
            errors.append(error_msg)
            search_failed_ids = search_ids
        
        # Delete from Azure Blob Storage
        try:
            blob_service_client = get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=AZURE_STORAGE_CONTAINER_NAME_RAW,
                blob=blob_id
            )
            blob_client.delete_blob()
            blob_deleted = True
            print(f"Deleted blob from Azure Storage: {blob_id}")
        except Exception as blob_error:
            error_msg = f"Failed to delete from Azure Blob Storage: {str(blob_error)}"
            print(error_msg)
            errors.append(error_msg)
        
        # Determine response status
        if search_deleted_count > 0 and blob_deleted:
            return jsonify({
                'message': 'Document deleted successfully from both Azure AI Search and Blob Storage',
                'search_ids_deleted': search_ids,
                'search_deleted_count': search_deleted_count,
                'blob_id': blob_id,
                'search_deleted': True,
                'blob_deleted': True
            }), 200
        elif search_deleted_count > 0 or blob_deleted:
            return jsonify({
                'message': 'Partial deletion completed',
                'warning': 'Document was deleted from some services but not all',
                'search_ids_requested': search_ids,
                'search_deleted_count': search_deleted_count,
                'search_failed_ids': search_failed_ids,
                'blob_id': blob_id,
                'search_deleted': search_deleted_count > 0,
                'blob_deleted': blob_deleted,
                'errors': errors
            }), 207  # Multi-Status
        else:
            return jsonify({
                'error': 'Failed to delete document from both services',
                'search_ids_requested': search_ids,
                'search_deleted_count': 0,
                'blob_id': blob_id,
                'search_deleted': False,
                'blob_deleted': False,
                'errors': errors
            }), 500
        
    except Exception as e:
        print(f"Delete error: {str(e)}")
        return jsonify({'error': f'Delete operation failed: {str(e)}'}), 500
