export interface Document {
  id: string;
  name: string;
  type: 'image' | 'pdf';
  uri: string;
  thumbnail: string;
  uploadedAt: Date;
}

export interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
}

export type TabType = 'home' | 'documents';
export type PageType = 'main' | 'profile' | 'upload' | 'viewer';
