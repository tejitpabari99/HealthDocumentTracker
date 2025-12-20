import React from 'react';
import { View, TouchableOpacity } from 'react-native';
import { ThemedText } from '@/components/ui';
import { UserProfile } from '@/types';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';

interface HeaderProps {
  userProfile: UserProfile;
  onProfileClick: () => void;
}

export function Header({ userProfile, onProfileClick }: HeaderProps) {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.leftSection}>
          <Ionicons name="medical" size={28} color="#007AFF" />
          <ThemedText type="title" style={styles.title}>
            Health Docs
          </ThemedText>
        </View>
        <TouchableOpacity onPress={onProfileClick} style={styles.profileButton}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={20} color="#007AFF" />
          </View>
        </TouchableOpacity>
      </View>
    </View>
  );
}
