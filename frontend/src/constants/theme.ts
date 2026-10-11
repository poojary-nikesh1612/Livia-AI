// src/constants/theme.ts
import { Platform, StyleSheet } from 'react-native';

export const COLORS = {
  primary: '#1B5E20',        // Deep forest green
  primaryDark: '#124116',    // Darker forest green for pressed states
  primaryLight: '#E8F5E9',   // Soft leaf tint for subtle badges/chips
  accent: '#4CAF50',         // Fresh rice-leaf green
  accentLight: '#81C784',    // Lighter leaf highlight
  background: '#F7F6F0',     // Warm off-white / rice-husk cream
  surface: '#FFFFFF',        // Crisp white surface for assistant cards
  surfaceSubtle: '#EFECE4',  // Subtle warm neutral surface
  textPrimary: '#1C281E',    // Deep charcoal-green readable text
  textSecondary: '#5A6B5C',  // Muted botanical gray-green
  textMuted: '#88968A',      // Placeholder and caption text
  textOnPrimary: '#FFFFFF',  // White text on primary green
  border: '#DCE3DC',         // Soft leaf-gray border
  errorRed: '#C62828',       // Accessible alert red
  errorBg: '#FFEBEE',        // Soft red background for error banners
  warningAmber: '#EF6C00',   // Clarification / status amber
  warningBg: '#FFF3E0',      // Soft amber background
  recordingRed: '#D32F2F',   // Active microphone recording indicator
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 14,
  lg: 20,
  xl: 28,
  xxl: 40,
};

export const RADIUS = {
  xs: 6,
  sm: 10,
  md: 16,
  lg: 22,
  pill: 999,
};

export const TYPOGRAPHY = {
  header: {
    fontSize: 19,
    fontWeight: '700' as const,
    color: COLORS.textPrimary,
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 12,
    fontWeight: '500' as const,
    color: COLORS.textSecondary,
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
    color: COLORS.textPrimary,
  },
  bodyStrong: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '600' as const,
    color: COLORS.textPrimary,
  },
  caption: {
    fontSize: 12,
    lineHeight: 16,
    color: COLORS.textSecondary,
  },
  small: {
    fontSize: 11,
    lineHeight: 14,
    color: COLORS.textMuted,
  },
};

export const SHADOWS = {
  card: Platform.select({
    ios: {
      shadowColor: '#1B5E20',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.06,
      shadowRadius: 6,
    },
    android: {
      elevation: 2,
    },
    default: {
      boxShadow: '0px 2px 6px rgba(27, 94, 32, 0.06)',
    },
  }),
  floating: Platform.select({
    ios: {
      shadowColor: '#000000',
      shadowOffset: { width: 0, height: -2 },
      shadowOpacity: 0.06,
      shadowRadius: 8,
    },
    android: {
      elevation: 6,
    },
    default: {
      boxShadow: '0px -2px 10px rgba(0, 0, 0, 0.05)',
    },
  }),
};

export const globalStyles = StyleSheet.create({
  flex1: { flex: 1 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  background: { backgroundColor: COLORS.background },
});
