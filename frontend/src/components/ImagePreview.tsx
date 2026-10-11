// src/components/ImagePreview.tsx
import React from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { CONFIG } from '../constants/config';
import { COLORS, RADIUS, SPACING } from '../constants/theme';
import { LanguageCode, SelectedImage } from '../types/chat';

interface ImagePreviewProps {
  images: SelectedImage[];
  onRemoveImage: (uri: string) => void;
  disabled?: boolean;
  language?: LanguageCode;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  images,
  onRemoveImage,
  disabled = false,
  language = 'en',
}) => {
  if (!images || images.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.counterText}>
          {language === 'kn'
            ? `ಆಯ್ಕೆಮಾಡಿದ ಬೆಳೆ ಚಿತ್ರಗಳು (${images.length}/${CONFIG.MAX_IMAGES})`
            : `Selected crop photos (${images.length}/${CONFIG.MAX_IMAGES})`}
        </Text>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {images.map((img, index) => (
          <View key={`${img.uri}-${index}`} style={styles.thumbWrapper}>
            <Image
              source={{ uri: img.uri }}
              style={styles.thumbnail}
              resizeMode="cover"
              accessibilityLabel={`Selected crop photo ${index + 1}`}
            />
            {!disabled && (
              <TouchableOpacity
                onPress={() => onRemoveImage(img.uri)}
                style={styles.removeBtn}
                accessibilityRole="button"
                accessibilityLabel={`Remove crop photo ${index + 1}`}
                hitSlop={{ top: 6, bottom: 6, left: 6, right: 6 }}
              >
                <Text style={styles.removeIcon}>✕</Text>
              </TouchableOpacity>
            )}
          </View>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingTop: SPACING.xs + 2,
    paddingBottom: SPACING.xs,
    paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  counterText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  scrollContent: {
    gap: SPACING.sm,
    paddingRight: SPACING.sm,
  },
  thumbWrapper: {
    position: 'relative',
    width: 68,
    height: 68,
    borderRadius: RADIUS.sm,
    overflow: 'visible',
  },
  thumbnail: {
    width: 68,
    height: 68,
    borderRadius: RADIUS.sm,
    backgroundColor: COLORS.surfaceSubtle,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  removeBtn: {
    position: 'absolute',
    top: -6,
    right: -6,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: COLORS.textPrimary,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  removeIcon: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
    lineHeight: 13,
  },
});

