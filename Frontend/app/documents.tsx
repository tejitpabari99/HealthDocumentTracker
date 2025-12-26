import React, { useState } from 'react';
import { View, StatusBar, TouchableOpacity, Animated } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { DocumentStore, DocumentViewer } from '@/components/screens';
import { Header, BottomNav, Disclaimer } from '@/components/navigation';
import { ThemedText } from '@/components/ui';
import { Document, UserProfile } from '@/types';
import { TEST_USER } from '@/config/api';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './(tabs)/styles';

export default function DocumentsPage() {
  const insets = useSafeAreaInsets();
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [userProfile] = useState<UserProfile>({
    firstName: 'Test',
    lastName: 'User',
    email: TEST_USER.email,
  });

  const handleProfileClick = () => {
    router.push('/profile');
  };

  const handleUploadClick = () => {
    router.push('/upload');
  };

  const handleTabChange = (tab: 'home' | 'documents') => {
    if (tab === 'home') {
      router.push('/search');
    } else {
      router.push('/documents');
    }
  };

  const handleDocumentClick = (doc: Document) => {
    setSelectedDocument(doc);
  };

  const handleDeleteDocument = (documentName: string) => {
    setSelectedDocument(null);
    setSuccessMessage(`Document "${documentName}" has been successfully deleted.`);
    // Auto-hide success message after 4 seconds
    setTimeout(() => {
      setSuccessMessage(null);
    }, 4000);
  };

  const handleCloseViewer = () => {
    setSelectedDocument(null);
  };

  if (selectedDocument) {
    return (
      <DocumentViewer
        document={selectedDocument}
        onClose={handleCloseViewer}
        onDelete={handleDeleteDocument}
      />
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <Header userProfile={userProfile} onProfileClick={handleProfileClick} />
      </View>

      <View style={[styles.content, { paddingBottom: 80 }]}>
        <DocumentStore
          onDocumentClick={handleDocumentClick}
          onDeleteDocument={handleDeleteDocument}
        />
        
        {/* Success Message */}
        {successMessage && (
          <View style={styles.successMessage}>
            <Ionicons name="checkmark-circle" size={20} color="#fff" />
            <ThemedText style={styles.successMessageText}>{successMessage}</ThemedText>
            <TouchableOpacity onPress={() => setSuccessMessage(null)} style={styles.successCloseButton}>
              <Ionicons name="close" size={20} color="#fff" />
            </TouchableOpacity>
          </View>
        )}
      </View>

      <BottomNav
        activeTab="documents"
        onTabChange={handleTabChange}
        onUploadClick={handleUploadClick}
      />

      {showDisclaimer && <Disclaimer />}
    </View>
  );
}
