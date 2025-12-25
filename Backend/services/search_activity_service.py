"""
SearchActivity service layer for Cosmos DB operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from azure.cosmos import exceptions
from Backend.config import (
    get_cosmos_database,
    get_search_activity_container
)
from Backend.models.search_activity import SearchActivity, SearchActivityCreate, SearchActivityUpdate, RefinedQuery
from Backend.utils.logger import get_logger
import uuid
import os

logger = get_logger(__name__)

class SearchActivityService:
    """Service class for SearchActivity operations in Cosmos DB."""
    
    @staticmethod
    def create_search_activity(search_data: SearchActivityCreate) -> Dict[str, Any]:
        """
        Create a new search activity record in Cosmos DB.
        
        Args:
            search_data: SearchActivityCreate model with search information
            
        Returns:
            Created search activity as dictionary
            
        Raises:
            Exception: If search activity creation fails
        """
        try:
            logger.info(f"Creating search activity for user: {search_data.userId}", extra={
                'custom_dimensions': {
                    'user_id': search_data.userId,
                    'query': search_data.originalQuery,
                    'results_found': search_data.resultsFound
                }
            })
            container = get_search_activity_container()
            
            # Generate unique IDs
            search_id = f"search-{uuid.uuid4()}"
            current_time = datetime.utcnow().isoformat() + "Z"
            
            # Create search activity document
            search_activity = {
                "id": search_id,
                "userId": search_data.userId,
                "searchId": search_data.searchId,
                "schemaVersion": "1.0",
                "originalQuery": search_data.originalQuery,
                "refinedQuery": {
                    "search_phrases": search_data.refinedQuery.search_phrases,
                    "search_filters": search_data.refinedQuery.search_filters
                },
                "timestamp": search_data.timestamp or current_time,
                "resultsFound": search_data.resultsFound,
                "resultsDocumentIds": search_data.resultsDocumentIds,
                "resultNumDocuments": search_data.resultNumDocuments,
                "topResultScore": search_data.topResultScore,
                "totalResultsReturned": search_data.totalResultsReturned,
                "userOpenedDocument": None,
                "documentOpenedIds": [],
                "timeToClickFirstDocumentMs": None,
                "wasAnswerHelpful": None,
                "deviceType": search_data.deviceType,
                "appVersion": search_data.appVersion,
                "searchDurationMs": search_data.searchDurationMs,
                "type": "search_activity"
            }
            
            # Insert into Cosmos DB
            created_search = container.create_item(body=search_activity)
            logger.info(f"Search activity created successfully: {search_id}", extra={
                'custom_dimensions': {'search_id': search_id, 'user_id': search_data.userId}
            })
            return created_search
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create search activity: {str(e)}", extra={
                'custom_dimensions': {'user_id': search_data.userId}
            }, exc_info=True)
            raise Exception(f"Failed to create search activity: {str(e)}")
    
    @staticmethod
    def get_search_activity(search_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a search activity by ID.
        
        Args:
            search_id: The search activity ID to retrieve
            
        Returns:
            Search activity as dictionary or None if not found
        """
        try:
            logger.debug(f"Retrieving search activity: {search_id}")
            container = get_search_activity_container()
            
            # Query for search activity by ID
            query = "SELECT * FROM c WHERE c.id = @searchId AND c.type = 'search_activity'"
            parameters = [{"name": "@searchId", "value": search_id}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                logger.debug(f"Search activity retrieved: {search_id}")
            else:
                logger.warning(f"Search activity not found: {search_id}")
            
            return items[0] if items else None
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to retrieve search activity {search_id}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve search activity: {str(e)}")
    
    @staticmethod
    def list_search_activities_by_user(user_id: str, limit: int = 100) -> Dict[str, Any]:
        """
        List all search activities for a specific user.
        
        Args:
            user_id: The user ID to filter by
            limit: Maximum number of search activities to return
            
        Returns:
            Dictionary with search activities list and count
        """
        try:
            container = get_search_activity_container()
            
            query = """
                SELECT * FROM c 
                WHERE c.userId = @userId 
                AND c.type = 'search_activity' 
                ORDER BY c.timestamp DESC
            """
            parameters = [{"name": "@userId", "value": user_id}]
            
            # Execute query
            query_iterable = container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=limit
            )
            
            activities = []
            for item in query_iterable:
                activities.append(item)
                if len(activities) >= limit:
                    break
            
            return {
                "searchActivities": activities,
                "count": len(activities),
                "userId": user_id
            }
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to list search activities: {str(e)}")
    
    @staticmethod
    def update_search_activity(search_id: str, update_data: SearchActivityUpdate) -> Optional[Dict[str, Any]]:
        """
        Update search activity information (PATCH operation).
        Used to track user interactions like opening documents.
        Only updates the fields that are provided in update_data.
        
        Args:
            search_id: The search activity ID to update
            update_data: SearchActivityUpdate model with fields to update
            
        Returns:
            Updated search activity or None if not found
        """
        try:
            logger.info(f"Updating search activity: {search_id}")
            container = get_search_activity_container()
            
            # Get existing search activity
            existing_activity = SearchActivityService.get_search_activity(search_id)
            if not existing_activity:
                logger.warning(f"Search activity not found for update: {search_id}")
                return None
            
            # Update only provided fields (exclude None values)
            update_dict = update_data.model_dump(exclude_none=True)
            for field, value in update_dict.items():
                existing_activity[field] = value
            
            # Replace item in Cosmos DB
            updated_activity = container.replace_item(
                item=existing_activity["id"], 
                body=existing_activity
            )
            logger.info(f"Search activity updated successfully: {search_id}", extra={
                'custom_dimensions': {'search_id': search_id, 'updated_fields': list(update_dict.keys())}
            })
            return updated_activity
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update search activity {search_id}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to update search activity: {str(e)}")
    
    @staticmethod
    def get_search_activity_by_search_id(search_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a search activity by searchId field.
        
        Args:
            search_id: The searchId value to search for
            
        Returns:
            Search activity as dictionary or None if not found
        """
        try:
            container = get_search_activity_container()
            
            query = "SELECT * FROM c WHERE c.searchId = @searchId AND c.type = 'search_activity'"
            parameters = [{"name": "@searchId", "value": search_id}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
            
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Failed to query search activity by searchId: {str(e)}")
