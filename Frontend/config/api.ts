/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

// Read API host from environment variable
// Falls back to localhost for development if not set
const API_HOST = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5000';

// Hardcoded user credentials for testing
export const TEST_USER = {
  id: 'user-194b85f1-faab-4c3b-8c19-d2e8ad8d5459',
  email: 'testuser@test.com',
};

/**
 * Get the current API host
 * You can modify this function to read from environment variables or async storage
 */
export const getApiHost = (): string => {
  return API_HOST;
};

/**
 * Update the API host (useful for switching between local and deployed)
 * You can call this from settings or configuration screen
 */
export const setApiHost = (host: string): void => {
  // In a real implementation, you might want to save this to AsyncStorage
  console.warn('To change API host, update the API_HOST constant in config/api.ts');
};

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  // Upload endpoint - POST /documents
  UPLOAD_DOCUMENT: `${API_HOST}/documents`,
  
  // List documents endpoint - GET /documents
  LIST_DOCUMENTS: `${API_HOST}/documents`,
  
  // Get document endpoint - GET /documents/:id
  GET_DOCUMENT: (id: string) => `${API_HOST}/documents/${id}`,
  
  // Delete document endpoint - DELETE /documents/:id
  DELETE_DOCUMENT: (id: string) => `${API_HOST}/documents/${id}`,
  
  // Search endpoint - POST /search
  SEARCH_DOCUMENTS: `${API_HOST}/search`,
  
  // Health check - GET /health
  HEALTH_CHECK: `${API_HOST}/health`,
};

/**
 * API Helper Functions
 */

/**
 * Get authentication headers with X-User-Id
 */
const getAuthHeaders = () => {
  return {
    'X-User-Id': TEST_USER.id,
  };
};

/**
 * Upload a single document to the backend
 * @param file - File object with uri, name, and type
 * @returns Promise with upload response
 */
export const uploadDocument = async (file: {
  uri: string;
  name: string;
  type: string;
}): Promise<any> => {
  try {
    // Determine the MIME type based on file extension
    let mimeType = 'application/octet-stream';
    const fileName = file.name.toLowerCase();
    
    if (fileName.endsWith('.pdf')) {
      mimeType = 'application/pdf';
    } else if (fileName.endsWith('.jpg') || fileName.endsWith('.jpeg')) {
      mimeType = 'image/jpeg';
    } else if (fileName.endsWith('.png')) {
      mimeType = 'image/png';
    } else if (file.type === 'image') {
      mimeType = 'image/jpeg'; // Default for generic images
    }
    
    // Ensure filename has proper extension
    let finalFileName = file.name;
    if (!finalFileName.includes('.')) {
      // No extension found - add one based on MIME type or file type
      if (mimeType === 'application/pdf') {
        finalFileName = `${finalFileName}.pdf`;
      } else if (mimeType === 'image/jpeg') {
        finalFileName = `${finalFileName}.jpg`;
      } else if (mimeType === 'image/png') {
        finalFileName = `${finalFileName}.png`;
      } else if (file.type === 'image') {
        finalFileName = `${finalFileName}.jpg`; // Default to jpg for images
      }
    }
    
    // Create FormData and handle platform-specific file preparation
    const formData = new FormData();
    
    // Check if running on web (blob: URL) or native (file:// or content://)
    if (file.uri.startsWith('blob:') || file.uri.startsWith('http')) {
      // Web platform - fetch the blob immediately and convert to File
      try {
        const blobResponse = await fetch(file.uri);
        if (!blobResponse.ok) {
          throw new Error(`Failed to fetch blob: ${blobResponse.statusText}`);
        }
        const blob = await blobResponse.blob();
        
        // Create a proper File object with the correct MIME type
        const webFile = new File([blob], finalFileName, { type: mimeType });
        formData.append('file', webFile);
        
        console.log('Web file prepared:', { name: finalFileName, type: mimeType, size: blob.size });
      } catch (blobError: any) {
        console.error('Failed to process blob URL:', blobError);
        throw new Error(`Failed to read file: ${blobError.message}. The file may have been moved or deleted.`);
      }
    } else {
      // React Native platform - use the standard format
      const fileToUpload: any = {
        uri: file.uri,
        name: finalFileName,
        type: mimeType,
      };
      formData.append('file', fileToUpload);
      console.log('Native file prepared:', { name: finalFileName, type: mimeType });
    }
    
    // Don't set Content-Type header - let the browser/fetch set it automatically with boundary
    const response = await fetch(API_ENDPOINTS.UPLOAD_DOCUMENT, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    
    let data;
    try {
      data = await response.json();
    } catch (parseError) {
      console.error('Failed to parse response:', parseError);
      throw new Error(`Upload failed with status ${response.status}. Unable to parse server response.`);
    }
    
    if (!response.ok) {
      console.error('Upload failed:', {
        status: response.status,
        statusText: response.statusText,
        error: data.error,
        message: data.message,
        details: data.details,
        fullResponse: data
      });
      throw new Error(data.error || data.message || `Upload failed with status ${response.status}`);
    }
    
    return data;
  } catch (error: any) {
    console.error('Upload error details:', {
      message: error.message,
      stack: error.stack,
      file: file
    });
    throw error;
  }
};

/**
 * List all documents for the authenticated user
 * @returns Promise with list of documents
 */
export const listDocuments = async (): Promise<any> => {
  try {
    const response = await fetch(API_ENDPOINTS.LIST_DOCUMENTS, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `Failed to list documents with status ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('List documents error:', error);
    throw error;
  }
};

/**
 * Get a single document by ID
 * @param documentId - The document ID
 * @returns Promise with document details
 */
export const getDocument = async (documentId: string): Promise<any> => {
  try {
    const response = await fetch(API_ENDPOINTS.GET_DOCUMENT(documentId), {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `Failed to get document with status ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('Get document error:', error);
    throw error;
  }
};

/**
 * Delete a document
 * @param documentId - The document ID to delete
 * @returns Promise with deletion result
 */
export const deleteDocument = async (documentId: string): Promise<any> => {
  try {
    const response = await fetch(API_ENDPOINTS.DELETE_DOCUMENT(documentId), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `Failed to delete document with status ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('Delete document error:', error);
    throw error;
  }
};


/**
 * Search documents with a query
 * @param query - Search query string
 * @returns Promise with search response
 */
export const searchDocuments = async (query: string): Promise<any> => {
  try {
    const response = await fetch(API_ENDPOINTS.SEARCH_DOCUMENTS, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ query }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || `Search failed with status ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
};

/**
 * Check backend health status
 * @returns Promise with health status
 */
export const checkHealth = async (): Promise<any> => {
  try {
    const response = await fetch(API_ENDPOINTS.HEALTH_CHECK, {
      method: 'GET',
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};
