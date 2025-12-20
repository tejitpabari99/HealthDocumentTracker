import React, { useState, useEffect } from 'react';
import { StyleSheet, View, StatusBar } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Home, DocumentStore, Profile, UploadPage, DocumentViewer } from '@/components/screens';
import { Header, BottomNav, Disclaimer } from '@/components/navigation';
import { Document, UserProfile, TabType, PageType } from '@/types';

const STORAGE_KEYS = {
  DOCUMENTS: '@health_docs_documents',
  PROFILE: '@health_docs_profile',
};

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState<TabType>('home');
  const [currentPage, setCurrentPage] = useState<PageType>('main');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile>({
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@example.com',
  });

  // Load data from storage on mount
  useEffect(() => {
    loadStoredData();
  }, []);

  // Save documents whenever they change
  useEffect(() => {
    saveDocuments();
  }, [documents]);

  // Save profile whenever it changes
  useEffect(() => {
    saveProfile();
  }, [userProfile]);

  const loadStoredData = async () => {
    try {
      const storedDocs = await AsyncStorage.getItem(STORAGE_KEYS.DOCUMENTS);
      const storedProfile = await AsyncStorage.getItem(STORAGE_KEYS.PROFILE);

      if (storedDocs) {
        const parsedDocs = JSON.parse(storedDocs);
        // Convert date strings back to Date objects
        const docsWithDates = parsedDocs.map((doc: any) => ({
          ...doc,
          uploadedAt: new Date(doc.uploadedAt),
        }));
        setDocuments(docsWithDates);
      }

      if (storedProfile) {
        setUserProfile(JSON.parse(storedProfile));
      }
    } catch (error) {
      console.error('Error loading stored data:', error);
    }
  };

  const saveDocuments = async () => {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEYS.DOCUMENTS,
        JSON.stringify(documents)
      );
    } catch (error) {
      console.error('Error saving documents:', error);
    }
  };

  const saveProfile = async () => {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEYS.PROFILE,
        JSON.stringify(userProfile)
      );
    } catch (error) {
      console.error('Error saving profile:', error);
    }
  };

  const handleProfileClick = () => {
    setCurrentPage('profile');
  };

  const handleUploadClick = () => {
    setCurrentPage('upload');
  };

  const handleDocumentClick = (doc: Document) => {
    setSelectedDocument(doc);
    setCurrentPage('viewer');
  };

  const handleDeleteDocument = (docId: string) => {
    setDocuments((prev) => prev.filter((doc) => doc.id !== docId));
    if (selectedDocument?.id === docId) {
      setCurrentPage('main');
      setSelectedDocument(null);
    }
  };

  const handleUploadSubmit = (
    files: { uri: string; name: string; type: string }[]
  ) => {
    const newDocs: Document[] = files.map((file, index) => ({
      id: `doc-${Date.now()}-${index}`,
      name: file.name,
      type: file.type === 'image' ? 'image' : 'pdf',
      uri: file.uri,
      thumbnail: file.uri,
      uploadedAt: new Date(),
    }));

    setDocuments((prev) => [...prev, ...newDocs]);
    setCurrentPage('main');
    setActiveTab('home');
    setShowDisclaimer(true);

    setTimeout(() => {
      setShowDisclaimer(false);
    }, 5000);
  };

  const handleBackToMain = () => {
    setCurrentPage('main');
    setSelectedDocument(null);
  };

  const handleUpdateProfile = (profile: UserProfile) => {
    setUserProfile(profile);
  };

  // Render different pages based on currentPage state
  if (currentPage === 'profile') {
    return (
      <Profile
        profile={userProfile}
        onUpdateProfile={handleUpdateProfile}
        onBack={handleBackToMain}
      />
    );
  }

  if (currentPage === 'upload') {
    return (
      <UploadPage onSubmit={handleUploadSubmit} onBack={handleBackToMain} />
    );
  }

  if (currentPage === 'viewer' && selectedDocument) {
    return (
      <DocumentViewer
        document={selectedDocument}
        onClose={handleBackToMain}
        onDelete={handleDeleteDocument}
      />
    );
  }

  // Main screen with tabs
  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <Header userProfile={userProfile} onProfileClick={handleProfileClick} />
      </View>

      <View style={[styles.content, { paddingBottom: 80 }]}>
        {activeTab === 'home' ? (
          <Home />
        ) : (
          <DocumentStore
            documents={documents}
            onDocumentClick={handleDocumentClick}
            onDeleteDocument={handleDeleteDocument}
          />
        )}
      </View>

      <BottomNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onUploadClick={handleUploadClick}
      />

      {showDisclaimer && <Disclaimer />}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    backgroundColor: '#ffffff',
  },
  content: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
});
