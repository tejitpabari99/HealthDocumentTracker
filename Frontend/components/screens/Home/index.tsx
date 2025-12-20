import React, { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, Linking } from 'react-native';
import { ThemedView, ThemedText } from '@/components/ui';
import { styles } from './styles';

// Mock data for API response
const getMockData = () => {
  const mockResponses = [
    {
      answer: "Based on your health records, your **blood pressure** has been consistently normal.\nKey findings:\n- Average BP: 120/80 mmHg\n- No significant variations detected\n- Continue regular monitoring",
      references: [
        { name: "Blood Pressure Report - Jan 2024", link: "https://example.com/bp-jan-2024" },
        { name: "Annual Health Checkup 2024", link: "https://example.com/checkup-2024" },
        { name: "Cardiology Consultation Notes", link: "https://example.com/cardio-notes" }
      ]
    },
    {
      answer: "Your recent **lab results** show normal values across all parameters.\n**Summary:**\n- Hemoglobin: 14.5 g/dL (Normal)\n- Blood Sugar: 95 mg/dL (Normal)\n- Cholesterol: 180 mg/dL (Healthy range)\nNo immediate concerns identified.",
      references: [
        { name: "Complete Blood Count Report", link: "https://example.com/cbc-report" },
        { name: "Lipid Profile Test", link: "https://example.com/lipid-profile" }
      ]
    },
    {
      answer: "Your **vaccination records** are up to date.\nCompleted vaccinations:\n- COVID-19: Booster dose (Dec 2023)\n- Influenza: Annual shot (Oct 2023)\n- Tetanus: Last dose 2020\n*Next recommended: Influenza vaccine in Oct 2024*",
      references: [
        { name: "Vaccination Certificate - COVID-19", link: "https://example.com/covid-vaccine" },
        { name: "Immunization History", link: "https://example.com/immunization" }
      ]
    }
  ];
  
  return mockResponses[Math.floor(Math.random() * mockResponses.length)];
};

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

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      return;
    }

    setIsLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      const mockData = getMockData();
      setSearchResult(mockData);
      setIsLoading(false);
    }, 500);
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

      {searchResult && (
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
