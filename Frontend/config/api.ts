/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

// Default to localhost for development
// Change this to your deployed backend URL when ready
const API_HOST = 'http://localhost:5000';

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
  
  // Search endpoint - POST /documents/search
  SEARCH_DOCUMENTS: `${API_HOST}/documents/search`,
  
  // Health check - GET /health
  HEALTH_CHECK: `${API_HOST}/health`,
};

/**
 * API Helper Functions
 */

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
    const formData = new FormData();
    
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
    
    // Check if running on web (blob: URL) or native (file:// or content://)
    if (file.uri.startsWith('blob:') || file.uri.startsWith('http')) {
      // Web platform - fetch the blob and convert to File
      const response = await fetch(file.uri);
      const blob = await response.blob();
      const webFile = new File([blob], finalFileName, { type: mimeType });
      formData.append('file', webFile);
    } else {
      // React Native platform - use the standard format
      const fileToUpload: any = {
        uri: file.uri,
        name: finalFileName,
        type: mimeType,
      };
      formData.append('file', fileToUpload);
    }
    
    // Don't set Content-Type header - let the browser/fetch set it automatically with boundary
    const response = await fetch(API_ENDPOINTS.UPLOAD_DOCUMENT, {
      method: 'POST',
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
