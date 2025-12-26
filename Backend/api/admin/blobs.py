"""
Admin Blob API Endpoints

Provides administrative access to Azure Blob Storage management across all users.
Allows viewing and deleting blobs for any user.
"""
from flask import Blueprint, request, jsonify
from Backend.config import get_blob_service_client, AZURE_STORAGE_CONTAINER_NAME_RAW
from Backend.utils.logger import get_logger

logger = get_logger(__name__)

# Create Blueprint
admin_blobs_bp = Blueprint('admin_blobs', __name__)

@admin_blobs_bp.route('/admin/blobs', methods=['GET'])
def get_all_blobs():
    """
    Get all blobs across all users or for a specific user.
    
    Query Parameters:
        userId: (optional) Filter blobs by user ID (matches blob name prefix)
        limit: (optional) Maximum number of blobs to return (default: 100)
    
    Returns: JSON with list of blobs
    """
    try:
        user_id = request.args.get('userId')
        limit = request.args.get('limit', 100, type=int)
        
        # Validate limit
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'limit must be between 1 and 1000'}), 400
        
        # Get blob service client
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME_RAW)
        
        # List blobs with optional prefix filter for user-specific directories
        blobs = []
        if user_id:
            logger.info(f"Admin listing blobs for user: {user_id}")
            # List blobs in user's directory (userId/)
            blob_list = container_client.list_blobs(name_starts_with=f"{user_id}/")
        else:
            logger.info("Admin listing all blobs")
            # List all blobs across all user directories
            blob_list = container_client.list_blobs()
        
        # Convert to list with limit
        for blob in blob_list:
            if len(blobs) >= limit:
                break
            blobs.append({
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_settings.content_type if blob.content_settings else None,
                'created_on': blob.creation_time.isoformat() if blob.creation_time else None,
                'last_modified': blob.last_modified.isoformat() if blob.last_modified else None,
                'metadata': blob.metadata if blob.metadata else {}
            })
        
        return jsonify({
            'blobs': blobs,
            'count': len(blobs),
            'container': AZURE_STORAGE_CONTAINER_NAME_RAW
        }), 200
        
    except Exception as e:
        logger.error(f"Admin failed to list blobs: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to list blobs: {str(e)}'}), 500

@admin_blobs_bp.route('/admin/blobs', methods=['DELETE'])
def delete_all_user_blobs():
    """
    Delete all blobs from Azure Blob Storage.
    
    Query Parameters:
        userId: (optional) User ID whose blobs should be deleted. If not provided, deletes ALL blobs.
    
    Returns: JSON with deletion results
    """
    try:
        user_id = request.args.get('userId')
        
        # Get blob service client
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME_RAW)
        
        # List blobs based on userId - now organized in user directories
        if user_id:
            logger.info(f"Admin deleting all blobs for user: {user_id}")
            # Delete all blobs in user's directory (userId/)
            blob_list = container_client.list_blobs(name_starts_with=f"{user_id}/")
        else:
            logger.warning("Admin deleting ALL blobs across all users")
            # Delete all blobs from container
            blob_list = container_client.list_blobs()
        
        deleted_count = 0
        failed_blobs = []
        
        # Delete each blob
        for blob in blob_list:
            try:
                container_client.delete_blob(blob.name)
                deleted_count += 1
                logger.debug(f"Deleted blob: {blob.name}")
            except Exception as e:
                logger.warning(f"Failed to delete blob {blob.name}: {str(e)}")
                failed_blobs.append({
                    'name': blob.name,
                    'error': str(e)
                })
        
        if failed_blobs:
            logger.warning(f"Some blobs failed to delete for user {user_id}")
            return jsonify({
                'message': 'Partial deletion completed',
                'userId': user_id,
                'deleted_count': deleted_count,
                'failed_count': len(failed_blobs),
                'failed_blobs': failed_blobs
            }), 207  # Multi-Status
        else:
            logger.info(f"Successfully deleted {deleted_count} blobs for user: {user_id}")
            return jsonify({
                'message': f'Successfully deleted all blobs for user {user_id}',
                'userId': user_id,
                'deleted_count': deleted_count
            }), 200
        
    except Exception as e:
        logger.error(f"Admin failed to delete blobs for user: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to delete blobs: {str(e)}'}), 500
