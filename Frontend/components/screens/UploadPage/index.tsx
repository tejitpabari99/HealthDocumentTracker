import React, { useState } from 'react';
import {
  View,
  ScrollView,
  TouchableOpacity,
  Alert,
  Image,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ThemedView, ThemedText } from '@/components/ui';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from 'expo-image-picker';
import { styles } from './styles';
import { uploadDocument } from '@/config/api';
import { useDocumentCache } from '@/context/DocumentCacheContext';

interface UploadPageProps {
  onSubmit: (files: { uri: string; name: string; type: string }[]) => void;
  onBack: () => void;
}

export function UploadPage({ onSubmit, onBack }: UploadPageProps) {
  const insets = useSafeAreaInsets();
  const { addDocument } = useDocumentCache();
  const [selectedFiles, setSelectedFiles] = useState<
    { uri: string; name: string; type: string }[]
  >([]);
  const [isUploading, setIsUploading] = useState(false);

  const pickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (!permissionResult.granted) {
      Alert.alert('Permission Required', 'Please grant camera roll permissions');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsMultipleSelection: true, // Allow multiple files
      quality: 1,
    });

    if (!result.canceled && result.assets) {
      const newFiles = result.assets.map((asset) => ({
        uri: asset.uri,
        name: asset.uri.split('/').pop() || 'image.jpg',
        type: 'image',
      }));
      setSelectedFiles((prev) => [...prev, ...newFiles]); // Append to existing files
    }
  };

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*'],
        multiple: true, // Allow multiple files
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets) {
        const newFiles = result.assets.map((asset) => ({
          uri: asset.uri,
          name: asset.name,
          type: asset.mimeType?.startsWith('image/') ? 'image' : 'pdf',
        }));
        setSelectedFiles((prev) => [...prev, ...newFiles]); // Append to existing files
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to pick document');
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (selectedFiles.length === 0) {
      Alert.alert('No Files', 'Please select at least one file to upload');
      return;
    }

    setIsUploading(true);
    
    const totalFiles = selectedFiles.length;
    let successCount = 0;
    let failCount = 0;
    const errors: string[] = [];

    try {
      // Upload files one at a time
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        
        try {
          const response = await uploadDocument(file);
          // Add uploaded document to cache immediately
          if (response.document) {
            addDocument(response.document);
          }
          successCount++;
          console.log(`Uploaded ${i + 1}/${totalFiles}: ${response.original_filename}`);
        } catch (error: any) {
          failCount++;
          errors.push(`${file.name}: ${error.message || 'Upload failed'}`);
          console.error(`Failed to upload ${file.name}:`, error);
        }
      }

      // Navigate back immediately after successful uploads
      if (successCount === totalFiles) {
        setSelectedFiles([]);
        onSubmit(selectedFiles);
        onBack(); // Navigate back to documents screen immediately
        
        // Show success message after navigation
        setTimeout(() => {
          Alert.alert(
            'Upload Complete',
            `Successfully uploaded all ${successCount} file${successCount !== 1 ? 's' : ''}!`
          );
        }, 100);
      } else if (successCount > 0) {
        setSelectedFiles([]);
        onSubmit(selectedFiles);
        onBack(); // Navigate back to documents screen immediately
        
        // Show partial success message after navigation
        setTimeout(() => {
          Alert.alert(
            'Upload Partially Complete',
            `Uploaded: ${successCount}/${totalFiles} files\n\nFailed uploads:\n${errors.join('\n')}`
          );
        }, 100);
      } else {
        Alert.alert(
          'Upload Failed',
          `All uploads failed:\n${errors.join('\n')}`
        );
      }
    } catch (error: any) {
      console.error('Upload process failed:', error);
      Alert.alert(
        'Upload Failed',
        error.message || 'Failed to upload documents. Please check your connection and try again.'
      );
    } finally {
      setIsUploading(false);
    }
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
          <ThemedText style={styles.helperText}>
            You can select multiple files. Each will be uploaded separately.
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
          <TouchableOpacity 
            style={[styles.submitButton, isUploading && styles.submitButtonDisabled]} 
            onPress={handleSubmit}
            disabled={isUploading}
          >
            {isUploading ? (
              <View style={styles.uploadingContainer}>
                <ActivityIndicator color="#ffffff" size="small" />
                <ThemedText style={[styles.submitButtonText, { marginLeft: 8 }]}>
                  Uploading {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}...
                </ThemedText>
              </View>
            ) : (
              <ThemedText style={styles.submitButtonText}>
                Upload {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
              </ThemedText>
            )}
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
}
