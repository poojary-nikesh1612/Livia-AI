// src/components/EmptyState.tsx
import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { COLORS, RADIUS, SHADOWS, SPACING, TYPOGRAPHY } from '../constants/theme';
import { LanguageCode } from '../types/chat';
import { RicePanicleLogo } from './RicePanicleLogo';

interface EmptyStateProps {
  language: LanguageCode;
  onSelectSuggestion?: (promptText: string) => void;
}

const SUGGESTIONS_EN = [
  'My rice leaves have diamond-shaped brown spots with gray centers.',
  'Yellowing starts from leaf tips and spreads down the edges.',
  'What organic treatment works best for rice leaf blast?',
];

const SUGGESTIONS_KN = [
  'ನನ್ನ ಭತ್ತದ ಎಲೆಗಳ ಮೇಲೆ ಕಂದು ಬಣ್ಣದ ಚುಕ್ಕೆಗಳು ಕಾಣಿಸುತ್ತಿವೆ.',
  'ಭತ್ತದ ಎಲೆಗಳ ತುದಿ ಹಳದಿ ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿ ಒಣಗುತ್ತಿದೆ.',
  'ಭತ್ತದ ಬೆಂಕಿ ರೋಗಕ್ಕೆ ಪರಿಹಾರವೇನು?',
];

export const EmptyState: React.FC<EmptyStateProps> = ({
  language,
  onSelectSuggestion,
}) => {
  const suggestions = language === 'kn' ? SUGGESTIONS_KN : SUGGESTIONS_EN;

  return (
    <View style={styles.container}>
      {/* Golden Rice Panicle & Leaf Emblem */}
      <View style={styles.emblemCircle} accessibilityElementsHidden>
        <RicePanicleLogo size={62} />
      </View>

      <Text style={styles.heading}>
        {language === 'kn' ? 'ಲಿವಿಯಾ ಎಐ ಗೆ ಸ್ವಾಗತ' : 'Welcome to Livia AI'}
      </Text>

      <Text style={styles.description}>
        {language === 'kn'
          ? 'ನಿಮ್ಮ ಭತ್ತದ ಬೆಳೆಯ ಎಲೆಗಳ ಚಿತ್ರವನ್ನು ಕಳುಹಿಸಿ, ಧ್ವನಿ ಸಂದೇಶ ರೆಕಾರ್ಡ್ ಮಾಡಿ ಅಥವಾ ರೋಗಲಕ್ಷಣಗಳನ್ನು ಕೆಳಗೆ ವಿವರಿಸಿ.'
          : 'Upload up to 5 photos of affected rice leaves, record a voice note, or describe symptoms below in English or Kannada.'}
      </Text>

      {/* Feature Highlights */}
      <View style={styles.featurePills}>
        <View style={styles.pill}>
          <Text style={styles.pillText}>
            {language === 'kn' ? '📷 ಬೆಳೆ ಚಿತ್ರ ಪರೀಕ್ಷೆ' : '📷 Leaf Photo Diagnosis'}
          </Text>
        </View>
        <View style={styles.pill}>
          <Text style={styles.pillText}>
            {language === 'kn' ? '🎙️ ಧ್ವನಿ ಸಂವಾದ' : '🎙️ Voice Advisory'}
          </Text>
        </View>
        <View style={styles.pill}>
          <Text style={styles.pillText}>
            {language === 'kn' ? '🌾 ಕನ್ನಡ ಮತ್ತು ಇಂಗ್ಲಿಷ್' : '🌾 English & ಕನ್ನಡ'}
          </Text>
        </View>
      </View>

      {/* Starter Prompts */}
      {onSelectSuggestion && (
        <View style={styles.suggestionsBox}>
          <Text style={styles.suggestionsTitle}>
            {language === 'kn' ? 'ಪ್ರಾರಂಭಿಸಲು ಒಂದನ್ನು ಆರಿಸಿ:' : 'Try asking:'}
          </Text>
          {suggestions.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.suggestionCard}
              onPress={() => onSelectSuggestion(item)}
              accessibilityRole="button"
              accessibilityLabel={`Use sample question: ${item}`}
            >
              <Text style={styles.suggestionText}>“{item}”</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.xl,
  },
  emblemCircle: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: '#FFFDF7',
    borderWidth: 2,
    borderColor: '#FBC02D',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.md,
    ...SHADOWS.card,
  },
  heading: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.xs + 2,
    textAlign: 'center',
  },
  description: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    textAlign: 'center',
    maxWidth: 420,
    marginBottom: SPACING.md,
  },
  featurePills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: SPACING.xs + 2,
    marginBottom: SPACING.lg,
  },
  pill: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.pill,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  pillText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  suggestionsBox: {
    width: '100%',
    maxWidth: 440,
    gap: SPACING.xs + 2,
  },
  suggestionsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textSecondary,
    marginBottom: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  suggestionCard: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm + 2,
    ...SHADOWS.card,
  },
  suggestionText: {
    fontSize: 13.5,
    color: COLORS.textPrimary,
    lineHeight: 19,
  },
});
