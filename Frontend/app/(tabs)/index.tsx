import React, { useState, useEffect } from 'react';
import { View, StatusBar, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Home, DocumentStore, Profile, UploadPage, DocumentViewer } from '@/components/screens';
import { Header, BottomNav, Disclaimer } from '@/components/navigation';
import { Document, UserProfile, TabType, PageType } from '@/types';
import { ThemedView, ThemedText } from '@/components/ui';
import { TEST_USER } from '@/config/api';
import { styles } from './styles';

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState<TabType>('home');
  const [currentPage, setCurrentPage] = useState<PageType>('main');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(true);
  const [userProfile, setUserProfile] = useState<UserProfile>({
    firstName: 'Test',
    lastName: 'User',
    email: TEST_USER.email,
  });

  // Simulate authentication check on mount
  useEffect(() => {
    // Simulate checking for authentication
    const checkAuth = async () => {
      // For now, just show loading screen for 500ms
      await new Promise(resolve => setTimeout(resolve, 500));
      setIsAuthenticating(false);
    };
    
    checkAuth();
  }, []);

  const handleTestUserLogin = () => {
    setIsAuthenticated(true);
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

  const handleDeleteDocument = async (docId: string) => {
    if (selectedDocument?.id === docId) {
      setCurrentPage('main');
      setSelectedDocument(null);
      setActiveTab('documents');
    }
  };

  const handleUploadSubmit = () => {
    // Navigate back to documents list
    setCurrentPage('main');
    setActiveTab('documents');
    
    // Show success message
    setShowDisclaimer(true);
    setTimeout(() => {
      setShowDisclaimer(false);
    }, 3000);
  };

  const handleBackToMain = () => {
    setCurrentPage('main');
    setSelectedDocument(null);
  };

  const handleUpdateProfile = (profile: UserProfile) => {
    setUserProfile(profile);
  };

  // Loading screen while checking authentication
  if (isAuthenticating) {
    return (
      <View style={[styles.loadingContainer, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" />
        <ActivityIndicator size="large" color="#007AFF" />
        <ThemedText style={styles.loadingText}>Loading...</ThemedText>
      </View>
    );
  }

  // Authentication screen with test user button
  if (!isAuthenticated) {
    return (
      <View style={[styles.authContainer, { paddingTop: insets.top }]}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.authContent}>
          <ThemedText type="title" style={styles.authTitle}>
            Health Document Tracker
          </ThemedText>
          <ThemedText style={styles.authSubtitle}>
            Securely store and search your health documents
          </ThemedText>
          
          <View style={styles.authCard}>
            <ThemedText style={styles.authCardTitle}>Test Mode</ThemedText>
            <ThemedText style={styles.authCardText}>
              For testing purposes, you can log in as a test user:
            </ThemedText>
            <View style={styles.userInfoBox}>
              <ThemedText style={styles.userInfoLabel}>User ID:</ThemedText>
              <ThemedText style={styles.userInfoValue}>{TEST_USER.id}</ThemedText>
              <ThemedText style={styles.userInfoLabel}>Email:</ThemedText>
              <ThemedText style={styles.userInfoValue}>{TEST_USER.email}</ThemedText>
            </View>
            <TouchableOpacity
              style={styles.loginButton}
              onPress={handleTestUserLogin}
            >
              <ThemedText style={styles.loginButtonText}>
                Continue as Test User
              </ThemedText>
            </TouchableOpacity>
          </View>

          <ThemedText style={styles.authNote}>
            Note: In production, this will be replaced with proper authentication
          </ThemedText>
        </View>
      </View>
    );
  }

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
