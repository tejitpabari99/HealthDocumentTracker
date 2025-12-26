"""
User service layer for Cosmos DB operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from azure.cosmos import exceptions
from Backend.config import get_users_container
from Backend.models.user import User, UserCreate, UserUpdate
from Backend.utils.logger import get_logger
import uuid

logger = get_logger(__name__)


class UserService:
    """Service class for User operations in Cosmos DB."""
    
    @staticmethod
    def create_user(user_data: UserCreate) -> Dict[str, Any]:
        """
        Create a new user in Cosmos DB.
        
        Args:
            user_data: UserCreate model with user information
            
        Returns:
            Created user document as dictionary
            
        Raises:
            Exception: If user creation fails
        """
        try:
            logger.info(f"Creating user with email: {user_data.email}")
            container = get_users_container()
            
            # Generate unique IDs
            user_id = f"user-{uuid.uuid4()}"
            current_time = datetime.utcnow().isoformat() + "Z"
            
            # Create user document
            user_doc = {
                "id": user_id,
                "userId": user_id,
                "schemaVersion": "1.0",
                "email": user_data.email,
                "firstName": user_data.firstName,
                "lastName": user_data.lastName,
                "createdAt": current_time,
                "updatedAt": current_time,
                "settings": {},
                "type": "user"
            }
            
            # Insert into Cosmos DB
            created_user = container.create_item(body=user_doc)
            logger.info(f"User created successfully: {user_id}", extra={
                'custom_dimensions': {'user_id': user_id, 'email': user_data.email}
            })
            return created_user
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create user: {str(e)}", extra={
                'custom_dimensions': {'email': user_data.email}
            }, exc_info=True)
            raise Exception(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: The user ID to retrieve
            
        Returns:
            User document as dictionary or None if not found
        """
        try:
            logger.debug(f"Retrieving user: {user_id}")
            container = get_users_container()
            
            # Read item from Cosmos DB (using userId as partition key)
            user = container.read_item(item=user_id, partition_key=user_id)
            logger.debug(f"User retrieved successfully: {user_id}")
            return user
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"User not found: {user_id}")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to retrieve user {user_id}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve user: {str(e)}")
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            User document as dictionary or None if not found
        """
        try:
            logger.debug(f"Querying user by email: {email}")
            container = get_users_container()
            
            # Query for user by email
            query = "SELECT * FROM c WHERE c.email = @email AND c.type = 'user'"
            parameters = [{"name": "@email", "value": email}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                logger.debug(f"User found by email: {email}")
            else:
                logger.debug(f"No user found with email: {email}")
            
            return items[0] if items else None
            
        except exceptions.CosmosHttpResponseError as e:
            # Extract just the essential error message
            error_msg = str(e).split('\n')[0] if '\n' in str(e) else str(e)
            logger.error(f"Failed to query user by email {email}: {error_msg}")
            raise Exception(f"Failed to query user by email: {error_msg}")
    
    @staticmethod
    def list_users(limit: int = 100, continuation_token: Optional[str] = None) -> Dict[str, Any]:
        """
        List all users with pagination support.
        
        Args:
            limit: Maximum number of users to return
            continuation_token: Token for pagination
            
        Returns:
            Dictionary with users list and continuation token
        """
        try:
            container = get_users_container()
            
            query = "SELECT * FROM c WHERE c.type = 'user' ORDER BY c.createdAt DESC"
            
            # Execute query with pagination
            query_iterable = container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=limit
            )
            
            users = []
            response_headers = {}
            
            # Get items from first page
            for item in query_iterable:
                users.append(item)
                if len(users) >= limit:
                    break
            
            # Get continuation token if available
            try:
                response_headers = query_iterable.response_headers
                next_token = response_headers.get('x-ms-continuation')
            except:
                next_token = None
            
            return {
                "users": users,
                "continuationToken": next_token,
                "count": len(users)
            }
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to list users: {str(e)}")
    
    @staticmethod
    def update_user(user_id: str, update_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """
        Update user information (PATCH operation).
        
        Args:
            user_id: The user ID to update
            update_data: UserUpdate model with fields to update
            
        Returns:
            Updated user document or None if user not found
        """
        try:
            logger.info(f"Updating user: {user_id}")
            container = get_users_container()
            
            # Get existing user
            try:
                existing_user = container.read_item(item=user_id, partition_key=user_id)
            except exceptions.CosmosResourceNotFoundError:
                logger.warning(f"User not found for update: {user_id}")
                return None
            
            # Update only provided fields
            updated_fields = []
            if update_data.email is not None:
                existing_user["email"] = update_data.email
                updated_fields.append("email")
            if update_data.firstName is not None:
                existing_user["firstName"] = update_data.firstName
                updated_fields.append("firstName")
            if update_data.lastName is not None:
                existing_user["lastName"] = update_data.lastName
                updated_fields.append("lastName")
            if update_data.settings is not None:
                existing_user["settings"] = update_data.settings
                updated_fields.append("settings")
            
            # Update timestamp
            existing_user["updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            # Replace item in Cosmos DB
            updated_user = container.replace_item(item=user_id, body=existing_user)
            logger.info(f"User updated successfully: {user_id}", extra={
                'custom_dimensions': {'user_id': user_id, 'updated_fields': updated_fields}
            })
            return updated_user
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to update user: {str(e)}")
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """
        Delete a user from Cosmos DB.
        
        Args:
            user_id: The user ID to delete
            
        Returns:
            True if deleted successfully, False if user not found
        """
        try:
            logger.info(f"Deleting user: {user_id}")
            container = get_users_container()
            
            # Delete item from Cosmos DB
            container.delete_item(item=user_id, partition_key=user_id)
            logger.info(f"User deleted successfully: {user_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"User not found for deletion: {user_id}")
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to delete user: {str(e)}")
