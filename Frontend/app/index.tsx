import React, { useState, useEffect } from 'react';
import { View, StatusBar, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { ThemedView, ThemedText } from '@/components/ui';
import { TEST_USER } from '@/config/api';
import { styles } from './(tabs)/styles';

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(true);

  // Simulate authentication check on mount
  useEffect(() => {
    const checkAuth = async () => {
      await new Promise(resolve => setTimeout(resolve, 500));
      setIsAuthenticating(false);
    };
    
    checkAuth();
  }, []);

  const handleTestUserLogin = () => {
    setIsAuthenticated(true);
    // Navigate to search page after login
    router.replace('/search');
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

  return null;
}
