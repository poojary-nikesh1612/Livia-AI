// src/components/AudioPlayer.tsx
import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { COLORS, RADIUS, SPACING } from '../constants/theme';
import { LanguageCode } from '../types/chat';

interface AudioPlayerProps {
  isPlaying: boolean;
  isLoading: boolean;
  errorText?: string;
  language: LanguageCode;
  onPress: () => void;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  isPlaying,
  isLoading,
  errorText,
  language,
  onPress,
}) => {
  const getLabel = (): string => {
    if (isLoading) {
      return language === 'kn' ? 'ಧ್ವನಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ…' : 'Generating audio…';
    }
    if (isPlaying) {
      return language === 'kn' ? 'ನಿಲ್ಲಿಸಿ' : 'Stop audio';
    }
    if (errorText) {
      return language === 'kn' ? 'ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ' : 'Retry audio';
    }
    return language === 'kn' ? 'ಧ್ವನಿ ಕೇಳಿ' : 'Listen';
  };

  return (
    <View style={styles.wrapper}>
      <TouchableOpacity
        onPress={onPress}
        disabled={isLoading}
        style={[
          styles.button,
          isPlaying && styles.buttonPlaying,
          !!errorText && !isPlaying && styles.buttonError,
        ]}
        accessibilityRole="button"
        accessibilityState={{ busy: isLoading, selected: isPlaying }}
        accessibilityLabel={getLabel()}
      >
        {isLoading ? (
          <ActivityIndicator size="small" color={COLORS.primary} />
        ) : isPlaying ? (
          /* Stop square icon + active soundwave bars */
          <View style={styles.iconRow}>
            <View style={styles.stopSquare} />
            <View style={styles.waveGroup}>
              <View style={[styles.waveBar, styles.waveBarActive1]} />
              <View style={[styles.waveBar, styles.waveBarActive2]} />
              <View style={[styles.waveBar, styles.waveBarActive3]} />
            </View>
          </View>
        ) : (
          /* Pure View/CSS Speaker + Soundwaves icon */
          <View style={styles.speakerGraphic}>
            <View style={styles.speakerBox} />
            <View style={styles.speakerCone} />
            <View style={styles.soundArcInner} />
            <View style={styles.soundArcOuter} />
          </View>
        )}

        <Text
          style={[
            styles.labelText,
            isPlaying && styles.labelTextPlaying,
            !!errorText && !isPlaying && styles.labelTextError,
          ]}
        >
          {getLabel()}
        </Text>
      </TouchableOpacity>

      {!!errorText && !isLoading && !isPlaying && (
        <Text style={styles.errorCaption} numberOfLines={2}>
          {errorText}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    marginTop: SPACING.sm,
    alignItems: 'flex-start',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primaryLight,
    borderWidth: 1,
    borderColor: '#C8E6C9',
    borderRadius: RADIUS.pill,
    paddingHorizontal: 12,
    paddingVertical: 6,
    minHeight: 34,
    gap: 7,
  },
  buttonPlaying: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  buttonError: {
    backgroundColor: COLORS.errorBg,
    borderColor: '#FFCDD2',
  },
  speakerGraphic: {
    flexDirection: 'row',
    alignItems: 'center',
    width: 18,
    height: 14,
  },
  speakerBox: {
    width: 4,
    height: 6,
    backgroundColor: COLORS.primary,
    borderTopLeftRadius: 1,
    borderBottomLeftRadius: 1,
  },
  speakerCone: {
    width: 0,
    height: 0,
    borderTopWidth: 5,
    borderBottomWidth: 5,
    borderRightWidth: 5,
    borderTopColor: 'transparent',
    borderBottomColor: 'transparent',
    borderRightColor: COLORS.primary,
    marginLeft: -1,
  },
  soundArcInner: {
    width: 4,
    height: 8,
    borderRightWidth: 1.8,
    borderTopWidth: 1.2,
    borderBottomWidth: 1.2,
    borderColor: COLORS.primary,
    borderTopRightRadius: 6,
    borderBottomRightRadius: 6,
    marginLeft: 2,
  },
  soundArcOuter: {
    width: 4,
    height: 12,
    borderRightWidth: 1.8,
    borderTopWidth: 1.2,
    borderBottomWidth: 1.2,
    borderColor: COLORS.accent,
    borderTopRightRadius: 8,
    borderBottomRightRadius: 8,
    marginLeft: 1,
  },
  iconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  stopSquare: {
    width: 9,
    height: 9,
    borderRadius: 2,
    backgroundColor: '#FFFFFF',
  },
  waveGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  waveBar: {
    width: 2,
    backgroundColor: COLORS.accentLight,
    borderRadius: 1,
  },
  waveBarActive1: {
    height: 7,
  },
  waveBarActive2: {
    height: 12,
  },
  waveBarActive3: {
    height: 9,
  },
  labelText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  labelTextPlaying: {
    color: '#FFFFFF',
  },
  labelTextError: {
    color: COLORS.errorRed,
  },
  errorCaption: {
    fontSize: 11,
    color: COLORS.errorRed,
    marginTop: 3,
    marginLeft: 4,
  },
});
