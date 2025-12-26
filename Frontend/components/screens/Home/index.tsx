import React, { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, Linking, Alert } from 'react-native';
import { ThemedView, ThemedText } from '@/components/ui';
import { styles } from './styles';
import { searchDocuments } from '@/config/api';
import { SearchResponse } from '@/types';

interface Reference {
  name: string;
  link: string;
}

interface SearchResult {
  answer: string;
  references: Reference[];
}

export function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      return;
    }

    setIsLoading(true);
    
    try {
      // Call the backend search API
      const response: SearchResponse = await searchDocuments(searchQuery);
      
      // Backend now returns: { message, sas_url, query, refined_query, searchId, etc. }
      // The sas_url is the direct reference to the document
      const answerText = response.message || 'No results found.';
      const sasUrl = response.sas_url;
      
      // Format the result
      const result: SearchResult = {
        answer: answerText,
        references: sasUrl 
          ? [{ name: 'View Document', link: sasUrl }]
          : []
      };
      
      setSearchResult(result);
    } catch (error: any) {
      console.error('Search failed:', error);
      Alert.alert(
        'Search Failed',
        error.message || 'Failed to search documents. Please check your connection and try again.'
      );
      setSearchResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLinkPress = (url: string) => {
    Linking.openURL(url).catch(err => console.error("Failed to open URL:", err));
  };

  const renderFormattedText = (text: string) => {
    // Split by newlines and process each segment
    const segments = text.split('\n');
    
    return segments.map((segment, index) => {
      // Process bold text (**text**)
      const parts = segment.split(/(\*\*.*?\*\*)/g);
      
      return (
        <Text key={index} style={styles.answerText}>
          {parts.map((part, partIndex) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              // Remove ** and render as bold
              const boldText = part.slice(2, -2);
              return (
                <Text key={partIndex} style={styles.boldText}>
                  {boldText}
                </Text>
              );
            }
            return part;
          })}
          {index < segments.length - 1 && '\n'}
        </Text>
      );
    });
  };

  return (
    <ScrollView 
      style={styles.container} 
      contentContainerStyle={styles.contentContainer} 
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
    >
      <TextInput
        style={styles.searchInput}
        placeholder="Search your docs"
        placeholderTextColor="#999"
        value={searchQuery}
        onChangeText={setSearchQuery}
        onSubmitEditing={handleSearch}
        returnKeyType="search"
      />

      {isLoading && (
        <ThemedView style={styles.resultContainer}>
          <ThemedText style={styles.loadingText}>Searching...</ThemedText>
        </ThemedView>
      )}

      {!isLoading && searchResult && (
        <ThemedView style={styles.resultContainer}>
          <ThemedView style={styles.answerSection}>
            <View style={styles.answerContent}>
              {renderFormattedText(searchResult.answer)}
            </View>
          </ThemedView>

          {searchResult.references.length > 0 && (
            <ThemedView style={styles.referencesSection}>
              <ThemedText type="subtitle" style={styles.sectionTitle}>References</ThemedText>
              {searchResult.references.map((ref, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.referenceItem}
                  onPress={() => handleLinkPress(ref.link)}
                >
                  <Text style={styles.referenceLink}>{ref.name}</Text>
                </TouchableOpacity>
              ))}
            </ThemedView>
          )}
        </ThemedView>
      )}
    </ScrollView>
  );
}
