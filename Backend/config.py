"""
Configuration file for shared settings and utilities
"""
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Azure Blob Storage configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'health-documents')
AZURE_STORAGE_CONTAINER_NAME_RAW = os.getenv('AZURE_STORAGE_CONTAINER_NAME_RAW', 'health-documents-raw')

# Azure AI Search configuration
AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT')
AZURE_SEARCH_KEY = os.getenv('AZURE_SEARCH_KEY')
AZURE_SEARCH_INDEX_NAME = os.getenv('AZURE_SEARCH_INDEX_NAME', 'health-documents-index')

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

# Azure Cosmos DB configuration
COSMOS_DB_ENDPOINT = os.getenv('COSMOS_DB_ENDPOINT')
COSMOS_DB_KEY = os.getenv('COSMOS_DB_KEY')
COSMOS_DB_DATABASE_NAME = os.getenv('COSMOS_DB_DATABASE_NAME', 'HealthDocumentTrackerDB')
COSMOS_DB_USERS_CONTAINER = os.getenv('COSMOS_DB_USERS_CONTAINER', 'Users')
COSMOS_DB_DOCUMENTS_CONTAINER = os.getenv('COSMOS_DB_DOCUMENTS_CONTAINER', 'Documents')
COSMOS_DB_SEARCH_ACTIVITY_CONTAINER = os.getenv('COSMOS_DB_SEARCH_ACTIVITY_CONTAINER', 'SearchActivity')

# Allowed file extensions (optional - customize as needed)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_blob_service_client():
    """Initialize and return Azure Blob Service Client"""
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise ValueError("Azure Storage connection string not configured")
    return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def get_search_client() -> SearchClient:
    """Initialize and return Azure AI Search Client"""
    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_KEY:
        raise ValueError("Azure AI Search endpoint or key not configured")
    
    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_KEY)
    )

def get_openai_client():
    """Initialize and return Azure OpenAI Client"""
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
        raise ValueError("Azure OpenAI endpoint or key not configured")
    
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )

def get_cosmos_client():
    """Initialize and return Azure Cosmos DB Client"""
    from azure.cosmos import CosmosClient
    
    if not COSMOS_DB_ENDPOINT or not COSMOS_DB_KEY:
        raise ValueError("Azure Cosmos DB endpoint or key not configured")
    
    return CosmosClient(COSMOS_DB_ENDPOINT, COSMOS_DB_KEY)

def get_cosmos_database():
    """Get Cosmos DB database instance"""
    client = get_cosmos_client()
    return client.get_database_client(COSMOS_DB_DATABASE_NAME)

def get_users_container():
    """Get Users container instance"""
    database = get_cosmos_database()
    return database.get_container_client(COSMOS_DB_USERS_CONTAINER)

def get_documents_container():
    """Get Documents container instance"""
    database = get_cosmos_database()
    return database.get_container_client(COSMOS_DB_DOCUMENTS_CONTAINER)

def get_search_activity_container():
    """Get SearchActivity container instance"""
    database = get_cosmos_database()
    return database.get_container_client(COSMOS_DB_SEARCH_ACTIVITY_CONTAINER)