import React, { useEffect } from 'react';
import { View, Animated } from 'react-native';
import { ThemedText } from '@/components/ui';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles';

export function Disclaimer() {
  const fadeAnim = new Animated.Value(0);
  const slideAnim = new Animated.Value(50);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      <View style={styles.content}>
        <Ionicons name="checkmark-circle" size={24} color="#34c759" />
        <View style={styles.textContainer}>
          <ThemedText style={styles.title}>Upload Successful!</ThemedText>
          <ThemedText style={styles.message}>
            Your documents have been securely stored
          </ThemedText>
        </View>
      </View>
    </Animated.View>
  );
}
