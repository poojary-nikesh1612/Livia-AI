// src/utils/audio.ts
import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';

const BASE64_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

/**
 * Converts an ArrayBuffer (e.g. from POST /voice/stream) into a Base64 string.
 * Safe for binary payloads of any size on React Native (Hermes) and Web.
 */
export const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
  const bytes = new Uint8Array(buffer);
  const len = bytes.length;
  if (len === 0) return '';

  let result = '';
  for (let i = 0; i < len; i += 3) {
    const b1 = bytes[i];
    const b2 = i + 1 < len ? bytes[i + 1] : 0;
    const b3 = i + 2 < len ? bytes[i + 2] : 0;

    const triplet = (b1 << 16) | (b2 << 8) | b3;

    result += BASE64_CHARS[(triplet >> 18) & 0x3f];
    result += BASE64_CHARS[(triplet >> 12) & 0x3f];
    result += i + 1 < len ? BASE64_CHARS[(triplet >> 6) & 0x3f] : '=';
    result += i + 2 < len ? BASE64_CHARS[triplet & 0x3f] : '=';
  }

  return result;
};

/**
 * Strips any `data:audio/...;base64,` prefix from a Base64 string.
 */
export const stripAudioBase64Prefix = (base64: string): string => {
  return base64.replace(/^data:[^;]+;base64,/i, '').trim();
};

/**
 * Converts a recorded audio URI into a raw Base64 string for POST /chat.
 */
export const uriToAudioBase64 = async (uri: string): Promise<string> => {
  if (!uri) {
    throw new Error('Recording URI is empty.');
  }

  if (uri.startsWith('data:')) {
    return stripAudioBase64Prefix(uri);
  }

  if (Platform.OS === 'web') {
    const response = await fetch(uri);
    const arrayBuffer = await response.arrayBuffer();
    return arrayBufferToBase64(arrayBuffer);
  }

  const base64 = await FileSystem.readAsStringAsync(uri, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return stripAudioBase64Prefix(base64);
};

/**
 * Converts a raw Base64 MP3 string into a playable URI.
 * - On Web: returns a `data:audio/mpeg;base64,...` URI.
 * - On Native (Android/iOS): writes a temporary `.mp3` file in cacheDirectory and returns its `file://` URI.
 */
export const base64ToPlayableUri = async (
  base64Audio: string,
  cacheKey: string
): Promise<string> => {
  const cleanBase64 = stripAudioBase64Prefix(base64Audio);
  if (!cleanBase64) {
    throw new Error('Audio data is empty.');
  }

  if (Platform.OS === 'web' || !FileSystem.cacheDirectory) {
    return `data:audio/mpeg;base64,${cleanBase64}`;
  }

  const safeKey = cacheKey.replace(/[^a-zA-Z0-9_-]/g, '_');
  const fileUri = `${FileSystem.cacheDirectory}livia_audio_${safeKey}.mp3`;

  await FileSystem.writeAsStringAsync(fileUri, cleanBase64, {
    encoding: FileSystem.EncodingType.Base64,
  });

  return fileUri;
};

/**
 * Deletes a temporary audio file when it is no longer needed on native platforms.
 */
export const deleteTempAudioFile = async (uri?: string | null): Promise<void> => {
  if (!uri || Platform.OS === 'web') return;
  if (uri.startsWith('file://')) {
    try {
      await FileSystem.deleteAsync(uri, { idempotent: true });
    } catch {
      // Ignore cleanup errors
    }
  }
};

/**
 * Formats elapsed seconds as M:SS (e.g. 0:07, 1:24).
 */
export const formatDuration = (seconds: number): string => {
  const total = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
};

