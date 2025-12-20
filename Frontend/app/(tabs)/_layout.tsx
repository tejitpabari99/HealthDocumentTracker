import { Tabs } from 'expo-router';
import React from 'react';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: { display: 'none' }, // Hide default tabs since we use custom BottomNav
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Health Docs',
        }}
      />
    </Tabs>
  );
}
