import React from 'react';
import { View, TouchableOpacity } from 'react-native';
import { ThemedText } from '@/components/ui';
import { TabType } from '@/types';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';

interface BottomNavProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  onUploadClick: () => void;
}

export function BottomNav({
  activeTab,
  onTabChange,
  onUploadClick,
}: BottomNavProps) {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.tab}
        onPress={() => onTabChange('home')}
        activeOpacity={0.7}
      >
        <Ionicons
          name={activeTab === 'home' ? 'home' : 'home-outline'}
          size={24}
          color={activeTab === 'home' ? '#007AFF' : '#666'}
        />
        <ThemedText
          style={[
            styles.tabText,
            activeTab === 'home' && styles.activeTabText,
          ]}
        >
          Home
        </ThemedText>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.uploadButton}
        onPress={onUploadClick}
        activeOpacity={0.7}
      >
        <View style={styles.uploadButtonInner}>
          <Ionicons name="add" size={32} color="#fff" />
        </View>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.tab}
        onPress={() => onTabChange('documents')}
        activeOpacity={0.7}
      >
        <Ionicons
          name={activeTab === 'documents' ? 'folder' : 'folder-outline'}
          size={24}
          color={activeTab === 'documents' ? '#007AFF' : '#666'}
        />
        <ThemedText
          style={[
            styles.tabText,
            activeTab === 'documents' && styles.activeTabText,
          ]}
        >
          Documents
        </ThemedText>
      </TouchableOpacity>
    </View>
  );
}
