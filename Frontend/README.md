# Health Document Tracker - React Native Expo App

A secure and user-friendly mobile application for managing health documents. Built with React Native and Expo, this app allows users to upload, organize, and view their medical records, prescriptions, test results, and other health-related documents.

## Features

- **Document Management**: Upload and store images and PDF documents
- **Document Search**: Search through all of your medical information and retrieve medical documents.
- **Share Documents**: Share documents with doctor, family or anyone else.

## Screenshots

The app includes:
- **Home Screen**: Welcome page with quick guide and features
- **Documents Screen**: Grid view of all uploaded documents
- **Upload Screen**: Easy file selection from photos or documents
- **Document Viewer**: View document details and images
- **Profile Screen**: Edit your personal information
- **About Screen**: Information about the app and how to use it

## Tech Stack

- **React Native**: Cross-platform mobile development
- **Expo**: Development platform and tooling
- **TypeScript**: Type-safe code
- **AsyncStorage**: Local data persistence
- **Expo Document Picker**: File selection
- **Expo Image Picker**: Photo selection
- **Expo Router**: File-based navigation

## Installation

1. Clone the repository
2. Navigate to the Frontend directory:
   ```bash
   cd Frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

## Running the App

### Development Mode

Start the Expo development server:
```bash
npm start
```

This will open Expo DevTools in your browser. From there, you can:
- Press `a` to open on Android emulator
- Press `i` to open on iOS simulator
- Scan the QR code with Expo Go app on your physical device

### Platform-Specific Commands

```bash
# Run on Android
npm run android

# Run on iOS
npm run ios

# Run on Web
npm run web
```

## Project Structure

```
Frontend/
├── app/                      # Expo Router pages
│   ├── (tabs)/              # Tab navigation
│   │   ├── index.tsx        # Main app screen (Home/Documents)
│   │   └── explore.tsx      # About/Info screen
│   ├── _layout.tsx          # Root layout
│   └── modal.tsx            # Modal screen
├── components/
│   ├── screens/             # Screen components
│   │   ├── Home.tsx         # Home screen
│   │   ├── DocumentStore.tsx # Documents grid view
│   │   ├── Profile.tsx      # Profile management
│   │   ├── UploadPage.tsx   # File upload screen
│   │   └── DocumentViewer.tsx # Document details
│   ├── navigation/          # Navigation components
│   │   ├── Header.tsx       # Top header
│   │   ├── BottomNav.tsx    # Bottom navigation
│   │   └── Disclaimer.tsx   # Success notification
│   ├── ui/                  # UI components
│   └── themed-*.tsx         # Themed components
├── types/                   # TypeScript type definitions
│   └── index.ts            # App types
├── constants/              # App constants
├── hooks/                  # Custom hooks
└── assets/                 # Images and other assets
```

## Key Components

### Main App (index.tsx)
- Manages app state (documents, profile, navigation)
- Handles document upload, deletion, and viewing
- Persists data using AsyncStorage
- Coordinates between different screens

### Screen Components

1. **Home**: Welcome screen with app information and quick guide
2. **DocumentStore**: Grid display of uploaded documents with thumbnails
3. **Profile**: User profile management with edit capability
4. **UploadPage**: File selection interface for photos and documents
5. **DocumentViewer**: Full-screen document viewing with metadata

### Navigation Components

1. **Header**: Top bar with app title and profile button
2. **BottomNav**: Bottom tab navigation with floating upload button
3. **Disclaimer**: Toast notification for successful uploads

## Data Storage

The app uses AsyncStorage to persist:
- **Documents**: All uploaded documents with metadata
- **User Profile**: User's personal information

Data is stored locally on the device and never sent to external servers.

## Permissions

The app requires the following permissions:
- **Media Library**: To select photos from the device
- **File System**: To access and store documents

## Type Definitions

```typescript
interface Document {
  id: string;
  name: string;
  type: 'image' | 'pdf';
  uri: string;
  thumbnail: string;
  uploadedAt: Date;
}

interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
}
```

## Development

### Adding New Features

1. Create new components in the appropriate directory
2. Update types in `types/index.ts` if needed
3. Update the main app logic in `app/(tabs)/index.tsx`
4. Test on all target platforms

### Code Style

- Use TypeScript for type safety
- Follow React Native best practices
- Use functional components with hooks
- Keep components focused and reusable

## Troubleshooting

### Common Issues

1. **App won't start**: Clear cache with `npm start -- --clear`
2. **Type errors**: Run `npx tsc --noEmit` to check TypeScript errors
3. **Module not found**: Delete `node_modules` and run `npm install` again

## Future Enhancements

Possible improvements:
- PDF viewer integration
- Document categories and tags
- Search functionality
- Cloud backup option
- Document sharing
- OCR text extraction
- Biometric authentication

## License

This project is part of the Health Document Tracker application.

## Support

For issues or questions, please create an issue in the repository.
