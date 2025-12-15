"""
Upload API endpoint for document uploads to Azure Blob Storage
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from datetime import datetime
import uuid
import os
import io
from config import (
    allowed_file,
    get_blob_service_client,
    get_search_client,
    AZURE_STORAGE_CONTAINER_NAME_RAW,
    ALLOWED_EXTENSIONS
)

# Create Blueprint
upload_bp = Blueprint('upload', __name__)

def extract_text_with_ocr(file_content, content_type, filename):
    """
    Extract text from document using Azure Document Intelligence or Computer Vision
    
    Args:
        file_content: Binary content of the file
        content_type: MIME type of the file
        filename: Original filename to check extension
    
    Returns:
        List of dictionaries with page_number and text for each page
    """
    try:
        # Determine file type
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # For PDFs and document formats, use Azure Document Intelligence
        if file_extension in ['pdf', 'doc', 'docx'] or 'pdf' in content_type.lower():
            return extract_text_from_document(file_content)
        
        # For images, use Azure Computer Vision
        elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff'] or 'image' in content_type.lower():
            text = extract_text_from_image(file_content)
            # Return as single page
            return [{"page_number": 1, "text": text}]
        
        else:
            print(f"Warning: Unsupported file type for OCR: {file_extension}")
            return [{"page_number": 1, "text": ""}]
        
    except Exception as e:
        print(f"OCR extraction failed: {str(e)}")
        return [{"page_number": 1, "text": ""}]

def extract_text_from_document(file_content):
    """
    Extract text from PDF/DOC files using Azure Document Intelligence
    
    Args:
        file_content: Binary content of the document
    
    Returns:
        List of dictionaries with page_number and text for each page
    """
    try:
        # Get Azure Document Intelligence credentials from environment
        doc_intel_endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        doc_intel_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        if not doc_intel_endpoint or not doc_intel_key:
            print("Warning: Azure Document Intelligence not configured, skipping document OCR")
            return [{"page_number": 1, "text": ""}]
        
        # Create Document Intelligence client
        client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=AzureKeyCredential(doc_intel_key)
        )
        
        # Analyze document using prebuilt-read model
        poller = client.begin_analyze_document(
            "prebuilt-read",
            analyze_request=file_content,
            content_type="application/octet-stream"
        )
        
        result = poller.result()
        
        # Extract text page by page
        pages_data = []
        if result.pages:
            for page in result.pages:
                page_number = page.page_number
                page_text = ""
                
                # Extract text from lines on this page
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        page_text += line.content + "\n"
                
                pages_data.append({
                    "page_number": page_number,
                    "text": page_text.strip()
                })
        
        # If no pages found but there's content, return as single page
        if not pages_data and result.content:
            pages_data.append({
                "page_number": 1,
                "text": result.content.strip()
            })
        
        return pages_data if pages_data else [{"page_number": 1, "text": ""}]
        
    except Exception as e:
        print(f"Document Intelligence extraction failed: {str(e)}")
        return [{"page_number": 1, "text": ""}]

def extract_text_from_image(file_content):
    """
    Extract text from image files using Azure Computer Vision
    
    Args:
        file_content: Binary content of the image
    
    Returns:
        Extracted text as string
    """
    try:
        # Get Azure Computer Vision credentials from environment
        vision_endpoint = os.getenv('AZURE_VISION_ENDPOINT')
        vision_key = os.getenv('AZURE_VISION_KEY')
        
        if not vision_endpoint or not vision_key:
            print("Warning: Azure Computer Vision not configured, skipping image OCR")
            return ""
        
        # Create Computer Vision client
        client = ImageAnalysisClient(
            endpoint=vision_endpoint,
            credential=AzureKeyCredential(vision_key)
        )
        
        # Perform OCR
        result = client.analyze(
            image_data=file_content,
            visual_features=[VisualFeatures.READ]
        )
        
        # Extract text from result
        extracted_text = ""
        if result.read is not None:
            for block in result.read.blocks:
                for line in block.lines:
                    extracted_text += line.text + "\n"
        
        return extracted_text.strip()
        
    except Exception as e:
        print(f"Computer Vision extraction failed: {str(e)}")
        return ""

@upload_bp.route('/documents', methods=['POST'])
def upload_document():
    """
    Upload a document to Azure Blob Storage
    
    Expected: multipart/form-data with 'file' field
    Returns: JSON with blob URL and metadata
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension (optional)
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Secure the filename and generate unique blob name
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        
        # Get blob service client
        blob_service_client = get_blob_service_client()
        
        # Get container client (create container if it doesn't exist)
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME_RAW)
        try:
            container_client.create_container()
        except Exception:
            # Container already exists
            pass
        
        # Upload file to blob storage
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_STORAGE_CONTAINER_NAME_RAW,
            blob=unique_filename
        )
        
        # Read file content for OCR
        file.seek(0)
        file_content = file.read()
        content_type = file.content_type or 'application/octet-stream'
        
        # Upload the original file
        file_stream = io.BytesIO(file_content)
        blob_client.upload_blob(file_stream, overwrite=True)
        
        # Get blob URL
        blob_url = blob_client.url
        
        # Extract text using OCR - returns list of pages
        pages_data = extract_text_with_ocr(file_content, content_type, original_filename)
        
        # Generate a unique ReportId for this document (connects all pages)
        report_id = str(uuid.uuid4())
        upload_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Create one search document per page
        search_documents = []
        total_text_length = 0
        
        for page_data in pages_data:
            page_document_id = str(uuid.uuid4())
            page_text = page_data.get('text', '')
            page_number = page_data.get('page_number', 1)
            total_text_length += len(page_text)
            
            search_document = {
                "id": page_document_id,
                "ReportId": report_id,
                "PageNumber": page_number,
                "ExtractedText": page_text,
                "BlobUri": blob_url,
                "ContentType": content_type,
                "FileName": original_filename,
                "UploadedAt": upload_timestamp
            }
            
            search_documents.append(search_document)
        
        # Upload all page documents to Azure AI Search
        uploaded_pages = 0
        try:
            search_client = get_search_client()
            result = search_client.upload_documents(documents=search_documents)
            uploaded_pages = len(search_documents)
            print(f"Uploaded {uploaded_pages} pages to Azure AI Search with ReportId: {report_id}")
        except Exception as search_error:
            print(f"Warning: Failed to upload to Azure AI Search: {str(search_error)}")
            # Continue even if search upload fails
        
        return jsonify({
            'message': 'File uploaded successfully',
            'blob_name': unique_filename,
            'original_filename': original_filename,
            'blob_url': blob_url,
            'report_id': report_id,
            'pages_uploaded': uploaded_pages,
            'container': AZURE_STORAGE_CONTAINER_NAME_RAW,
            'extracted_text_length': total_text_length
        }), 201
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500
