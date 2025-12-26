"""
Search API Endpoints

Provides AI-powered document search using Azure OpenAI and Azure AI Search.
Delegates all business logic to SearchService.
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import json
import uuid
from Backend.services.search_service import SearchService
from Backend.services.search_activity_service import SearchActivityService
from Backend.models.search_activity import SearchActivityCreate, RefinedQuery
from Backend.utils.logger import get_logger
from Backend.utils.middleware import require_auth

logger = get_logger(__name__)

# Create Blueprint
search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
@require_auth
def search_documents():
    """
    Search for documents using AI-powered search for the authenticated user.
    Delegates to SearchService for all business logic.
    
    Authentication: Required (via X-User-Id header in dev, JWT in production)
    
    Expected: JSON body with 'query' field
    Returns: JSON response with formatted answer and document references
    """
    try:
        # Get user_id from middleware (extracted from auth)
        user_id = g.user_id
        
        logger.info(f"Search request received for user: {user_id}")
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            logger.warning("No query provided in search request")
            return jsonify({'error': 'No query provided'}), 400
        
        user_query = data.get('query', '').strip()
        if not user_query:
            logger.warning("Empty query provided in search request")
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Get optional tracking parameters
        device_type = data.get('deviceType')
        app_version = data.get('appVersion')
        
        # Generate unique search ID
        search_id = f"search-{uuid.uuid4()}"
        
        logger.info(f"Processing search query", extra={
            'custom_dimensions': {
                'search_id': search_id,
                'user_id': user_id,
                'query': user_query
            }
        })
        
        # Perform search using SearchService
        search_result = SearchService.perform_search(
            user_query=user_query,
            user_id=user_id,
            device_type=device_type,
            app_version=app_version
        )
        
        # Extract results
        answer_text = search_result['answer_text']
        sas_url = search_result['document_sas_url']
        refined_query = search_result['refined_query']
        search_duration_ms = search_result['search_duration_ms']
        document_id = search_result.get('document_id')
        extracted_text = search_result['extracted_text']
        
        # Create SearchActivity record if userId is provided
        search_activity_id = None
        if user_id:
            try:
                # Parse refined query JSON
                refined_query_json = json.loads(refined_query)
                refined_query_obj = RefinedQuery(
                    search_phrases=refined_query_json.get('search_phrases', []),
                    search_filters=refined_query_json.get('search_filters', {})
                )
                
                # Determine if results were found
                results_found = bool(extracted_text and document_id)
                
                # Build list of document identifiers (both blobUri and documentId if available)
                result_doc_ids = [document_id] if document_id else []
                
                # Create search activity
                search_activity_data = SearchActivityCreate(
                    userId=user_id,
                    searchId=search_id,
                    originalQuery=user_query,
                    refinedQuery=refined_query_obj,
                    resultsFound=results_found,
                    resultsDocumentIds=result_doc_ids,
                    resultNumDocuments=1 if results_found else 0,
                    topResultScore=None,
                    totalResultsReturned=1 if results_found else 0,
                    deviceType=device_type,
                    appVersion=app_version,
                    searchDurationMs=search_duration_ms
                )
                
                created_activity = SearchActivityService.create_search_activity(search_activity_data)
                search_activity_id = created_activity.get('id')
                logger.debug(f"Created search activity: {search_activity_id}")
                
            except Exception as activity_error:
                logger.warning(f"Failed to create search activity: {str(activity_error)}")
                # Continue without failing the search
        
        logger.info(f"Search completed successfully", extra={
            'custom_dimensions': {
                'search_id': search_id,
                'user_id': user_id,
                'duration_ms': search_duration_ms,
                'results_found': bool(extracted_text)
            }
        })
        
        response_data = {
            'message': answer_text,
            'sas_url': sas_url,
            'query': user_query,
            'refined_query': refined_query,
            'searchId': search_id,
            'searchDurationMs': search_duration_ms,
            'documentId': document_id,
            'searchActivityId': search_activity_id
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        return jsonify({'error': f'Search failed: {str(e)}'}), 500
