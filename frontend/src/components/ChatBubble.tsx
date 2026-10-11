// src/components/ChatBubble.tsx
import React, { useState } from 'react';
import {
  Image,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { COLORS, RADIUS, SHADOWS, SPACING, TYPOGRAPHY } from '../constants/theme';
import { ChatMessage, LanguageCode } from '../types/chat';
import { formatDuration } from '../utils/audio';
import { AudioPlayer } from './AudioPlayer';
import { RicePanicleLogo } from './RicePanicleLogo';

interface ChatBubbleProps {
  message: ChatMessage;
  isUser: boolean;
  language: LanguageCode;
  isPlayingAudio: boolean;
  isLoadingAudio: boolean;
  audioErrorText?: string;
  onPressAudio: () => void;
  onRetrySend?: (message: ChatMessage) => void;
}

/**
 * Safely renders Markdown-like inline bold (**text**) and line breaks without HTML injection.
 */
const renderFormattedText = (text: string, isUser: boolean) => {
  const lines = text.split('\n');
  return lines.map((line, lineIdx) => {
    const trimmed = line.trim();
    const isBullet = /^[-*•]\s+/.test(trimmed);
    const cleanLine = isBullet ? trimmed.replace(/^[-*•]\s+/, '• ') : line;

    const segments = cleanLine.split(/(\*\*[^*]+\*\*)/g);

    return (
      <Text
        key={lineIdx}
        style={[
          isUser ? styles.userText : styles.assistantText,
          lineIdx < lines.length - 1 && styles.paragraphGap,
        ]}
      >
        {segments.map((seg, segIdx) => {
          if (seg.startsWith('**') && seg.endsWith('**') && seg.length > 4) {
            return (
              <Text
                key={segIdx}
                style={isUser ? styles.userBoldText : styles.assistantBoldText}
              >
                {seg.slice(2, -2)}
              </Text>
            );
          }
          return <Text key={segIdx}>{seg}</Text>;
        })}
      </Text>
    );
  });
};

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  message,
  isUser,
  language,
  isPlayingAudio,
  isLoadingAudio,
  audioErrorText,
  onPressAudio,
  onRetrySend,
}) => {
  const [previewUri, setPreviewUri] = useState<string | null>(null);

  const validImages = (message.images ?? []).filter(
    (uri) =>
      typeof uri === 'string' &&
      (uri.startsWith('http://') ||
        uri.startsWith('https://') ||
        uri.startsWith('file://') ||
        uri.startsWith('data:image/') ||
        uri.startsWith('blob:') ||
        uri.startsWith('content://'))
  );

  const formattedTime = message.timestamp
    ? (() => {
        const d = new Date(message.timestamp);
        return isNaN(d.getTime())
          ? ''
          : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      })()
    : '';

  const canPlayUserVoice =
    isUser &&
    message.hasVoiceInput &&
    Boolean(message.audioUri || message.audioBase64);

  return (
    <>
      <View
        style={isUser ? styles.userRow : styles.assistantRow}
        accessible
        accessibilityLabel={
          isUser
            ? 'Your message'
            : language === 'kn'
              ? 'ಲಿವಿಯಾ ಎಐ ಸಂದೇಶ'
              : 'Livia AI message'
        }
      >
        {/* Assistant Golden Rice Panicle Avatar */}
        {!isUser && (
          <View style={styles.avatar} accessibilityElementsHidden>
            <RicePanicleLogo size={24} />
          </View>
        )}

        <View
          style={[
            isUser ? styles.userBubble : styles.assistantBubble,
            isUser && message.status === 'failed' && styles.userBubbleFailed,
          ]}
        >
          {/* Assistant Header Tag */}
          {!isUser && (
            <Text style={styles.assistantName}>
              {language === 'kn' ? 'ಲಿವಿಯಾ ಎಐ' : 'Livia AI'}
            </Text>
          )}

          {/* Interactive Voice Note Player for User Messages */}
          {isUser && message.hasVoiceInput && (
            <TouchableOpacity
              onPress={canPlayUserVoice ? onPressAudio : undefined}
              disabled={!canPlayUserVoice}
              activeOpacity={0.8}
              style={[
                styles.voiceBadge,
                isPlayingAudio && styles.voiceBadgePlaying,
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected: isPlayingAudio }}
              accessibilityLabel={
                isPlayingAudio
                  ? language === 'kn'
                    ? 'ಧ್ವನಿ ಸಂದೇಶ ನಿಲ್ಲಿಸಿ'
                    : 'Stop playing your voice note'
                  : language === 'kn'
                    ? 'ನಿಮ್ಮ ಧ್ವನಿ ಸಂದೇಶ ಕೇಳಿ'
                    : 'Play your voice note'
              }
            >
              {/* Play / Stop circle button */}
              <View style={styles.userPlayCircle}>
                {isPlayingAudio ? (
                  <View style={styles.userStopSquare} />
                ) : (
                  <View style={styles.userPlayTriangle} />
                )}
              </View>

              <View style={styles.voiceWaveRow}>
                <View style={[styles.vBar, { height: 7 }]} />
                <View style={[styles.vBar, { height: 13 }]} />
                <View style={[styles.vBar, { height: 9 }]} />
                <View style={[styles.vBar, { height: 14 }]} />
                <View style={[styles.vBar, { height: 8 }]} />
                <View style={[styles.vBar, { height: 11 }]} />
              </View>

              <Text style={styles.voiceBadgeText}>
                {isPlayingAudio
                  ? language === 'kn'
                    ? 'ನಿಲ್ಲಿಸಿ'
                    : 'Playing…'
                  : language === 'kn'
                    ? 'ಧ್ವನಿ ಕೇಳಿ'
                    : 'Voice note'}
                {message.voiceDurationSeconds
                  ? ` (${formatDuration(message.voiceDurationSeconds)})`
                  : ''}
              </Text>
            </TouchableOpacity>
          )}

          {/* Attached Crop Photos */}
          {validImages.length > 0 && (
            <View style={styles.imageGrid}>
              {validImages.map((uri, idx) => (
                <TouchableOpacity
                  key={`${uri}-${idx}`}
                  onPress={() => setPreviewUri(uri)}
                  activeOpacity={0.85}
                  accessibilityRole="imagebutton"
                  accessibilityLabel={`View attached crop image ${idx + 1}`}
                >
                  <Image
                    source={{ uri }}
                    style={[
                      styles.attachedImage,
                      validImages.length === 1 && styles.singleImage,
                    ]}
                    resizeMode="cover"
                  />
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Message Text */}
          {!!message.text && (
            <View style={styles.textBlock}>
              {renderFormattedText(message.text, isUser)}
            </View>
          )}

          {/* Assistant Audio Playback Button */}
          {!isUser && !!message.text && (
            <AudioPlayer
              isPlaying={isPlayingAudio}
              isLoading={isLoadingAudio}
              errorText={audioErrorText}
              language={language}
              onPress={onPressAudio}
            />
          )}

          {/* Footer: Timestamp only (no 'Sending...' status) */}
          {!!formattedTime && (
            <View style={styles.footerRow}>
              <Text style={isUser ? styles.userTime : styles.assistantTime}>
                {formattedTime}
              </Text>
            </View>
          )}

          {/* Failed State + Retry Control */}
          {isUser && message.status === 'failed' && (
            <View style={styles.failedBox}>
              <Text style={styles.failedReason}>
                {message.errorText ||
                  (language === 'kn'
                    ? 'ಕಳುಹಿಸಲು ವಿಫಲವಾಗಿದೆ.'
                    : 'Delivery failed.')}
              </Text>
              {onRetrySend && message.retryPayload && (
                <TouchableOpacity
                  onPress={() => onRetrySend(message)}
                  style={styles.retryBtn}
                  accessibilityRole="button"
                  accessibilityLabel="Retry sending this message"
                >
                  <Text style={styles.retryBtnText}>
                    {language === 'kn' ? 'ಮತ್ತೆ ಕಳುಹಿಸಿ ↻' : 'Retry ↻'}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>
      </View>

      {/* Fullscreen Image Lightbox Modal */}
      <Modal
        visible={!!previewUri}
        transparent
        animationType="fade"
        onRequestClose={() => setPreviewUri(null)}
      >
        <Pressable
          style={styles.modalBackdrop}
          onPress={() => setPreviewUri(null)}
        >
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={() => setPreviewUri(null)}
              style={styles.modalCloseBtn}
              accessibilityRole="button"
              accessibilityLabel="Close image preview"
            >
              <Text style={styles.modalCloseText}>
                {language === 'kn' ? '✕ ಮುಚ್ಚಿ' : '✕ Close'}
              </Text>
            </TouchableOpacity>
          </View>
          {previewUri && (
            <Image
              source={{ uri: previewUri }}
              style={styles.fullscreenImage}
              resizeMode="contain"
            />
          )}
        </Pressable>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  userRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginVertical: SPACING.xs + 2,
    paddingHorizontal: SPACING.md,
  },
  assistantRow: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    marginVertical: SPACING.xs + 2,
    paddingHorizontal: SPACING.md,
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
    marginTop: 2,
  },
  userBubble: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    borderBottomRightRadius: 4,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm + 2,
    maxWidth: '82%',
    ...SHADOWS.card,
  },
  userBubbleFailed: {
    backgroundColor: '#7F1D1D',
  },
  assistantBubble: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderTopLeftRadius: 4,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm + 3,
    borderWidth: 1,
    borderColor: COLORS.border,
    maxWidth: '84%',
    flexShrink: 1,
    ...SHADOWS.card,
  },
  assistantName: {
    fontSize: 11.5,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: 4,
    letterSpacing: 0.2,
  },
  voiceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.18)',
    borderRadius: RADIUS.pill,
    paddingHorizontal: 10,
    paddingVertical: 7,
    marginBottom: 4,
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.28)',
  },
  voiceBadgePlaying: {
    backgroundColor: 'rgba(255, 255, 255, 0.28)',
    borderColor: '#FFFFFF',
  },
  userPlayCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  userPlayTriangle: {
    width: 0,
    height: 0,
    borderTopWidth: 5,
    borderBottomWidth: 5,
    borderLeftWidth: 8,
    borderTopColor: 'transparent',
    borderBottomColor: 'transparent',
    borderLeftColor: COLORS.primary,
    marginLeft: 2,
  },
  userStopSquare: {
    width: 8,
    height: 8,
    borderRadius: 1.5,
    backgroundColor: COLORS.primary,
  },
  voiceWaveRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2.5,
  },
  vBar: {
    width: 2.2,
    backgroundColor: '#FFFFFF',
    borderRadius: 1,
  },
  voiceBadgeText: {
    fontSize: 12.5,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  imageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 6,
  },
  attachedImage: {
    width: 96,
    height: 96,
    borderRadius: RADIUS.sm,
    backgroundColor: COLORS.surfaceSubtle,
  },
  singleImage: {
    width: 190,
    height: 145,
  },
  textBlock: {
    marginTop: 1,
  },
  paragraphGap: {
    marginBottom: 4,
  },
  userText: {
    ...TYPOGRAPHY.body,
    color: '#FFFFFF',
  },
  userBoldText: {
    ...TYPOGRAPHY.bodyStrong,
    color: '#FFFFFF',
  },
  assistantText: {
    ...TYPOGRAPHY.body,
    color: COLORS.textPrimary,
  },
  assistantBoldText: {
    ...TYPOGRAPHY.bodyStrong,
    color: COLORS.textPrimary,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 4,
  },
  userTime: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.72)',
  },
  assistantTime: {
    fontSize: 10,
    color: COLORS.textMuted,
  },
  failedBox: {
    marginTop: SPACING.xs + 2,
    paddingTop: SPACING.xs + 2,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.22)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: SPACING.sm,
  },
  failedReason: {
    fontSize: 11,
    color: '#FFCDD2',
    flexShrink: 1,
  },
  retryBtn: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
  },
  retryBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#7F1D1D',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.88)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.md,
  },
  modalHeader: {
    position: 'absolute',
    top: 48,
    right: 20,
    zIndex: 10,
  },
  modalCloseBtn: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: RADIUS.pill,
  },
  modalCloseText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  fullscreenImage: {
    width: '94%',
    height: '78%',
    borderRadius: RADIUS.md,
  },
});
