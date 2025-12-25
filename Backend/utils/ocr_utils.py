"""
OCR utility functions for extracting text from documents and images.
"""
import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

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
