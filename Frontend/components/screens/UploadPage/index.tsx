import React, { useState } from 'react';
import {
  View,
  ScrollView,
  TouchableOpacity,
  Alert,
  Image,
  StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ThemedView, ThemedText } from '@/components/ui';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from 'expo-image-picker';
import { styles } from './styles';

interface UploadPageProps {
  onSubmit: (files: { uri: string; name: string; type: string }[]) => void;
  onBack: () => void;
}

export function UploadPage({ onSubmit, onBack }: UploadPageProps) {
  const insets = useSafeAreaInsets();
  const [selectedFiles, setSelectedFiles] = useState<
    { uri: string; name: string; type: string }[]
  >([]);

  const pickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (!permissionResult.granted) {
      Alert.alert('Permission Required', 'Please grant camera roll permissions');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsMultipleSelection: true,
      quality: 1,
    });

    if (!result.canceled && result.assets) {
      const newFiles = result.assets.map((asset) => ({
        uri: asset.uri,
        name: asset.uri.split('/').pop() || 'image.jpg',
        type: 'image',
      }));
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*'],
        multiple: true,
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets) {
        const newFiles = result.assets.map((asset) => ({
          uri: asset.uri,
          name: asset.name,
          type: asset.mimeType?.startsWith('image/') ? 'image' : 'pdf',
        }));
        setSelectedFiles((prev) => [...prev, ...newFiles]);
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to pick document');
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    if (selectedFiles.length === 0) {
      Alert.alert('No Files', 'Please select at least one file to upload');
      return;
    }

    onSubmit(selectedFiles);
    setSelectedFiles([]);
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#007AFF" />
        </TouchableOpacity>
        <ThemedText type="title" style={styles.headerTitle}>
          Upload Documents
        </ThemedText>
        <View style={styles.placeholder} />
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
      >
        <ThemedView style={styles.uploadSection}>
          <ThemedText type="subtitle" style={styles.sectionTitle}>
            Select Files
          </ThemedText>
          
          <TouchableOpacity style={styles.uploadButton} onPress={pickImage}>
            <Ionicons name="images-outline" size={32} color="#007AFF" />
            <ThemedText style={styles.uploadButtonText}>
              Choose from Photos
            </ThemedText>
          </TouchableOpacity>

          <TouchableOpacity style={styles.uploadButton} onPress={pickDocument}>
            <Ionicons name="document-outline" size={32} color="#007AFF" />
            <ThemedText style={styles.uploadButtonText}>
              Choose Documents
            </ThemedText>
          </TouchableOpacity>
        </ThemedView>

        {selectedFiles.length > 0 && (
          <ThemedView style={styles.selectedSection}>
            <ThemedText type="subtitle" style={styles.sectionTitle}>
              Selected Files ({selectedFiles.length})
            </ThemedText>

            {selectedFiles.map((file, index) => (
              <View key={index} style={styles.fileCard}>
                <View style={styles.filePreview}>
                  {file.type === 'image' ? (
                    <Image source={{ uri: file.uri }} style={styles.thumbnail} />
                  ) : (
                    <View style={styles.pdfIcon}>
                      <Ionicons name="document-text" size={32} color="#666" />
                    </View>
                  )}
                </View>
                <View style={styles.fileInfo}>
                  <ThemedText style={styles.fileName} numberOfLines={2}>
                    {file.name}
                  </ThemedText>
                  <ThemedText style={styles.fileType}>
                    {file.type === 'image' ? 'Image' : 'PDF'}
                  </ThemedText>
                </View>
                <TouchableOpacity
                  onPress={() => removeFile(index)}
                  style={styles.removeButton}
                >
                  <Ionicons name="close-circle" size={24} color="#ff3b30" />
                </TouchableOpacity>
              </View>
            ))}
          </ThemedView>
        )}

        {selectedFiles.length > 0 && (
          <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
            <ThemedText style={styles.submitButtonText}>
              Upload {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
            </ThemedText>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
}
