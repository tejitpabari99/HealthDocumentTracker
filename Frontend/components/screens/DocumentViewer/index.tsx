import React from 'react';
import {
  View,
  TouchableOpacity,
  Alert,
  ScrollView,
  Image,
  StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ThemedView, ThemedText } from '@/components/ui';
import { Document } from '@/types';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';

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
  const handleDelete = () => {
    Alert.alert(
      'Delete Document',
      `Are you sure you want to delete "${document.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            onDelete(document.id);
            onClose();
          },
        },
      ]
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#007AFF" />
        </TouchableOpacity>
        <View style={styles.headerTitle}>
          <ThemedText style={styles.headerTitleText} numberOfLines={1}>
            {document.name}
          </ThemedText>
        </View>
        <TouchableOpacity onPress={handleDelete} style={styles.deleteButton}>
          <Ionicons name="trash-outline" size={24} color="#ff3b30" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
      >
        <View style={styles.documentContainer}>
          {document.type === 'image' ? (
            <Image
              source={{ uri: document.uri }}
              style={styles.documentImage}
              resizeMode="contain"
            />
          ) : (
            <View style={styles.pdfContainer}>
              <Ionicons name="document-text" size={80} color="#666" />
              <ThemedText style={styles.pdfText}>
                PDF documents cannot be displayed in this view
              </ThemedText>
              <ThemedText style={styles.pdfSubtext}>
                The document is stored and can be shared or exported
              </ThemedText>
            </View>
          )}
        </View>

        <ThemedView style={styles.infoCard}>
          <View style={styles.infoRow}>
            <ThemedText style={styles.infoLabel}>Name:</ThemedText>
            <ThemedText style={styles.infoValue}>{document.name}</ThemedText>
          </View>
          <View style={styles.infoRow}>
            <ThemedText style={styles.infoLabel}>Type:</ThemedText>
            <ThemedText style={styles.infoValue}>
              {document.type === 'image' ? 'Image' : 'PDF'}
            </ThemedText>
          </View>
          <View style={styles.infoRow}>
            <ThemedText style={styles.infoLabel}>Uploaded:</ThemedText>
            <ThemedText style={styles.infoValue}>
              {new Date(document.uploadedAt).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </ThemedText>
          </View>
        </ThemedView>
      </ScrollView>
    </View>
  );
}
