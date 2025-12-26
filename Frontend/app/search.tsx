import React, { useState } from 'react';
import { View, StatusBar } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Home } from '@/components/screens';
import { Header, BottomNav } from '@/components/navigation';
import { UserProfile } from '@/types';
import { TEST_USER } from '@/config/api';
import { styles } from './(tabs)/styles';

export default function SearchPage() {
  const insets = useSafeAreaInsets();
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

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <Header userProfile={userProfile} onProfileClick={handleProfileClick} />
      </View>

      <View style={[styles.content, { paddingBottom: 80 }]}>
        <Home />
      </View>

      <BottomNav
        activeTab="home"
        onTabChange={handleTabChange}
        onUploadClick={handleUploadClick}
      />
    </View>
  );
}
