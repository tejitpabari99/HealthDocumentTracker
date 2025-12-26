"""
Admin Search Activity API Endpoints

Provides administrative access to search activity records.
Allows viewing search activities across all users.
"""
from flask import Blueprint, request, jsonify
from Backend.services.search_activity_service import SearchActivityService
from Backend.utils.logger import get_logger

logger = get_logger(__name__)

# Create Blueprint
admin_search_activity_bp = Blueprint('admin_search_activity', __name__)

@admin_search_activity_bp.route('/admin/search-activities', methods=['GET'])
def list_all_search_activities():
    """
    List all search activities across all users with pagination support.
    
    Query Parameters:
        userId: (optional) Filter by specific user ID
        limit: (optional) Maximum number of activities to return (default: 100)
    
    Returns: JSON with list of search activities
    """
    try:
        user_id = request.args.get('userId')
        limit = request.args.get('limit', 100, type=int)
        
        # Validate limit
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'limit must be between 1 and 1000'}), 400
        
        if user_id:
            # Get search activities for specific user
            logger.info(f"Admin listing search activities for user: {user_id}")
            result = SearchActivityService.list_search_activities_by_user(user_id, limit=limit)
        else:
            # Get all search activities
            logger.info("Admin listing all search activities")
            result = SearchActivityService.list_all_search_activities(limit=limit)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Admin failed to list search activities: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to list search activities: {str(e)}'}), 500

@admin_search_activity_bp.route('/admin/search-activities', methods=['DELETE'])
def delete_search_activities():
    """
    Delete search activities. Can delete all activities or filter by user ID.
    
    Query Parameters:
        userId: (optional) Delete only activities for specific user ID
    
    Returns: JSON with deletion status and count
    """
    try:
        user_id = request.args.get('userId')
        
        if user_id:
            # Delete search activities for specific user
            logger.info(f"Admin deleting search activities for user: {user_id}")
            result = SearchActivityService.delete_search_activities_by_user(user_id)
        else:
            # Delete all search activities
            logger.info("Admin deleting all search activities")
            result = SearchActivityService.delete_all_search_activities()
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Admin failed to delete search activities: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to delete search activities: {str(e)}'}), 500
