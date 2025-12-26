import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { Document } from '@/types';
import { listDocuments as apiListDocuments } from '@/config/api';

interface DocumentCache {
  documents: Document[];
  lastFetched: number | null;
  isLoading: boolean;
}

interface DocumentCacheContextType {
  documents: Document[];
  isLoading: boolean;
  getDocuments: (forceRefresh?: boolean) => Promise<void>;
  addDocument: (document: Document) => void;
  removeDocument: (documentId: string) => void;
  refreshDocuments: () => Promise<void>;
  invalidateCache: () => void;
}

const DocumentCacheContext = createContext<DocumentCacheContextType | undefined>(undefined);

// Cache TTL in milliseconds (2 minutes)
const CACHE_TTL = 2 * 60 * 1000;

export function DocumentCacheProvider({ children }: { children: React.ReactNode }) {
  const [cache, setCache] = useState<DocumentCache>({
    documents: [],
    lastFetched: null,
    isLoading: false,
  });

  // Use ref to track if a background fetch is in progress
  const fetchingRef = useRef(false);

  /**
   * Check if cache is stale
   */
  const isCacheStale = useCallback(() => {
    if (cache.lastFetched === null) return true;
    const now = Date.now();
    return now - cache.lastFetched > CACHE_TTL;
  }, [cache.lastFetched]);

  /**
   * Fetch documents from API and update cache
   */
  const fetchDocuments = useCallback(async (showLoading = true) => {
    // Prevent multiple simultaneous fetches
    if (fetchingRef.current) return;
    
    fetchingRef.current = true;
    
    if (showLoading) {
      setCache(prev => ({ ...prev, isLoading: true }));
    }

    try {
      const response = await apiListDocuments();
      const documents = response.documents || [];
      
      setCache({
        documents,
        lastFetched: Date.now(),
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setCache(prev => ({ ...prev, isLoading: false }));
      throw error;
    } finally {
      fetchingRef.current = false;
    }
  }, []);

  /**
   * Get documents with stale-while-revalidate strategy
   * Shows cached data immediately, fetches fresh data in background if stale
   */
  const getDocuments = useCallback(async (forceRefresh = false) => {
    // If cache is empty or force refresh requested, fetch with loading state
    if (cache.documents.length === 0 || forceRefresh) {
      await fetchDocuments(true);
      return;
    }

    // If cache is stale, fetch in background without loading state
    if (isCacheStale()) {
      // Don't await - fetch in background
      fetchDocuments(false).catch(err => {
        console.error('Background refresh failed:', err);
      });
    }
  }, [cache.documents.length, isCacheStale, fetchDocuments]);

  /**
   * Add a document to cache (after successful upload)
   */
  const addDocument = useCallback((document: Document) => {
    setCache(prev => ({
      ...prev,
      documents: [document, ...prev.documents], // Add to beginning (newest first)
    }));
  }, []);

  /**
   * Remove a document from cache (after successful delete)
   */
  const removeDocument = useCallback((documentId: string) => {
    setCache(prev => ({
      ...prev,
      documents: prev.documents.filter(doc => doc.id !== documentId),
    }));
  }, []);

  /**
   * Force refresh documents (for pull-to-refresh)
   */
  const refreshDocuments = useCallback(async () => {
    await fetchDocuments(false); // Don't show loading spinner on refresh
  }, [fetchDocuments]);

  /**
   * Invalidate cache (clear all cached data)
   */
  const invalidateCache = useCallback(() => {
    setCache({
      documents: [],
      lastFetched: null,
      isLoading: false,
    });
  }, []);

  const value: DocumentCacheContextType = {
    documents: cache.documents,
    isLoading: cache.isLoading,
    getDocuments,
    addDocument,
    removeDocument,
    refreshDocuments,
    invalidateCache,
  };

  return (
    <DocumentCacheContext.Provider value={value}>
      {children}
    </DocumentCacheContext.Provider>
  );
}

/**
 * Hook to use document cache
 */
export function useDocumentCache() {
  const context = useContext(DocumentCacheContext);
  if (context === undefined) {
    throw new Error('useDocumentCache must be used within a DocumentCacheProvider');
  }
  return context;
}
