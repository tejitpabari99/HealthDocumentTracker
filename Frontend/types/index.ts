export interface Document {
  id: string;
  userId: string;
  documentId: string;
  reportId: string;
  originalFileName: string;
  displayName: string;
  contentType: string;
  fileSize: number;
  blobUri: string;
  sasUrl?: string;
  blobName: string;
  blobContainer: string;
  thumbnailUri?: string;
  searchDocumentIds: string[];
  totalPages: number;
  uploadedAt: string;
  status: string;
  type: string;
}

export interface DocumentListResponse {
  documents: Document[];
  count: number;
  userId: string;
}

export type SortField = 'originalFileName' | 'uploadedAt';
export type SortOrder = 'asc' | 'desc';

export interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
}

export type TabType = 'home' | 'documents';
export type PageType = 'main' | 'profile' | 'upload' | 'viewer';

export interface SearchResponse {
  message: string;
  sas_url: string | null;
  query: string;
  refined_query: string;
  searchId: string;
  searchDurationMs: number;
  documentId: string | null;
  searchActivityId: string | null;
}
