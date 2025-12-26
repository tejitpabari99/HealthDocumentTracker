import React, { useState } from 'react';
import { View, StatusBar } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { UploadPage } from '@/components/screens';
import { styles } from './(tabs)/styles';

export default function UploadScreen() {
  const insets = useSafeAreaInsets();

  const handleUploadSubmit = () => {
    // Navigate to documents page after successful upload
    router.push('/documents');
  };

  const handleBack = () => {
    router.back();
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <UploadPage onSubmit={handleUploadSubmit} onBack={handleBack} />
    </View>
  );
}
