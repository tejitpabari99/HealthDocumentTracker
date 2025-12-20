import React, { useState } from 'react';
import {
  View,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ThemedView, ThemedText } from '@/components/ui';
import { UserProfile } from '@/types';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';

interface ProfileProps {
  profile: UserProfile;
  onUpdateProfile: (profile: UserProfile) => void;
  onBack: () => void;
}

export function Profile({ profile, onUpdateProfile, onBack }: ProfileProps) {
  const insets = useSafeAreaInsets();
  const [firstName, setFirstName] = useState(profile.firstName);
  const [lastName, setLastName] = useState(profile.lastName);
  const [email, setEmail] = useState(profile.email);
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = () => {
    if (!firstName.trim() || !lastName.trim() || !email.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    onUpdateProfile({
      firstName: firstName.trim(),
      lastName: lastName.trim(),
      email: email.trim(),
    });
    setIsEditing(false);
    Alert.alert('Success', 'Profile updated successfully');
  };

  const handleCancel = () => {
    setFirstName(profile.firstName);
    setLastName(profile.lastName);
    setEmail(profile.email);
    setIsEditing(false);
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#007AFF" />
        </TouchableOpacity>
        <ThemedText type="title" style={styles.headerTitle}>
          Profile
        </ThemedText>
        <TouchableOpacity
          onPress={() => (isEditing ? handleCancel() : setIsEditing(true))}
          style={styles.editButton}
        >
          <ThemedText style={styles.editButtonText}>
            {isEditing ? 'Cancel' : 'Edit'}
          </ThemedText>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
      >
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={60} color="#007AFF" />
          </View>
          <ThemedText style={styles.userName}>
            {profile.firstName} {profile.lastName}
          </ThemedText>
        </View>

        <ThemedView style={styles.card}>
          <View style={styles.inputGroup}>
            <ThemedText style={styles.label}>First Name</ThemedText>
            <TextInput
              style={[
                styles.input,
                !isEditing && styles.inputDisabled,
              ]}
              value={firstName}
              onChangeText={setFirstName}
              editable={isEditing}
              placeholder="Enter first name"
              placeholderTextColor="#999"
            />
          </View>

          <View style={styles.inputGroup}>
            <ThemedText style={styles.label}>Last Name</ThemedText>
            <TextInput
              style={[
                styles.input,
                !isEditing && styles.inputDisabled,
              ]}
              value={lastName}
              onChangeText={setLastName}
              editable={isEditing}
              placeholder="Enter last name"
              placeholderTextColor="#999"
            />
          </View>

          <View style={styles.inputGroup}>
            <ThemedText style={styles.label}>Email</ThemedText>
            <TextInput
              style={[
                styles.input,
                !isEditing && styles.inputDisabled,
              ]}
              value={email}
              onChangeText={setEmail}
              editable={isEditing}
              placeholder="Enter email"
              keyboardType="email-address"
              autoCapitalize="none"
              placeholderTextColor="#999"
            />
          </View>

          {isEditing && (
            <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
              <ThemedText style={styles.saveButtonText}>
                Save Changes
              </ThemedText>
            </TouchableOpacity>
          )}
        </ThemedView>

        <ThemedView style={styles.card}>
          <ThemedText type="subtitle" style={styles.sectionTitle}>
            About
          </ThemedText>
          <ThemedText style={styles.aboutText}>
            This is your personal health document tracker. Your documents are
            stored securely on your device.
          </ThemedText>
        </ThemedView>
      </ScrollView>
    </View>
  );
}
