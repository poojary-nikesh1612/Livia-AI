// src/components/TypingIndicator.tsx
import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';
import { COLORS, RADIUS, SHADOWS, SPACING } from '../constants/theme';
import { LanguageCode } from '../types/chat';
import { RicePanicleLogo } from './RicePanicleLogo';

interface TypingIndicatorProps {
  language?: LanguageCode;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  language = 'en',
}) => {
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const createPulse = (val: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(val, {
            toValue: -5,
            duration: 280,
            useNativeDriver: true,
          }),
          Animated.timing(val, {
            toValue: 0,
            duration: 280,
            useNativeDriver: true,
          }),
        ])
      );

    const a1 = createPulse(dot1, 0);
    const a2 = createPulse(dot2, 140);
    const a3 = createPulse(dot3, 280);

    a1.start();
    a2.start();
    a3.start();

    return () => {
      a1.stop();
      a2.stop();
      a3.stop();
    };
  }, [dot1, dot2, dot3]);

  return (
    <View
      style={styles.row}
      accessible
      accessibilityLabel={
        language === 'kn'
          ? 'ಲಿವಿಯಾ ಎಐ ವಿಶ್ಲೇಷಿಸುತ್ತಿದೆ'
          : 'Livia AI is analyzing your crop query'
      }
    >
      <View style={styles.avatar}>
        <RicePanicleLogo size={24} />
      </View>

      <View style={styles.bubble}>
        <View style={styles.dotsRow}>
          {[dot1, dot2, dot3].map((dot, idx) => (
            <Animated.View
              key={idx}
              style={[styles.dot, { transform: [{ translateY: dot }] }]}
            />
          ))}
        </View>
        <Text style={styles.statusText}>
          {language === 'kn'
            ? 'ಲಿವಿಯಾ ಎಐ ಪರಿಶೀಲಿಸುತ್ತಿದೆ…'
            : 'Livia AI is analyzing…'}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    marginVertical: SPACING.xs + 2,
  },
  avatar: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#FFFDF7',
    borderWidth: 1,
    borderColor: '#FBC02D',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.sm,
  },
  bubble: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderTopLeftRadius: 4,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm + 2,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: SPACING.sm,
    ...SHADOWS.card,
  },
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: COLORS.accent,
  },
  statusText: {
    fontSize: 12.5,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
});
