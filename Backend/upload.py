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
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import uuid
import os
import io
from Backend.config import (
    allowed_file,
    get_blob_service_client,
    get_search_client,
    AZURE_STORAGE_CONTAINER_NAME_RAW,
    ALLOWED_EXTENSIONS
)

# Create Blueprint
upload_bp = Blueprint('upload', __name__)

def extract_text_with_ocr(file_content, content_type, filename, blob_url=None):
    """
    Extract text from document using Azure Document Intelligence or Computer Vision
    
    Args:
        file_content: Binary content of the file
        content_type: MIME type of the file
        filename: Original filename to check extension
        blob_url: Optional blob URL for large documents
    
    Returns:
        List of dictionaries with page_number and text for each page
    """
    try:
        # Determine file type
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # For PDFs and document formats, use Azure Document Intelligence
        if file_extension in ['pdf', 'doc', 'docx'] or 'pdf' in content_type.lower():
            return extract_text_from_document(file_content, blob_url)
        
        # For images, use Azure Computer Vision
        elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff'] or 'image' in content_type.lower():
            text = extract_text_from_image(file_content)
            # Return as single page
            return [{"page_number": 1, "text": text}] if text else []
        
        else:
            print(f"Warning: Unsupported file type for OCR: {file_extension}")
            return []
        
    except Exception as e:
        print(f"OCR extraction failed: {str(e)}")
        return []

def extract_text_from_document(file_content, blob_url=None):
    """
    Extract text from PDF/DOC files using Azure Document Intelligence
    
    Args:
        file_content: Binary content of the document
        blob_url: Optional blob URL for large documents (recommended for files > 4MB)
    
    Returns:
        List of dictionaries with page_number and text for each page
    """
    try:
        # Get Azure Document Intelligence credentials from environment
        doc_intel_endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        doc_intel_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        if not doc_intel_endpoint or not doc_intel_key:
            print("Warning: Azure Document Intelligence not configured, skipping document OCR")
            return []
        
        # Create Document Intelligence client
        client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=AzureKeyCredential(doc_intel_key)
        )
        
        # Use blob URL approach for large files (more reliable for 20+ page documents)
        if blob_url:
            print(f"Using blob URL approach for document: {blob_url}")
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
            
            poller = client.begin_analyze_document(
                "prebuilt-read",
                AnalyzeDocumentRequest(url_source=blob_url)
            )
        else:
            # For smaller files, use direct content
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
                
                # Only add pages with actual text content
                if page_text.strip():
                    pages_data.append({
                        "page_number": page_number,
                        "text": page_text.strip()
                    })
        
        # If no pages found but there's content, return as single page
        if not pages_data and result.content and result.content.strip():
            pages_data.append({
                "page_number": 1,
                "text": result.content.strip()
            })
        
        return pages_data
        
    except Exception as e:
        print(f"Document Intelligence extraction failed: {str(e)}")
        # Return empty list on failure instead of placeholder
        return []

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
        
        # Check file size to determine OCR approach
        file_size_mb = len(file_content) / (1024 * 1024)
        use_blob_url = file_size_mb > 4  # Use blob URL for files larger than 4MB
        
        # Generate SAS URL for Document Intelligence to access the blob
        blob_url_with_sas = None
        if use_blob_url:
            try:
                # Generate SAS token valid for 1 hour with read permission
                sas_token = generate_blob_sas(
                    account_name=blob_service_client.account_name,
                    container_name=AZURE_STORAGE_CONTAINER_NAME_RAW,
                    blob_name=unique_filename,
                    account_key=blob_service_client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=1)
                )
                blob_url_with_sas = f"{blob_url}?{sas_token}"
                print(f"Generated SAS URL for Document Intelligence (size: {file_size_mb:.2f}MB)")
            except Exception as sas_error:
                print(f"Warning: Failed to generate SAS token: {str(sas_error)}")
                # Fall back to direct content approach
                use_blob_url = False
        
        # Extract text using OCR - returns list of pages
        # For large files, pass SAS URL to use URL-based analysis
        pages_data = extract_text_with_ocr(
            file_content, 
            content_type, 
            original_filename,
            blob_url_with_sas if use_blob_url else None
        )
        
        # Generate a unique ReportId for this document (connects all pages)
        report_id = str(uuid.uuid4())
        upload_timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Only create search documents if OCR extracted text
        if not pages_data:
            # OCR failed or returned no content - delete the blob
            try:
                blob_client.delete_blob()
                print(f"Deleted blob {unique_filename} due to OCR failure")
            except Exception as delete_error:
                print(f"Warning: Failed to delete blob after OCR failure: {str(delete_error)}")
            
            return jsonify({
                'error': 'OCR extraction failed',
                'message': 'No text could be extracted from the document. File has been removed from storage.',
                'details': 'The document may be a scanned image without text, corrupted, or in an unsupported format.',
                'original_filename': original_filename,
                'file_size_mb': round(file_size_mb, 2)
            }), 400
        
        # Create one search document per page (only for pages with content)
        search_documents = []
        total_text_length = 0
        
        for page_data in pages_data:
            page_document_id = str(uuid.uuid4())
            page_text = page_data.get('text', '')
            page_number = page_data.get('page_number', 1)
            
            # Skip empty pages
            if not page_text.strip():
                continue
                
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
        
        # Only upload to Azure AI Search if we have documents with content
        uploaded_pages = 0
        if search_documents:
            try:
                search_client = get_search_client()
                result = search_client.upload_documents(documents=search_documents)
                uploaded_pages = len(search_documents)
                print(f"Uploaded {uploaded_pages} pages to Azure AI Search with ReportId: {report_id}")
            except Exception as search_error:
                print(f"Warning: Failed to upload to Azure AI Search: {str(search_error)}")
                return jsonify({
                    'message': 'File uploaded successfully but search indexing failed',
                    'warning': f'Document is stored in blob storage but could not be indexed: {str(search_error)}',
                    'blob_name': unique_filename,
                    'original_filename': original_filename,
                    'blob_url': blob_url,
                    'report_id': report_id,
                    'pages_uploaded': 0,
                    'container': AZURE_STORAGE_CONTAINER_NAME_RAW,
                    'extracted_text_length': total_text_length
                }), 201
        else:
            # Pages were extracted but all were empty - delete the blob
            try:
                blob_client.delete_blob()
                print(f"Deleted blob {unique_filename} due to empty pages")
            except Exception as delete_error:
                print(f"Warning: Failed to delete blob after empty pages: {str(delete_error)}")
            
            return jsonify({
                'error': 'No text content found',
                'message': 'All pages in the document were empty. File has been removed from storage.',
                'details': 'The document may contain only images without text or be blank pages.',
                'original_filename': original_filename,
                'pages_processed': len(pages_data),
                'file_size_mb': round(file_size_mb, 2)
            }), 400
        
        return jsonify({
            'message': 'File uploaded successfully',
            'blob_name': unique_filename,
            'original_filename': original_filename,
            'blob_url': blob_url,
            'report_id': report_id,
            'pages_uploaded': uploaded_pages,
            'container': AZURE_STORAGE_CONTAINER_NAME_RAW,
            'extracted_text_length': total_text_length,
            'ocr_method': 'blob_url' if use_blob_url else 'direct_content'
        }), 201
        
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500
