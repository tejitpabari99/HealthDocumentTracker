import React, { useState, useEffect } from 'react';
import {
  View,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Modal,
} from 'react-native';
import { ThemedView, ThemedText } from '@/components/ui';
import { Document, SortField, SortOrder } from '@/types';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';
import { useDocumentCache } from '@/context/DocumentCacheContext';

interface DocumentStoreProps {
  onDocumentClick: (doc: Document) => void;
  onDeleteDocument: (docId: string) => void;
}

type SortOption = 'name-asc' | 'name-desc' | 'upload-new' | 'upload-old';

export function DocumentStore({
  onDocumentClick,
  onDeleteDocument,
}: DocumentStoreProps) {
  const { documents: cachedDocuments, isLoading, getDocuments, refreshDocuments } = useDocumentCache();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [sortOption, setSortOption] = useState<SortOption>('upload-new');
  const [showSortDropdown, setShowSortDropdown] = useState(false);

  // Sorted documents based on current sort option
  const sortedDocuments = React.useMemo(() => {
    const sorted = [...cachedDocuments].sort((a, b) => {
      switch (sortOption) {
        case 'name-asc':
          return a.displayName.localeCompare(b.displayName);
        case 'name-desc':
          return b.displayName.localeCompare(a.displayName);
        case 'upload-new':
          return new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime();
        case 'upload-old':
          return new Date(a.uploadedAt).getTime() - new Date(b.uploadedAt).getTime();
        default:
          return 0;
      }
    });
    return sorted;
  }, [cachedDocuments, sortOption]);

  // Load documents on mount
  useEffect(() => {
    getDocuments().catch((error: any) => {
      console.error('Failed to fetch documents:', error);
      Alert.alert(
        'Error',
        error.message || 'Failed to load documents. Please try again.'
      );
    });
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshDocuments();
    } catch (error: any) {
      console.error('Failed to refresh documents:', error);
      Alert.alert(
        'Error',
        error.message || 'Failed to refresh documents. Please try again.'
      );
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSortOptionSelect = (option: SortOption) => {
    setSortOption(option);
    setShowSortDropdown(false);
  };

  const getSortLabel = (option: SortOption): string => {
    switch (option) {
      case 'name-asc':
        return 'Name: A-Z';
      case 'name-desc':
        return 'Name: Z-A';
      case 'upload-new':
        return 'Newest First';
      case 'upload-old':
        return 'Oldest First';
      default:
        return 'Sort';
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
  };

  const sortOptions: SortOption[] = ['name-asc', 'name-desc', 'upload-new', 'upload-old'];

  const renderDocument = ({ item }: { item: Document }) => {
    return (
      <TouchableOpacity
        style={styles.listItem}
        onPress={() => onDocumentClick(item)}
        activeOpacity={0.7}
      >
        <View style={styles.listItemContent}>
          <View style={styles.listItemLeft}>
            <Ionicons 
              name={item.contentType.startsWith('image/') ? 'image-outline' : 'document-text-outline'} 
              size={24} 
              color="#007AFF" 
              style={styles.listItemIcon}
            />
            <ThemedText style={styles.listItemText} numberOfLines={2}>
              {item.displayName}
            </ThemedText>
          </View>
          <ThemedText style={styles.dateText}>
            {formatDate(item.uploadedAt)}
          </ThemedText>
        </View>
      </TouchableOpacity>
    );
  };

  if (isLoading && cachedDocuments.length === 0) {
    return (
      <ThemedView style={styles.emptyContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <ThemedText style={styles.emptyText}>Loading documents...</ThemedText>
      </ThemedView>
    );
  }

  if (sortedDocuments.length === 0) {
    return (
      <ThemedView style={styles.emptyContainer}>
        <Ionicons name="folder-open-outline" size={80} color="#ccc" />
        <ThemedText style={styles.emptyTitle}>No Documents Yet</ThemedText>
        <ThemedText style={styles.emptyText}>
          Tap the '+' button to upload your first document
        </ThemedText>
      </ThemedView>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerBar}>
        <ThemedText style={styles.headerTitle}>My Documents</ThemedText>
        <TouchableOpacity
          style={styles.sortButton}
          onPress={() => setShowSortDropdown(true)}
        >
          <Ionicons name="funnel-outline" size={16} color="#007AFF" />
          <ThemedText style={styles.sortButtonText}>{getSortLabel(sortOption)}</ThemedText>
          <Ionicons name="chevron-down" size={16} color="#007AFF" />
        </TouchableOpacity>
      </View>

      <FlatList
        data={sortedDocuments}
        renderItem={renderDocument}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} />
        }
      />

      <Modal
        visible={showSortDropdown}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowSortDropdown(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowSortDropdown(false)}
        >
          <View style={styles.dropdownContainer}>
            <View style={styles.dropdownHeader}>
              <ThemedText style={styles.dropdownTitle}>Sort By</ThemedText>
              <TouchableOpacity onPress={() => setShowSortDropdown(false)}>
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>
            {sortOptions.map((option) => (
              <TouchableOpacity
                key={option}
                style={[
                  styles.dropdownItem,
                  sortOption === option && styles.dropdownItemActive
                ]}
                onPress={() => handleSortOptionSelect(option)}
              >
                <ThemedText 
                  style={[
                    styles.dropdownItemText,
                    sortOption === option && styles.dropdownItemTextActive
                  ]}
                >
                  {getSortLabel(option)}
                </ThemedText>
                {sortOption === option && (
                  <Ionicons name="checkmark" size={20} color="#007AFF" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}
