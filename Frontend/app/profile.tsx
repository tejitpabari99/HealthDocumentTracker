import React, { useState } from 'react';
import { View, StatusBar } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Profile } from '@/components/screens';
import { UserProfile } from '@/types';
import { TEST_USER } from '@/config/api';
import { styles } from './(tabs)/styles';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const [userProfile, setUserProfile] = useState<UserProfile>({
    firstName: 'Test',
    lastName: 'User',
    email: TEST_USER.email,
  });

  const handleUpdateProfile = (profile: UserProfile) => {
    setUserProfile(profile);
  };

  const handleBack = () => {
    router.back();
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <Profile
        profile={userProfile}
        onUpdateProfile={handleUpdateProfile}
        onBack={handleBack}
      />
    </View>
  );
}
