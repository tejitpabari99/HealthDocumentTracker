import React, { useState } from 'react';
import {
  View,
  TouchableOpacity,
  Alert,
  Image,
  StatusBar,
  ActivityIndicator,
  Linking,
  Dimensions,
  Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ThemedText } from '@/components/ui';
import { Document } from '@/types';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';
import { deleteDocument as deleteDocumentApi } from '@/config/api';
import { useDocumentCache } from '@/context/DocumentCacheContext';

interface DocumentViewerProps {
  document: Document;
  onClose: () => void;
  onDelete: (docId: string) => void;
}

export function DocumentViewer({
  document,
  onClose,
  onDelete,
}: DocumentViewerProps) {
  const insets = useSafeAreaInsets();
  const { removeDocument } = useDocumentCache();
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  const handleDeleteConfirm = async () => {
    const documentName = document.displayName;
    setShowDeleteConfirm(false);
    setIsDeleting(true);
    try {
      await deleteDocumentApi(document.id);
      // Remove from cache immediately after successful API call
      removeDocument(document.id);
      // Close viewer first
      onClose();
      // Then notify parent with document name for success message
      onDelete(documentName);
    } catch (error: any) {
      Alert.alert(
        'Delete Failed',
        error.message || 'Failed to delete document. Please try again.'
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const getDocumentType = (contentType: string): 'image' | 'pdf' => {
    if (contentType.startsWith('image/')) {
      return 'image';
    }
    return 'pdf';
  };

  const docType = getDocumentType(document.contentType);
  const documentUrl = document.sasUrl || document.blobUri;

  const handleOpenDocument = () => {
    Linking.openURL(documentUrl).catch((err) => {
      console.error('Failed to open document:', err);
      Alert.alert('Error', 'Failed to open document in browser');
    });
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#007AFF" />
        </TouchableOpacity>
        <View style={styles.headerTitle}>
          <ThemedText style={styles.headerTitleText} numberOfLines={1}>
            {document.displayName}
          </ThemedText>
        </View>
        <TouchableOpacity
          onPress={handleDeleteClick}
          style={styles.deleteButton}
          disabled={isDeleting}
        >
          {isDeleting ? (
            <ActivityIndicator size="small" color="#ff3b30" />
          ) : (
            <Ionicons name="trash-outline" size={24} color="#ff3b30" />
          )}
        </TouchableOpacity>
      </View>

      {/* Delete Confirmation Modal */}
      <Modal
        visible={showDeleteConfirm}
        transparent={true}
        animationType="fade"
        onRequestClose={handleDeleteCancel}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.confirmDialog}>
            <ThemedText style={styles.confirmTitle}>Delete Document</ThemedText>
            <ThemedText style={styles.confirmMessage}>
              Are you sure you want to delete "{document.displayName}"? This action cannot be undone.
            </ThemedText>
            <View style={styles.confirmButtons}>
              <TouchableOpacity
                style={[styles.confirmButton, styles.cancelButton]}
                onPress={handleDeleteCancel}
              >
                <ThemedText style={styles.cancelButtonText}>Cancel</ThemedText>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.confirmButton, styles.deleteConfirmButton]}
                onPress={handleDeleteConfirm}
              >
                <ThemedText style={styles.deleteButtonText}>Delete</ThemedText>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Document Content - Full Page */}
      <View style={styles.documentContainer}>
        {docType === 'image' ? (
          <Image
            source={{ uri: documentUrl }}
            style={styles.documentImage}
            resizeMode="contain"
          />
        ) : (
          <View style={styles.pdfContainer}>
            <Ionicons name="document-text" size={80} color="#666" />
            <ThemedText style={styles.pdfText}>PDF Document</ThemedText>
            <ThemedText style={styles.pdfSubtext}>
              {document.totalPages} page{document.totalPages !== 1 ? 's' : ''}
            </ThemedText>
            <TouchableOpacity
              style={styles.openButton}
              onPress={handleOpenDocument}
            >
              <Ionicons name="open-outline" size={20} color="#fff" />
              <ThemedText style={styles.openButtonText}>
                Open in Browser
              </ThemedText>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </View>
  );
}
