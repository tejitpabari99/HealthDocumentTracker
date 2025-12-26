"""
Search Activity API Endpoints

Tracks and manages search activity records for analytics and user interaction monitoring.
Records include query details, results, user engagement metrics, and device information.
"""
from flask import Blueprint, request, jsonify, g
from Backend.services.search_activity_service import SearchActivityService
from Backend.models.search_activity import SearchActivityCreate, SearchActivityUpdate, RefinedQuery
from Backend.utils.logger import get_logger
from Backend.utils.middleware import require_auth

logger = get_logger(__name__)

# Create Blueprint
search_activity_bp = Blueprint('search_activity', __name__)

@search_activity_bp.route('/search-activities', methods=['POST'])
@require_auth
def create_search_activity():
    """
    Create a new search activity record for the authenticated user.
    
    Authentication: Required (via X-User-Id header in dev, JWT in production)
    
    Expected: JSON body with search activity details
    Returns: JSON response with created search activity
    """
    try:
        # Get user_id from middleware (extracted from auth)
        user_id = g.user_id
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields (userId no longer required in body, comes from auth)
        required_fields = ['searchId', 'originalQuery', 'refinedQuery', 'resultsFound']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse refinedQuery
        refined_query_data = data.get('refinedQuery', {})
        refined_query = RefinedQuery(
            search_phrases=refined_query_data.get('search_phrases', []),
            search_filters=refined_query_data.get('search_filters', {})
        )
        
        # Create SearchActivityCreate model (use authenticated user_id)
        search_activity_data = SearchActivityCreate(
            userId=user_id,
            searchId=data['searchId'],
            originalQuery=data['originalQuery'],
            refinedQuery=refined_query,
            timestamp=data.get('timestamp'),
            resultsFound=data['resultsFound'],
            resultsDocumentIds=data.get('resultsDocumentIds', []),
            resultNumDocuments=data.get('resultNumDocuments', 0),
            topResultScore=data.get('topResultScore'),
            totalResultsReturned=data.get('totalResultsReturned', 0),
            deviceType=data.get('deviceType'),
            appVersion=data.get('appVersion'),
            searchDurationMs=data.get('searchDurationMs')
        )
        
        # Create search activity in Cosmos DB
        created_activity = SearchActivityService.create_search_activity(search_activity_data)
        
        logger.info(f"Search activity created via API: {created_activity.get('id')}")
        
        return jsonify({
            'message': 'Search activity created successfully',
            'searchActivity': created_activity
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create search activity: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to create search activity: {str(e)}'}), 500

@search_activity_bp.route('/search-activities/<search_id>', methods=['GET'])
def get_search_activity(search_id):
    """
    Get a single search activity by ID.
    
    Path Parameters:
        search_id: The search activity ID to retrieve
    
    Returns: JSON with search activity details
    """
    try:
        # Get search activity from Cosmos DB
        search_activity = SearchActivityService.get_search_activity(search_id)
        
        if not search_activity:
            return jsonify({'error': 'Search activity not found'}), 404
        
        return jsonify(search_activity), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve search activity: {str(e)}'}), 500

@search_activity_bp.route('/search-activities/<search_id>', methods=['PATCH'])
def update_search_activity(search_id):
    """
    Update search activity with user interaction metrics.
    
    Tracks user engagement: document opens, click timing, and feedback on answer quality.
    
    Path Parameters:
        search_id: The search activity ID to update
    
    Request Body:
        userOpenedDocument: (optional) Whether user opened a document
        documentOpenedIds: (optional) List of document IDs opened
        timeToClickFirstDocumentMs: (optional) Time taken to click first document
        wasAnswerHelpful: (optional) User feedback on answer helpfulness
    
    Returns: JSON with updated search activity
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create update model
        update_data = SearchActivityUpdate(
            userOpenedDocument=data.get('userOpenedDocument'),
            documentOpenedIds=data.get('documentOpenedIds'),
            timeToClickFirstDocumentMs=data.get('timeToClickFirstDocumentMs'),
            wasAnswerHelpful=data.get('wasAnswerHelpful')
        )
        
        # Update search activity in Cosmos DB
        updated_activity = SearchActivityService.update_search_activity(search_id, update_data)
        
        if not updated_activity:
            logger.warning(f"Search activity not found for update: {search_id}")
            return jsonify({'error': 'Search activity not found'}), 404
        
        logger.info(f"Search activity updated via API: {search_id}")
        
        return jsonify({
            'message': 'Search activity updated successfully',
            'searchActivity': updated_activity
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update search activity: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to update search activity: {str(e)}'}), 500
