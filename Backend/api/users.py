"""
User API Endpoints

Provides CRUD operations for user management in Cosmos DB.
Supports user creation, retrieval, listing, updating, and deletion.
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from Backend.models.user import UserCreate, UserUpdate
from Backend.services.user_service import UserService
from Backend.utils.logger import get_logger

logger = get_logger(__name__)

# Create Blueprint
users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user.
    
    Expected JSON body:
    {
        "email": "user@example.com",
        "firstName": "John",
        "lastName": "Doe"
    }
    
    Returns: Created user document with 201 status
    """
    try:
        logger.info("User creation request received")
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            logger.warning("No data provided in user creation request")
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate and create user data model
        try:
            user_data = UserCreate(**data)
        except ValidationError as e:
            logger.warning(f"Invalid user data: {e.errors()}")
            return jsonify({'error': 'Invalid user data', 'details': e.errors()}), 400
        
        # Check if user with email already exists
        existing_user = UserService.get_user_by_email(user_data.email)
        if existing_user:
            logger.warning(f"User creation failed - email already exists: {user_data.email}")
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create user in Cosmos DB
        created_user = UserService.create_user(user_data)
        
        logger.info(f"User created successfully: {created_user.get('id')}", extra={
            'custom_dimensions': {'user_id': created_user.get('id'), 'email': user_data.email}
        })
        
        return jsonify({
            'message': 'User created successfully',
            'user': created_user
        }), 201
        
    except ValueError as ve:
        logger.error(f"User creation failed: {str(ve)}")
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        logger.error(f"User creation failed: {str(e)}")
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500

@users_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Retrieve a user by ID.
    
    Path parameter:
        user_id: The user ID to retrieve
    
    Returns: User document or 404 if not found
    """
    try:
        logger.debug(f"Retrieving user: {user_id}")
        user = UserService.get_user(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        logger.debug(f"User retrieved successfully: {user_id}")
        return jsonify({'user': user}), 200
        
    except ValueError as ve:
        logger.error(f"Failed to retrieve user {user_id}: {str(ve)}")
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        logger.error(f"Failed to retrieve user {user_id}: {str(e)}")
        return jsonify({'error': f'Failed to retrieve user: {str(e)}'}), 500

@users_bp.route('/users/email/<email>', methods=['GET'])
def get_user_by_email(email):
    """
    Retrieve a user by email address.
    
    Path parameter:
        email: The email address to search for
    
    Returns: User document or 404 if not found
    """
    try:
        logger.debug(f"Retrieving user by email: {email}")
        user = UserService.get_user_by_email(email)
        
        if not user:
            logger.warning(f"User not found with email: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        logger.debug(f"User retrieved by email: {email}")
        return jsonify({'user': user}), 200
        
    except ValueError as ve:
        logger.error(f"Failed to retrieve user by email {email}: {str(ve)}")
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        logger.error(f"Failed to retrieve user by email {email}: {str(e)}")
        return jsonify({'error': f'Failed to retrieve user: {str(e)}'}), 500

@users_bp.route('/users/<user_id>', methods=['PATCH'])
def update_user(user_id):
    """
    Update user information (partial update).
    
    Path parameter:
        user_id: The user ID to update
    
    Expected JSON body (all fields optional):
    {
        "email": "newemail@example.com",
        "firstName": "Jane",
        "lastName": "Smith",
        "settings": { "theme": "dark" }
    }
    
    Returns: Updated user document or 404 if not found
    """
    try:
        logger.info(f"User update request: {user_id}")
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            logger.warning("No data provided in user update request")
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate update data
        try:
            update_data = UserUpdate(**data)
        except ValidationError as e:
            logger.warning(f"Invalid user update data: {e.errors()}")
            return jsonify({'error': 'Invalid update data', 'details': e.errors()}), 400
        
        # Check if at least one field is provided
        if all(getattr(update_data, field) is None for field in ['email', 'firstName', 'lastName', 'settings']):
            logger.warning("No fields provided for user update")
            return jsonify({'error': 'At least one field must be provided for update'}), 400
        
        # Update user in Cosmos DB
        updated_user = UserService.update_user(user_id, update_data)
        
        if not updated_user:
            logger.warning(f"User not found for update: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        logger.info(f"User updated successfully: {user_id}")
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user
        }), 200
        
    except ValueError as ve:
        logger.error(f"Failed to update user {user_id}: {str(ve)}")
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {str(e)}")
        return jsonify({'error': f'Failed to update user: {str(e)}'}), 500

@users_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user.
    
    Path parameter:
        user_id: The user ID to delete
    
    Returns: Success message or 404 if not found
    """
    try:
        logger.info(f"User deletion request: {user_id}")
        
        # Delete user from Cosmos DB
        deleted = UserService.delete_user(user_id)
        
        if not deleted:
            logger.warning(f"User not found for deletion: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        logger.info(f"User deleted successfully: {user_id}")
        return jsonify({
            'message': 'User deleted successfully',
            'userId': user_id
        }), 200
        
    except ValueError as ve:
        logger.error(f"Failed to delete user {user_id}: {str(ve)}")
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500
