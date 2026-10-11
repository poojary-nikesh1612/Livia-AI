// src/components/Header.tsx
import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { COLORS, RADIUS, SPACING, TYPOGRAPHY } from '../constants/theme';
import { LanguageCode } from '../types/chat';
import { RicePanicleLogo } from './RicePanicleLogo';

interface HeaderProps {
  language: LanguageCode;
  onChangeLanguage: (lang: LanguageCode) => void;
}

export const Header: React.FC<HeaderProps> = ({
  language,
  onChangeLanguage,
}) => {
  return (
    <View style={styles.container} accessibilityRole="header">
      {/* Left: Golden Rice Panicle Logo & Localized App Title */}
      <View style={styles.brandRow}>
        <View style={styles.brandBadge} accessibilityElementsHidden>
          <RicePanicleLogo size={32} />
        </View>

        <View style={styles.titleBlock}>
          <Text style={styles.title}>
            {language === 'kn' ? 'ಲಿವಿಯಾ ಎಐ' : 'Livia AI'}
          </Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            {language === 'kn'
              ? 'ಭತ್ತದ ಬೆಳೆ ರೋಗ ನಿರ್ಣಯ ಸಹಾಯಕ'
              : 'Rice Crop Diagnostic Assistant'}
          </Text>
        </View>
      </View>

      {/* Right: Segmented Language Selector */}
      <View style={styles.rightControls}>
        <View
          style={styles.langPill}
          accessibilityRole="radiogroup"
          accessibilityLabel="Select conversation language"
        >
          <TouchableOpacity
            onPress={() => onChangeLanguage('en')}
            style={[
              styles.langOption,
              language === 'en' && styles.langOptionActive,
            ]}
            accessibilityRole="radio"
            accessibilityState={{ selected: language === 'en' }}
            accessibilityLabel="English language"
          >
            <Text
              style={[
                styles.langText,
                language === 'en' && styles.langTextActive,
              ]}
            >
              English
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => onChangeLanguage('kn')}
            style={[
              styles.langOption,
              language === 'kn' && styles.langOptionActive,
            ]}
            accessibilityRole="radio"
            accessibilityState={{ selected: language === 'kn' }}
            accessibilityLabel="Kannada language"
          >
            <Text
              style={[
                styles.langText,
                language === 'kn' && styles.langTextActive,
              ]}
            >
              ಕನ್ನಡ
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm + 2,
    backgroundColor: COLORS.primary,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.primaryDark,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexShrink: 1,
    marginRight: SPACING.sm,
  },
  brandBadge: {
    width: 40,
    height: 40,
    borderRadius: RADIUS.sm,
    backgroundColor: '#FFFDF7',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.sm,
    borderWidth: 1,
    borderColor: 'rgba(251, 192, 45, 0.45)',
  },
  titleBlock: {
    flexShrink: 1,
  },
  title: {
    ...TYPOGRAPHY.header,
    color: '#FFFFFF',
  },
  subtitle: {
    ...TYPOGRAPHY.subtitle,
    color: 'rgba(255, 255, 255, 0.85)',
    marginTop: 1,
  },
  rightControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  langPill: {
    flexDirection: 'row',
    backgroundColor: 'rgba(0, 0, 0, 0.22)',
    borderRadius: RADIUS.pill,
    padding: 2,
  },
  langOption: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
    minHeight: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  langOptionActive: {
    backgroundColor: '#FFFFFF',
  },
  langText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.88)',
  },
  langTextActive: {
    color: COLORS.primary,
    fontWeight: '700',
  },
});
