"""
Search API endpoint for document search functionality
"""
from flask import Blueprint, request, jsonify
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import os
import json
from config import (
    get_blob_service_client,
    get_search_client,
    get_openai_client,
    AZURE_STORAGE_CONTAINER_NAME_RAW,
)

# Create Blueprint
search_bp = Blueprint('search', __name__)

@search_bp.route('/documents/search', methods=['POST'])
def search_documents():
    """
    Search for documents using 3-step process:
    1. Refine query with Azure OpenAI
    2. Search documents with Azure AI Search
    3. Generate formatted answer with Azure OpenAI
    
    Expected: JSON body with 'query' field
    Returns: JSON response with formatted answer and document references
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        user_query = data.get('query', '').strip()
        if not user_query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        print(f"Original query: {user_query}")
        
        # Step 1: Refine the query with Azure OpenAI
        openai_client = get_openai_client()
        
        system_query = """You are a query-expansion assistant. Input: a user's question. Output: a JSON with two fields:
        - "search_phrases": [list of concise search phrases and synonyms to use, prioritized]
        - "search_filters": { optional filters like "lab", "date_range" }
        Example:
        Input: "What are my iron levels?"
        Output:
        {
        "search_phrases": ["ferritin", "serum ferritin", "iron", "transferrin saturation", "Fe", "ferritin level"],
        "search_filters": {}
        }
        """

        refine_response = openai_client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4'),
            messages=[
                {"role": "system", "content": system_query},
                {"role": "user", "content": user_query}
            ]
        )
        refined_query = refine_response.choices[0].message.content.strip()
        print(f"Refined query: {refined_query}")

        # Step 2: Search documents with Azure AI Search
        search_client = get_search_client()
        
        search_results = search_client.search(
            search_text=refined_query,
            select=["ExtractedText", "BlobUri", "FileName"],
            top=1 # Get top 5 relevant documents
        )

        extractedText = ""
        blobUri = ""
        fileName = ""
        for result in search_results:
            # Collect search result
            extractedText = result.get("ExtractedText", "")
            blobUri = result.get("BlobUri", "")
            fileName = result.get("FileName", "")
            break

        print(extractedText)

        answer_system_prompt = """You are a medical information extraction assistant. You will be given:
            1. A user's question.
            2. A set of text passages extracted from medical reports.

            Your job is to return the single value from the passages that best answers the user's question.

            Rules:
            - Use only the information provided in the passages.
            - If the value for the exact lab test the user asked for is not present, return the closest clinically related marker.
            - For iron-related questions:
                - Ferritin, Transferrin Saturation (TSAT), TIBC, and Serum Iron are all acceptable substitutes.
            - Do NOT hallucinate values that are not explicitly present.
            - Return null fields if no clinically related value is present at all.
            - Provide the name of the analyte you used, its value, its unit, and the best document reference.
            - Always return JSON ONLY following this schema:

            {
            "analyte_used": string | null,
            "value": string | null,
            "unit": string | null,
            "answer_text": string | null,
            "document_link": string | null
        }"""

        extracts = f"""{
            {
                "Text": {extractedText},
                "Document link": {blobUri}
            }
        }"""

        answer_user_prompt = f"""
        Question: {user_query}
        Extracts: {extracts}
        """

        answer_response = openai_client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4'),
            messages=[
                {"role": "system", "content": answer_system_prompt},
                {"role": "user", "content": answer_user_prompt}
            ]
        )
        
        formatted_answer = answer_response.choices[0].message.content.strip()
        print(f"Generated answer: {formatted_answer}...")
        
        # Generate SAS URLs for referenced documents
        blob_service_client = get_blob_service_client()
        
        formatted_answer_json = json.loads(formatted_answer)

        answer_text = formatted_answer_json.get("answer_text") or "No answer could be generated from the documents."
        blob_uri = formatted_answer_json.get("document_link")
        sas_url = None
        if blob_uri:
            try:
                # Extract blob name from URI
                blob_parts = blob_uri.split('/')
                blob_name = blob_parts[-1] if blob_parts else None
                
                if blob_name:
                    # Generate SAS token (valid for 1 hour)
                    sas_token = generate_blob_sas(
                        account_name=blob_service_client.account_name,
                        container_name=AZURE_STORAGE_CONTAINER_NAME_RAW,
                        blob_name=blob_name,
                        account_key=blob_service_client.credential.account_key,
                        permission=BlobSasPermissions(read=True),
                        expiry=datetime.utcnow() + timedelta(hours=1)
                    )
                    
                    sas_url = f"{blob_uri}?{sas_token}"
            except Exception as sas_error:
                print(f"Error generating SAS token: {str(sas_error)}")
                # Include without SAS if generation fails
                sas_url = blob_uri

        # Format final message with document references
        final_message = answer_text
        if sas_url:
            final_message += f"\n\n**Document Reference: {sas_url}**"
        
        print(final_message)
        return jsonify({
            'message': final_message,
            'query': user_query,
            'refined_query': refined_query
        }), 200
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500
