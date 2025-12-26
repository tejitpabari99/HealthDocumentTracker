import React, { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, Linking, Alert } from 'react-native';
import { ThemedView, ThemedText } from '@/components/ui';
import { styles } from './styles';
import { searchDocuments } from '@/config/api';

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
      const response = await searchDocuments(searchQuery);
      
      // Parse the response
      // Backend returns: { message, query, refined_query }
      // The message contains the answer text and document reference
      const message = response.message || 'No results found.';
      
      // Extract document link if present (format: **Document Reference: URL**)
      const linkMatch = message.match(/\*\*Document Reference:\s*(https?:\/\/[^\*]+)\*\*/);
      const documentLink = linkMatch ? linkMatch[1].trim() : null;
      
      // Remove the document reference from the answer text
      const answerText = message.replace(/\n\n\*\*Document Reference:.*\*\*/, '');
      
      // Format the result
      const result: SearchResult = {
        answer: answerText,
        references: documentLink 
          ? [{ name: 'View Document', link: documentLink }]
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
