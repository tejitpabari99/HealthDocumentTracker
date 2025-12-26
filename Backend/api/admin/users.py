"""
Admin User API Endpoints

Provides administrative access to user management.
Allows viewing all users in the system.
"""
from flask import Blueprint, request, jsonify
from Backend.services.user_service import UserService
from Backend.utils.logger import get_logger

logger = get_logger(__name__)

# Create Blueprint
admin_users_bp = Blueprint('admin_users', __name__)

@admin_users_bp.route('/admin/users', methods=['GET'])
def list_all_users():
    """
    List all users with pagination support.
    
    Query parameters:
        limit: Maximum number of users to return (default: 100)
        continuationToken: Token for pagination
    
    Returns: List of users with pagination info
    """
    try:
        logger.info("Admin list users request received")
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        continuation_token = request.args.get('continuationToken', None)
        
        # Validate limit
        if limit < 1 or limit > 1000:
            logger.warning(f"Invalid limit value: {limit}")
            return jsonify({'error': 'Limit must be between 1 and 1000'}), 400
        
        # Get users from service
        result = UserService.list_users(limit=limit, continuation_token=continuation_token)
        
        logger.info(f"Admin listed {result.get('count', 0)} users")
        return jsonify(result), 200
        
    except ValueError as ve:
        logger.error(f"Failed to list users: {str(ve)}")
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        return jsonify({'error': f'Failed to list users: {str(e)}'}), 500
