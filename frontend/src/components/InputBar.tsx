// src/components/InputBar.tsx
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Linking,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { CONFIG } from '../constants/config';
import { COLORS, RADIUS, SHADOWS, SPACING } from '../constants/theme';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { AudioRecordingResult, LanguageCode, SelectedImage } from '../types/chat';
import { formatDuration } from '../utils/audio';
import { detectImageMimeType, validateSelectedImage } from '../utils/images';
import { ImagePreview } from './ImagePreview';

export interface InputSubmission {
  text: string;
  images: SelectedImage[];
  audio: AudioRecordingResult | null;
}

interface InputBarProps {
  language: LanguageCode;
  isSending: boolean;
  prefillText?: string;
  onConsumePrefill?: () => void;
  isPreviewPlaying?: boolean;
  onTogglePreviewAudio?: (uri: string) => void;
  onStopPreviewAudio?: () => void;
  onSend: (submission: InputSubmission) => Promise<boolean>;
}

export const InputBar: React.FC<InputBarProps> = ({
  language,
  isSending,
  prefillText,
  onConsumePrefill,
  isPreviewPlaying = false,
  onTogglePreviewAudio,
  onStopPreviewAudio,
  onSend,
}) => {
  const [text, setText] = useState('');
  const [selectedImages, setSelectedImages] = useState<SelectedImage[]>([]);
  const [notice, setNotice] = useState<{
    message: string;
    canOpenSettings?: boolean;
  } | null>(null);

  const {
    isRecording,
    elapsedSeconds,
    recordedAudio,
    errorMessage: recorderError,
    startRecording,
    stopRecording,
    discardRecording,
    consumeRecording,
    clearError: clearRecorderError,
  } = useAudioRecorder();

  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (prefillText && prefillText.trim().length > 0) {
      setText(prefillText);
      onConsumePrefill?.();
    }
  }, [prefillText, onConsumePrefill]);

  useEffect(() => {
    if (recorderError) {
      setNotice({
        message: recorderError,
        canOpenSettings: recorderError.toLowerCase().includes('permission'),
      });
    }
  }, [recorderError]);

  useEffect(() => {
    if (!isRecording) {
      pulseAnim.setValue(1);
      return;
    }
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 0.35,
          duration: 550,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 550,
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [isRecording, pulseAnim]);

  const appendPickedAssets = useCallback(
    (assets: ImagePicker.ImagePickerAsset[]) => {
      setNotice(null);
      setSelectedImages((prev) => {
        const remainingSlots = CONFIG.MAX_IMAGES - prev.length;
        if (remainingSlots <= 0) {
          setNotice({
            message:
              language === 'kn'
                ? `ಗರಿಷ್ಠ ${CONFIG.MAX_IMAGES} ಚಿತ್ರಗಳನ್ನು ಮಾತ್ರ ಸೇರಿಸಬಹುದು.`
                : `You can attach up to ${CONFIG.MAX_IMAGES} photos per message.`,
          });
          return prev;
        }

        const existingUris = new Set(prev.map((item) => item.uri));
        const nextList = [...prev];
        let skippedOverflow = false;

        for (const asset of assets) {
          if (!asset.uri || existingUris.has(asset.uri)) {
            continue;
          }
          const candidate: SelectedImage = {
            uri: asset.uri,
            mimeType: detectImageMimeType(asset.uri, asset.mimeType),
            fileName: asset.fileName ?? undefined,
            width: asset.width,
            height: asset.height,
            fileSize: asset.fileSize,
            base64: asset.base64 ?? undefined,
          };

          const validation = validateSelectedImage(candidate);
          if (!validation.valid) {
            setNotice({ message: validation.reason ?? 'Invalid image selected.' });
            continue;
          }

          if (nextList.length < CONFIG.MAX_IMAGES) {
            nextList.push(candidate);
            existingUris.add(candidate.uri);
          } else {
            skippedOverflow = true;
          }
        }

        if (skippedOverflow) {
          setNotice({
            message:
              language === 'kn'
                ? `ಮೊದಲ ${CONFIG.MAX_IMAGES} ಚಿತ್ರಗಳನ್ನು ಮಾತ್ರ ಉಳಿಸಲಾಗಿದೆ.`
                : `Maximum of ${CONFIG.MAX_IMAGES} images reached. Extra selections were skipped.`,
          });
        }

        return nextList;
      });
    },
    [language]
  );

  // Camera capture
  const handleOpenCamera = useCallback(async () => {
    if (isSending || isRecording) return;
    setNotice(null);

    if (selectedImages.length >= CONFIG.MAX_IMAGES) {
      setNotice({
        message:
          language === 'kn'
            ? `ಗರಿಷ್ಠ ${CONFIG.MAX_IMAGES} ಚಿತ್ರಗಳ ಮಿತಿ ತಲುಪಿದೆ.`
            : `Maximum of ${CONFIG.MAX_IMAGES} images already selected.`,
      });
      return;
    }

    try {
      if (Platform.OS !== 'web') {
        const perm = await ImagePicker.requestCameraPermissionsAsync();
        if (!perm.granted) {
          setNotice({
            message:
              language === 'kn'
                ? 'ಕ್ಯಾಮೆರಾ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಅನುಮತಿಸಿ.'
                : 'Camera permission was denied. Please enable camera access in Settings.',
            canOpenSettings: true,
          });
          return;
        }
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        quality: 0.82,
        allowsEditing: false,
      });

      if (!result.canceled && result.assets?.length) {
        appendPickedAssets(result.assets);
      }
    } catch {
      setNotice({
        message:
          language === 'kn'
            ? 'ಕ್ಯಾಮೆರಾ ತೆರೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.'
            : 'Unable to open camera on this device.',
      });
    }
  }, [appendPickedAssets, isRecording, isSending, language, selectedImages.length]);

  // Gallery selection
  const handleOpenGallery = useCallback(async () => {
    if (isSending || isRecording) return;
    setNotice(null);

    const remaining = CONFIG.MAX_IMAGES - selectedImages.length;
    if (remaining <= 0) {
      setNotice({
        message:
          language === 'kn'
            ? `ಗರಿಷ್ಠ ${CONFIG.MAX_IMAGES} ಚಿತ್ರಗಳ ಮಿತಿ ತಲುಪಿದೆ.`
            : `Maximum of ${CONFIG.MAX_IMAGES} images already selected.`,
      });
      return;
    }

    try {
      if (Platform.OS !== 'web') {
        const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!perm.granted) {
          setNotice({
            message:
              language === 'kn'
                ? 'ಗ್ಯಾಲರಿ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಅನುಮತಿಸಿ.'
                : 'Photo library permission was denied. Please allow access in Settings.',
            canOpenSettings: true,
          });
          return;
        }
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsMultipleSelection: true,
        selectionLimit: remaining,
        quality: 0.82,
      });

      if (!result.canceled && result.assets?.length) {
        appendPickedAssets(result.assets);
      }
    } catch {
      setNotice({
        message:
          language === 'kn'
            ? 'ಗ್ಯಾಲರಿಯಿಂದ ಚಿತ್ರಗಳನ್ನು ಆಯ್ಕೆಮಾಡಲು ವಿಫಲವಾಗಿದೆ.'
            : 'Failed to open photo library.',
      });
    }
  }, [appendPickedAssets, isRecording, isSending, language, selectedImages.length]);

  const handleRemoveImage = useCallback((uri: string) => {
    setSelectedImages((prev) => prev.filter((item) => item.uri !== uri));
  }, []);

  const handleMicToggle = useCallback(async () => {
    if (isSending) return;
    setNotice(null);
    clearRecorderError();
    onStopPreviewAudio?.();

    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  }, [clearRecorderError, isRecording, isSending, onStopPreviewAudio, startRecording, stopRecording]);

  const handleDiscardVoice = useCallback(async () => {
    onStopPreviewAudio?.();
    await discardRecording();
  }, [discardRecording, onStopPreviewAudio]);

  const canSend =
    !isSending &&
    !isRecording &&
    (text.trim().length > 0 || selectedImages.length > 0 || !!recordedAudio);

  const handlePressSend = useCallback(async () => {
    if (!canSend) return;
    setNotice(null);
    onStopPreviewAudio?.();

    const snapshotText = text.trim();
    const snapshotImages = [...selectedImages];
    const snapshotAudio = recordedAudio;

    const accepted = await onSend({
      text: snapshotText,
      images: snapshotImages,
      audio: snapshotAudio,
    });

    if (accepted) {
      setText('');
      setSelectedImages([]);
      if (snapshotAudio) {
        // Keep the recorded audio file intact so the sent user bubble can play it
        consumeRecording();
      }
    }
  }, [canSend, consumeRecording, onSend, onStopPreviewAudio, recordedAudio, selectedImages, text]);

  return (
    <View style={styles.wrapper}>
      {/* Inline Notice / Permission Banner */}
      {notice && (
        <View style={styles.noticeBanner} accessibilityRole="alert">
          <Text style={styles.noticeText}>{notice.message}</Text>
          <View style={styles.noticeActions}>
            {notice.canOpenSettings && Platform.OS !== 'web' && (
              <TouchableOpacity
                onPress={() => Linking.openSettings().catch(() => {})}
                style={styles.settingsLink}
                accessibilityRole="button"
                accessibilityLabel="Open system settings"
              >
                <Text style={styles.settingsLinkText}>Settings</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity
              onPress={() => {
                setNotice(null);
                clearRecorderError();
              }}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              accessibilityRole="button"
              accessibilityLabel="Dismiss notice"
            >
              <Text style={styles.dismissNoticeText}>✕</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Selected Crop Photos Strip */}
      <ImagePreview
        images={selectedImages}
        onRemoveImage={handleRemoveImage}
        disabled={isSending}
        language={language}
      />

      {/* Active Recording Indicator Bar */}
      {isRecording && (
        <View style={styles.recordingBar} accessibilityLiveRegion="polite">
          <View style={styles.recordingInfo}>
            <Animated.View style={[styles.recordingDot, { opacity: pulseAnim }]} />
            <Text style={styles.recordingLabel}>
              {language === 'kn' ? 'ಧ್ವನಿ ರೆಕಾರ್ಡ್ ಆಗುತ್ತಿದೆ… ' : 'Recording voice… '}
              <Text style={styles.recordingTimer}>{formatDuration(elapsedSeconds)}</Text>
            </Text>
          </View>

          <TouchableOpacity
            onPress={handleMicToggle}
            style={styles.stopRecordBtn}
            accessibilityRole="button"
            accessibilityLabel="Stop voice recording"
          >
            <View style={styles.stopRecordSquare} />
            <Text style={styles.stopRecordText}>
              {language === 'kn' ? 'ನಿಲ್ಲಿಸಿ' : 'Stop'}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Recorded Voice Review Bar with Play Button + Discard Button */}
      {!isRecording && recordedAudio && (
        <View style={styles.recordedReviewBar}>
          <View style={styles.recordedLeft}>
            {/* Play / Stop Button to listen to the recorded voice note before sending */}
            <TouchableOpacity
              onPress={() => onTogglePreviewAudio?.(recordedAudio.uri)}
              disabled={isSending}
              style={[
                styles.previewPlayBtn,
                isPreviewPlaying && styles.previewPlayBtnActive,
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected: isPreviewPlaying }}
              accessibilityLabel={
                isPreviewPlaying
                  ? language === 'kn'
                    ? 'ಧ್ವನಿ ನಿಲ್ಲಿಸಿ'
                    : 'Stop listening to recorded voice note'
                  : language === 'kn'
                    ? 'ರೆಕಾರ್ಡ್ ಮಾಡಿದ ಧ್ವನಿ ಕೇಳಿ'
                    : 'Listen to recorded voice note'
              }
            >
              {isPreviewPlaying ? (
                <View style={styles.previewStopSquare} />
              ) : (
                <View style={styles.previewPlayTriangle} />
              )}
              <Text
                style={[
                  styles.previewPlayLabel,
                  isPreviewPlaying && styles.previewPlayLabelActive,
                ]}
              >
                {isPreviewPlaying
                  ? language === 'kn'
                    ? 'ನಿಲ್ಲಿಸಿ'
                    : 'Stop'
                  : language === 'kn'
                    ? 'ಕೇಳಿ'
                    : 'Play'}
              </Text>
            </TouchableOpacity>

            <Text style={styles.recordedText}>
              {language === 'kn'
                ? `ಧ್ವನಿ ಸಂದೇಶ (${formatDuration(recordedAudio.durationSeconds)})`
                : `Voice note (${formatDuration(recordedAudio.durationSeconds)})`}
            </Text>
          </View>

          <TouchableOpacity
            onPress={handleDiscardVoice}
            disabled={isSending}
            style={styles.discardAudioBtn}
            accessibilityRole="button"
            accessibilityLabel="Discard recorded voice clip"
          >
            <Text style={styles.discardAudioText}>
              {language === 'kn' ? 'ಅಳಿಸಿ ✕' : 'Discard ✕'}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Main Bottom Input Row */}
      <View style={styles.inputRow}>
        {/* Camera Button */}
        <TouchableOpacity
          onPress={handleOpenCamera}
          disabled={isSending || isRecording}
          style={[
            styles.iconButton,
            (isSending || isRecording) && styles.disabledControl,
          ]}
          accessibilityRole="button"
          accessibilityLabel="Take a photo of rice crop leaves"
        >
          <View style={styles.cameraIcon}>
            <View style={styles.cameraTopBump} />
            <View style={styles.cameraLens} />
          </View>
        </TouchableOpacity>

        {/* Gallery Button */}
        <TouchableOpacity
          onPress={handleOpenGallery}
          disabled={isSending || isRecording}
          style={[
            styles.iconButton,
            (isSending || isRecording) && styles.disabledControl,
          ]}
          accessibilityRole="button"
          accessibilityLabel="Select crop photos from gallery"
        >
          <View style={styles.galleryIcon}>
            <View style={styles.gallerySun} />
            <View style={styles.galleryMountain} />
          </View>
        </TouchableOpacity>

        {/* Expanding Multiline Text Input */}
        <View style={styles.inputContainer}>
          <TextInput
            value={text}
            onChangeText={setText}
            editable={!isSending && !isRecording}
            multiline
            maxLength={1500}
            placeholder={
              language === 'kn'
                ? 'ರೋಗಲಕ್ಷಣಗಳನ್ನು ವಿವರಿಸಿ ಅಥವಾ ಮೈಕ್ ಒತ್ತಿರಿ…'
                : 'Describe symptoms or tap the mic...'
            }
            placeholderTextColor={COLORS.textMuted}
            style={styles.textInput}
            accessibilityLabel="Message text input"
          />
        </View>

        {/* Microphone Button (Tap to Start / Tap to Stop) */}
        <TouchableOpacity
          onPress={handleMicToggle}
          disabled={isSending}
          style={[
            styles.micButton,
            isRecording && styles.micButtonActive,
            isSending && styles.disabledControl,
          ]}
          accessibilityRole="button"
          accessibilityState={{ selected: isRecording }}
          accessibilityLabel={
            isRecording ? 'Stop voice recording' : 'Start voice recording'
          }
        >
          <View style={styles.micGraphic}>
            <View
              style={[
                styles.micCapsule,
                isRecording && styles.micCapsuleActive,
              ]}
            />
            <View
              style={[
                styles.micCradle,
                isRecording && styles.micCradleActive,
              ]}
            />
            <View
              style={[
                styles.micStem,
                isRecording && styles.micStemActive,
              ]}
            />
          </View>
        </TouchableOpacity>

        {/* Send Button */}
        <TouchableOpacity
          onPress={handlePressSend}
          disabled={!canSend}
          style={[styles.sendButton, !canSend && styles.sendButtonDisabled]}
          accessibilityRole="button"
          accessibilityState={{ disabled: !canSend, busy: isSending }}
          accessibilityLabel={
            language === 'kn'
              ? 'ಲಿವಿಯಾ ಎಐ ಗೆ ಸಂದೇಶ ಕಳುಹಿಸಿ'
              : 'Send message to Livia AI'
          }
        >
          {isSending ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <View style={styles.sendArrowContainer}>
              <View style={styles.sendArrowShaft} />
              <View style={styles.sendArrowHead} />
            </View>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    ...SHADOWS.floating,
  },
  noticeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.warningBg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs + 3,
    borderBottomWidth: 1,
    borderBottomColor: '#FFE0B2',
  },
  noticeText: {
    fontSize: 12,
    color: COLORS.warningAmber,
    fontWeight: '600',
    flex: 1,
    marginRight: SPACING.sm,
  },
  noticeActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  settingsLink: {
    backgroundColor: COLORS.warningAmber,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: RADIUS.xs,
  },
  settingsLinkText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  dismissNoticeText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.warningAmber,
  },
  recordingBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.errorBg,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#FFCDD2',
  },
  recordingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  recordingDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.recordingRed,
  },
  recordingLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.recordingRed,
  },
  recordingTimer: {
    fontVariant: ['tabular-nums'],
    fontWeight: '700',
  },
  stopRecordBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.recordingRed,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    gap: 6,
  },
  stopRecordSquare: {
    width: 8,
    height: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 1.5,
  },
  stopRecordText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  recordedReviewBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.primaryLight,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs + 3,
    borderBottomWidth: 1,
    borderBottomColor: '#C8E6C9',
  },
  recordedLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  previewPlayBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: COLORS.primary,
    borderRadius: RADIUS.pill,
    paddingHorizontal: 10,
    paddingVertical: 4,
    gap: 5,
  },
  previewPlayBtnActive: {
    backgroundColor: COLORS.primary,
  },
  previewPlayTriangle: {
    width: 0,
    height: 0,
    borderTopWidth: 4.5,
    borderBottomWidth: 4.5,
    borderLeftWidth: 7,
    borderTopColor: 'transparent',
    borderBottomColor: 'transparent',
    borderLeftColor: COLORS.primary,
    marginLeft: 1,
  },
  previewStopSquare: {
    width: 7,
    height: 7,
    borderRadius: 1,
    backgroundColor: '#FFFFFF',
  },
  previewPlayLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
  },
  previewPlayLabelActive: {
    color: '#FFFFFF',
  },
  recordedText: {
    fontSize: 12.5,
    fontWeight: '600',
    color: COLORS.primary,
  },
  discardAudioBtn: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(198, 40, 40, 0.1)',
  },
  discardAudioText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.errorRed,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: SPACING.sm + 2,
    paddingVertical: SPACING.sm,
    gap: 6,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.surfaceSubtle,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  disabledControl: {
    opacity: 0.45,
  },
  cameraIcon: {
    width: 18,
    height: 14,
    borderRadius: 3,
    borderWidth: 1.8,
    borderColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
  },
  cameraTopBump: {
    position: 'absolute',
    top: -4,
    width: 8,
    height: 3,
    backgroundColor: COLORS.primary,
    borderTopLeftRadius: 1.5,
    borderTopRightRadius: 1.5,
  },
  cameraLens: {
    width: 6,
    height: 6,
    borderRadius: 3,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  galleryIcon: {
    width: 17,
    height: 15,
    borderRadius: 3,
    borderWidth: 1.8,
    borderColor: COLORS.primary,
    overflow: 'hidden',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  gallerySun: {
    position: 'absolute',
    top: 2,
    left: 2,
    width: 3.5,
    height: 3.5,
    borderRadius: 2,
    backgroundColor: COLORS.accent,
  },
  galleryMountain: {
    width: 12,
    height: 8,
    backgroundColor: COLORS.primary,
    transform: [{ rotate: '45deg' }],
    marginBottom: -5,
    marginRight: -3,
  },
  inputContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderRadius: RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: SPACING.md,
    paddingVertical: Platform.OS === 'ios' ? 9 : 6,
    minHeight: 40,
    maxHeight: 116,
    justifyContent: 'center',
  },
  textInput: {
    fontSize: 15,
    color: COLORS.textPrimary,
    maxHeight: 96,
    paddingTop: 0,
    paddingBottom: 0,
  },
  micButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primaryLight,
    borderWidth: 1,
    borderColor: '#C8E6C9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  micButtonActive: {
    backgroundColor: COLORS.recordingRed,
    borderColor: COLORS.recordingRed,
  },
  micGraphic: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  micCapsule: {
    width: 8,
    height: 12,
    borderRadius: 4,
    backgroundColor: COLORS.primary,
  },
  micCapsuleActive: {
    backgroundColor: '#FFFFFF',
  },
  micCradle: {
    width: 14,
    height: 7,
    borderBottomLeftRadius: 7,
    borderBottomRightRadius: 7,
    borderWidth: 1.8,
    borderTopWidth: 0,
    borderColor: COLORS.primary,
    marginTop: -4,
  },
  micCradleActive: {
    borderColor: '#FFFFFF',
  },
  micStem: {
    width: 2,
    height: 3,
    backgroundColor: COLORS.primary,
  },
  micStemActive: {
    backgroundColor: '#FFFFFF',
  },
  sendButton: {
    width: 42,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: COLORS.border,
  },
  sendArrowContainer: {
    width: 16,
    height: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendArrowShaft: {
    width: 2.2,
    height: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 1,
  },
  sendArrowHead: {
    position: 'absolute',
    top: 2,
    width: 8,
    height: 8,
    borderTopWidth: 2.2,
    borderRightWidth: 2.2,
    borderColor: '#FFFFFF',
    transform: [{ rotate: '-45deg' }],
  },
});
