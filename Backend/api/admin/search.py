"""
Admin Search API Endpoints

Provides administrative access to Azure AI Search index management across all users.
Allows viewing and deleting search entries for any user.
"""
from flask import Blueprint, request, jsonify
from Backend.config import get_search_client
from Backend.utils.logger import get_logger
from azure.core.exceptions import ResourceNotFoundError

logger = get_logger(__name__)

# Create Blueprint
admin_search_bp = Blueprint('admin_search', __name__)

@admin_search_bp.route('/admin/search', methods=['GET'])
def get_all_search_entries():
    """
    Get all search index entries across all users or for a specific user.
    
    Query Parameters:
        userId: (optional) Filter search entries by user ID
        limit: (optional) Maximum number of entries to return (default: 100)
    
    Returns: JSON with list of search index entries
    """
    try:
        user_id = request.args.get('userId')
        limit = request.args.get('limit', 100, type=int)
        
        # Validate limit
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'limit must be between 1 and 1000'}), 400
        
        # Get search client
        search_client = get_search_client()
        
        # Build search query
        if user_id:
            logger.info(f"Admin listing search entries for user: {user_id}")
            # Filter by userId field
            results = search_client.search(
                search_text="*",
                filter=f"UserId eq '{user_id}'",
                top=limit
            )
        else:
            logger.info("Admin listing all search entries")
            # Get all entries
            results = search_client.search(
                search_text="*",
                top=limit
            )
        
        # Convert results to list
        entries = []
        for result in results:
            entries.append(dict(result))
        
        return jsonify({
            'entries': entries,
            'count': len(entries)
        }), 200
        
    except Exception as e:
        logger.error(f"Admin failed to list search entries: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to list search entries: {str(e)}'}), 500

@admin_search_bp.route('/admin/search', methods=['DELETE'])
def delete_all_user_search_entries():
    """
    Delete all search index entries from Azure AI Search.
    
    Query Parameters:
        userId: (optional) User ID whose search entries should be deleted. If not provided, deletes ALL entries.
    
    Returns: JSON with deletion results
    """
    try:
        user_id = request.args.get('userId')
        
        # Get search client
        search_client = get_search_client()
        
        # Search for entries based on userId
        if user_id:
            logger.info(f"Admin deleting all search entries for user: {user_id}")
            results = search_client.search(
                search_text="*",
                filter=f"userId eq '{user_id}'",
                select="id",
                top=1000  # Get up to 1000 entries
            )
        else:
            logger.warning("Admin deleting ALL search entries across all users")
            results = search_client.search(
                search_text="*",
                select="id",
                top=1000  # Get up to 1000 entries
            )
        
        # Collect document IDs to delete
        doc_ids = [result['id'] for result in results]
        
        if not doc_ids:
            logger.info(f"No search entries found for user: {user_id}")
            return jsonify({
                'message': f'No search entries found for user {user_id}',
                'userId': user_id,
                'deleted_count': 0
            }), 200
        
        deleted_count = 0
        failed_ids = []
        
        # Delete documents in batches (Azure Search supports batch operations)
        try:
            # Delete all documents
            documents_to_delete = [{"id": doc_id} for doc_id in doc_ids]
            result = search_client.delete_documents(documents=documents_to_delete)
            
            # Check results
            for item in result:
                if item.succeeded:
                    deleted_count += 1
                else:
                    failed_ids.append({
                        'id': item.key,
                        'error': item.error_message if hasattr(item, 'error_message') else 'Unknown error'
                    })
                    logger.warning(f"Failed to delete search entry {item.key}")
        
        except Exception as e:
            logger.error(f"Batch deletion failed: {str(e)}")
            # Fall back to individual deletion
            for doc_id in doc_ids:
                try:
                    search_client.delete_documents(documents=[{"id": doc_id}])
                    deleted_count += 1
                except Exception as delete_error:
                    logger.warning(f"Failed to delete search entry {doc_id}: {str(delete_error)}")
                    failed_ids.append({
                        'id': doc_id,
                        'error': str(delete_error)
                    })
        
        if failed_ids:
            logger.warning(f"Some search entries failed to delete for user {user_id}")
            return jsonify({
                'message': 'Partial deletion completed',
                'userId': user_id,
                'deleted_count': deleted_count,
                'failed_count': len(failed_ids),
                'failed_ids': failed_ids
            }), 207  # Multi-Status
        else:
            logger.info(f"Successfully deleted {deleted_count} search entries for user: {user_id}")
            return jsonify({
                'message': f'Successfully deleted all search entries for user {user_id}',
                'userId': user_id,
                'deleted_count': deleted_count
            }), 200
        
    except Exception as e:
        logger.error(f"Admin failed to delete search entries for user: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to delete search entries: {str(e)}'}), 500
