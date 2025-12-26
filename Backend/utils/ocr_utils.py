"""
OCR utility functions for extracting text from documents and images.
"""
import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


class OCRError(Exception):
    """Base exception for OCR-related errors"""
    pass


class UnsupportedFileTypeError(OCRError):
    """Exception raised when file type is not supported for OCR"""
    pass


class FileSizeTooLargeError(OCRError):
    """Exception raised when file size exceeds supported limits"""
    pass


class OCRExtractionError(OCRError):
    """Exception raised when OCR extraction fails"""
    pass

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
        
    Raises:
        UnsupportedFileTypeError: If file type is not supported
        FileSizeTooLargeError: If file size exceeds limits
        OCRExtractionError: If OCR extraction fails
    """
    # Determine file type
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Check file size (Azure Document Intelligence has a 500MB limit, Computer Vision has 20MB limit)
    file_size_mb = len(file_content) / (1024 * 1024)
    
    # For PDFs and document formats, use Azure Document Intelligence
    if file_extension in ['pdf', 'doc', 'docx'] or 'pdf' in content_type.lower():
        if file_size_mb > 500:
            raise FileSizeTooLargeError(
                f"File size ({file_size_mb:.1f}MB) exceeds the maximum supported size of 500MB for document files. "
                "Please upload a smaller file."
            )
        return extract_text_from_document(file_content, blob_url, filename)
    
    # For images, use Azure Computer Vision
    elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff'] or 'image' in content_type.lower():
        if file_size_mb > 20:
            raise FileSizeTooLargeError(
                f"File size ({file_size_mb:.1f}MB) exceeds the maximum supported size of 20MB for image files. "
                "Please upload a smaller image."
            )
        text = extract_text_from_image(file_content, filename)
        # Return as single page
        return [{"page_number": 1, "text": text}] if text else []
    
    else:
        # Unsupported file type
        supported_types = "PDF, DOC, DOCX, JPG, JPEG, PNG, BMP, TIFF"
        raise UnsupportedFileTypeError(
            f"File type '.{file_extension}' is not supported. "
            f"Supported file types are: {supported_types}"
        )

def extract_text_from_document(file_content, blob_url=None, filename="document"):
    """
    Extract text from PDF/DOC files using Azure Document Intelligence
    
    Args:
        file_content: Binary content of the document
        blob_url: Optional blob URL for large documents (recommended for files > 4MB)
        filename: Original filename for error messages
    
    Returns:
        List of dictionaries with page_number and text for each page
        
    Raises:
        OCRExtractionError: If extraction fails
    """
    try:
        # Get Azure Document Intelligence credentials from environment
        doc_intel_endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        doc_intel_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        
        if not doc_intel_endpoint or not doc_intel_key:
            raise OCRExtractionError(
                "OCR service is not configured. Please contact support."
            )
        
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
        
        # If still no data, raise an error
        if not pages_data:
            raise OCRExtractionError(
                f"No text could be extracted from the document '{filename}'. "
                "The file may be empty, corrupted, or contain only images without text."
            )
        
        return pages_data
        
    except OCRExtractionError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Wrap other exceptions
        error_msg = str(e)
        if "InvalidRequest" in error_msg or "InvalidImage" in error_msg:
            raise OCRExtractionError(
                f"The file '{filename}' could not be processed. It may be corrupted or in an unsupported format."
            )
        elif "Unauthorized" in error_msg or "401" in error_msg:
            raise OCRExtractionError(
                "OCR service authentication failed. Please contact support."
            )
        else:
            raise OCRExtractionError(
                f"Failed to extract text from '{filename}': {error_msg}"
            )

def extract_text_from_image(file_content, filename="image"):
    """
    Extract text from image files using Azure Computer Vision
    
    Args:
        file_content: Binary content of the image
        filename: Original filename for error messages
    
    Returns:
        Extracted text as string
        
    Raises:
        OCRExtractionError: If extraction fails
    """
    try:
        # Get Azure Computer Vision credentials from environment
        vision_endpoint = os.getenv('AZURE_VISION_ENDPOINT')
        vision_key = os.getenv('AZURE_VISION_KEY')
        
        if not vision_endpoint or not vision_key:
            raise OCRExtractionError(
                "OCR service is not configured. Please contact support."
            )
        
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
        
        # If no text extracted, raise error
        if not extracted_text.strip():
            raise OCRExtractionError(
                f"No text could be extracted from the image '{filename}'. "
                "The image may not contain any readable text."
            )
        
        return extracted_text.strip()
        
    except OCRExtractionError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Wrap other exceptions
        error_msg = str(e)
        if "InvalidImageFormat" in error_msg or "InvalidImage" in error_msg:
            raise OCRExtractionError(
                f"The image '{filename}' is in an invalid format or is corrupted."
            )
        elif "Unauthorized" in error_msg or "401" in error_msg:
            raise OCRExtractionError(
                "OCR service authentication failed. Please contact support."
            )
        else:
            raise OCRExtractionError(
                f"Failed to extract text from image '{filename}': {error_msg}"
            )
