import React from 'react';
import {
  View,
  FlatList,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import { ThemedView, ThemedText } from '@/components/ui';
import { Document } from '@/types';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';

interface DocumentStoreProps {
  documents: Document[];
  onDocumentClick: (doc: Document) => void;
  onDeleteDocument: (docId: string) => void;
}

export function DocumentStore({
  documents,
  onDocumentClick,
  onDeleteDocument,
}: DocumentStoreProps) {
  const handleDelete = (doc: Document) => {
    Alert.alert(
      'Delete Document',
      `Are you sure you want to delete "${doc.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => onDeleteDocument(doc.id),
        },
      ]
    );
  };

  const renderDocument = ({ item }: { item: Document }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => onDocumentClick(item)}
      activeOpacity={0.7}
    >
      <View style={styles.imageContainer}>
        {item.type === 'image' ? (
          <Image source={{ uri: item.thumbnail }} style={styles.thumbnail} />
        ) : (
          <View style={styles.pdfPlaceholder}>
            <Ionicons name="document-text" size={48} color="#666" />
          </View>
        )}
      </View>
      <View style={styles.cardContent}>
        <ThemedText style={styles.documentName} numberOfLines={2}>
          {item.name}
        </ThemedText>
        <ThemedText style={styles.documentDate}>
          {new Date(item.uploadedAt).toLocaleDateString()}
        </ThemedText>
      </View>
      <TouchableOpacity
        style={styles.deleteButton}
        onPress={() => handleDelete(item)}
      >
        <Ionicons name="trash-outline" size={20} color="#ff3b30" />
      </TouchableOpacity>
    </TouchableOpacity>
  );

  if (documents.length === 0) {
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
    <FlatList
      data={documents}
      renderItem={renderDocument}
      keyExtractor={(item) => item.id}
      numColumns={2}
      contentContainerStyle={styles.listContent}
      columnWrapperStyle={styles.row}
      style={styles.container}
      showsVerticalScrollIndicator={false}
    />
  );
}
