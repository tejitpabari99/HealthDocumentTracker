# HealthDocumentTracker

A Python Flask API for managing health documents with Azure Blob Storage integration.

## Features

- **Document Upload**: Upload health documents to Azure Blob Storage with automatic OCR text extraction
- **Azure AI Search Integration**: Automatically indexes documents in Azure AI Search with extracted text, file metadata, and timestamps
- **Document Search**: Advanced 3-step search process using Azure OpenAI for query refinement and answer generation, with Azure AI Search for document retrieval
- **OCR Text Extraction**: Uses Azure Document Intelligence for PDFs/documents and Azure Computer Vision for images
- **Environment Configuration**: Secure credential management using environment variables
- **File Validation**: Support for common document formats (PDF, DOC, DOCX, TXT, images)

## Prerequisites

- Python 3.8 or higher
- Azure Storage Account with Blob Storage enabled
- Azure Computer Vision resource (for image OCR text extraction)
- Azure Document Intelligence resource (for PDF/document OCR text extraction)
- Azure AI Search service with an index configured
- Azure OpenAI service with a deployed GPT model (for search query refinement and answer generation)

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/gitika-bose/HealthDocumentTracker.git
cd HealthDocumentTracker
```

2. **Navigate to the Backend directory**
```bash
cd Backend
```

3. **Create and activate a virtual environment** (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Getting Your Azure Credentials

#### Azure Storage Connection String
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Storage Account
3. Go to **Security + networking** → **Access keys**
4. Copy the **Connection string** from Key1 or Key2

#### Azure Computer Vision Credentials
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Computer Vision resource (or create one)
3. Go to **Keys and Endpoint**
4. Copy the **Endpoint** and **Key 1**

#### Azure Document Intelligence Credentials
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Document Intelligence resource (or create one)
3. Go to **Keys and Endpoint**
4. Copy the **Endpoint** and **Key 1**

#### Azure AI Search Credentials
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your AI Search service (or create one)
3. Go to **Keys**
4. Copy the **URL** (endpoint) and **Primary admin key**

#### Azure OpenAI Credentials
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource (or create one)
3. Go to **Keys and Endpoint**
4. Copy the **Endpoint** and **Key 1**
5. Note your **Deployment name** (e.g., gpt-4, gpt-35-turbo)

## Running the API

Start the Flask application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Upload Document

**Endpoint**: `POST /documents`

**Description**: Upload a document to Azure Blob Storage with automatic OCR text extraction and metadata generation

**Request Type**: `multipart/form-data`

**Parameters**:
- `file` (required): The file to upload

**Supported File Types**: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG

**What Happens**:
1. File is uploaded to Azure Blob Storage
2. OCR extracts text from the document using Azure Computer Vision
3. Document metadata is automatically indexed in Azure AI Search with:
   - `id`: Unique document identifier
   - `extractedText`: OCR-extracted text from the document
   - `blobUri`: URL of the original document in storage
   - `contentType`: MIME type of the file
   - `fileName`: Original filename
   - `uploadedAt`: ISO 8601 timestamp

**Example using cURL**:
```bash
curl -X POST http://localhost:5000/documents \
  -F "file=@/path/to/your/document.pdf"
```

**Example using Python**:
```python
import requests

url = "http://localhost:5000/documents"
files = {'file': open('document.pdf', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

**Success Response** (201):
```json
{
  "message": "File uploaded successfully",
  "blob_name": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_document.pdf",
  "original_filename": "document.pdf",
  "blob_url": "https://youraccount.blob.core.windows.net/health-documents-raw/a1b2c3d4-e5f6-7890-abcd-ef1234567890_document.pdf",
  "document_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "container": "health-documents-raw",
  "extracted_text_length": 1234
}
```

**Azure AI Search Document Structure**:
```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "extractedText": "This is the extracted text from the document...",
  "blobUri": "https://youraccount.blob.core.windows.net/health-documents-raw/document.pdf",
  "contentType": "application/pdf",
  "fileName": "document.pdf",
  "uploadedAt": "2025-12-08T11:00:00.000Z"
}
```

**Error Responses**:
- `400`: No file provided or invalid file type
- `500`: Upload failed or Azure configuration error

**Notes**: 
- OCR requires Azure Computer Vision to be configured. If not configured, the file will still upload but `extractedText` will be empty.
- Metadata is automatically indexed in Azure AI Search for searchability. If AI Search is not configured, the file will still upload to blob storage but indexing will be skipped.

### 2. Search Documents

**Endpoint**: `POST /documents/search`

**Description**: Advanced AI-powered search using a 3-step process with Azure OpenAI and Azure AI Search

**Request Type**: `application/json`

**Parameters**:
```json
{
  "query": "your search text here"
}
```

**What Happens - 3-Step Process**:

1. **Query Refinement (Azure OpenAI)**
   - User's query is sent to Azure OpenAI
   - GPT model refines the query into a search-friendly format
   - Adds medical synonyms and clinical terms (e.g., "iron" → "iron and ferritin")
   
2. **Document Search (Azure AI Search)**
   - Refined query is used to search the Azure AI Search index
   - Retrieves top 5 relevant documents with their extracted text and blob URIs
   
3. **Answer Generation (Azure OpenAI)**
   - Retrieved documents are sent to Azure OpenAI with the refined query
   - GPT model generates a formatted, contextual answer based on the documents
   - SAS tokens are generated for document references (valid for 1 hour)

**Example using cURL**:
```bash
curl -X POST http://localhost:5000/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my iron levels?"}'
```

**Example using Python**:
```python
import requests

url = "http://localhost:5000/documents/search"
data = {"query": "What are my iron levels?"}
response = requests.post(url, json=data)
print(response.json())
```

**Success Response** (200):
```json
{
  "message": "Based on your recent blood work from March 2025, your iron levels show:\n- Serum Iron: 85 mcg/dL (normal range: 60-170)\n- Ferritin: 45 ng/mL (normal range: 20-250)\n\nYour iron and ferritin levels are within normal ranges.\n\n**Document References:**\n- [BloodTest_March2025.pdf](https://youraccount.blob.core.windows.net/health-documents-raw/abc123.pdf?sv=...&sig=...)\n- [LabResults_2025.pdf](https://youraccount.blob.core.windows.net/health-documents-raw/def456.pdf?sv=...&sig=...)",
  "query": "What are my iron levels?",
  "refined_query": "iron levels serum iron ferritin hemoglobin blood test results",
  "documents_found": 2
}
```

**Response Format**:
- `message`: Formatted answer with document references (includes clickable SAS URLs)
- `query`: Original user query
- `refined_query`: AI-refined search query with synonyms
- `documents_found`: Number of relevant documents found

**Error Responses**:
- `400`: No query provided or empty query
- `500`: Search operation failed, Azure OpenAI error, or Azure AI Search error

**Notes**:
- The refined query optimizes search results by adding medical terminology
- SAS URLs in document references expire after 1 hour for security
- If no documents are found, the API returns a message indicating no results

### 3. Health Check

**Endpoint**: `GET /health`

**Description**: Check if the API is running

**Example**:
```bash
curl http://localhost:5000/health
```

**Response** (200):
```json
{
  "status": "healthy",
  "service": "HealthDocumentTracker"
}
```

## Project Structure

```
HealthDocumentTracker/
├── Backend/
│   ├── app.py              # Main Flask application entry point
│   ├── config.py           # Shared configuration and utilities
│   ├── upload.py           # Document upload API endpoint
│   ├── search.py           # Document search API endpoint
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables (not in git)
│   └── .env.example       # Example environment configuration
├── .gitignore
└── README.md              # This file
```

### File Descriptions

- **app.py**: Main Flask application that registers blueprints and runs the server
- **config.py**: Shared configuration, environment variables, and utility functions for Azure Blob Storage
- **upload.py**: Blueprint containing the `/documents` POST endpoint for file uploads
- **search.py**: Blueprint containing the `/documents/search` POST endpoint for document search
- **requirements.txt**: Python package dependencies
- **.env.example**: Template for environment variables (copy to .env and configure)

## Security Considerations

- Never commit your `.env` file to version control
- Keep your Azure Storage connection string secure
- Use Azure's managed identities in production environments
- Consider implementing authentication/authorization for production use
- Validate and sanitize all user inputs
- Set appropriate CORS policies if needed

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage account connection string | Yes | - |
| `AZURE_STORAGE_CONTAINER_NAME_RAW` | Blob container name for raw documents | No | `health-documents-raw` |
| `AZURE_VISION_ENDPOINT` | Azure Computer Vision endpoint URL | Yes (for OCR) | - |
| `AZURE_VISION_KEY` | Azure Computer Vision API key | Yes (for OCR) | - |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search service endpoint | Yes | - |
| `AZURE_SEARCH_KEY` | Azure AI Search admin API key | Yes | - |
| `AZURE_SEARCH_INDEX_NAME` | Azure AI Search index name | No | `health-documents-index` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | Yes | - |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | Yes | - |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version | No | `2024-02-15-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Name of deployed GPT model | No | `gpt-4` |
| `PORT` | Port for Flask server | No | `5000` |
| `FLASK_DEBUG` | Enable debug mode | No | `False` |

## Development

To run in debug mode, set in your `.env` file:
```
FLASK_DEBUG=True
```

## Troubleshooting

**Issue**: "Azure Storage connection string not configured"
- **Solution**: Ensure `AZURE_STORAGE_CONNECTION_STRING` is set in your `.env` file

**Issue**: Container creation fails
- **Solution**: Check your Azure Storage account permissions and ensure the connection string is correct

**Issue**: File upload fails
- **Solution**: Verify the file size is within Azure Blob Storage limits and the file type is allowed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues or questions, please open an issue in the GitHub repository.
