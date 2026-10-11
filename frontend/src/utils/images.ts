// src/utils/images.ts
import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import { SelectedImage } from '../types/chat';

const MAX_FILE_SIZE_BYTES = 12 * 1024 * 1024; // 12 MB safety ceiling per image

/**
 * Strips any `data:image/...;base64,` prefix so backend receives raw Base64 bytes.
 */
export const stripBase64Prefix = (base64: string): string => {
  return base64.replace(/^data:[^;]+;base64,/i, '').trim();
};

/**
 * Infers a MIME type from a URI or file name.
 */
export const detectImageMimeType = (uri: string, providedMime?: string | null): string => {
  if (providedMime && providedMime.startsWith('image/')) {
    return providedMime.toLowerCase();
  }
  const clean = uri.split('?')[0].toLowerCase();
  if (clean.endsWith('.png')) return 'image/png';
  if (clean.endsWith('.webp')) return 'image/webp';
  return 'image/jpeg';
};

/**
 * Validates whether a picked image asset is acceptable.
 */
export const validateSelectedImage = (
  image: SelectedImage
): { valid: boolean; reason?: string } => {
  if (!image.uri) {
    return { valid: false, reason: 'Selected image has no readable URI.' };
  }
  if (image.fileSize && image.fileSize > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      reason: 'One of the selected images exceeds the 12 MB size limit.',
    };
  }
  return { valid: true };
};

/**
 * Converts a local image URI (or SelectedImage) into a raw Base64 string (without data: prefix)
 * across Android, iOS, and Web.
 */
export const uriToBase64 = async (imageOrUri: SelectedImage | string): Promise<string> => {
  const uri = typeof imageOrUri === 'string' ? imageOrUri : imageOrUri.uri;
  const cachedBase64 = typeof imageOrUri === 'string' ? undefined : imageOrUri.base64;

  if (cachedBase64 && cachedBase64.trim().length > 0) {
    return stripBase64Prefix(cachedBase64);
  }

  if (!uri) {
    throw new Error('Image URI is empty.');
  }

  if (uri.startsWith('data:')) {
    return stripBase64Prefix(uri);
  }

  if (Platform.OS === 'web') {
    const response = await fetch(uri);
    const blob = await response.blob();
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          resolve(stripBase64Prefix(reader.result));
        } else {
          reject(new Error('Failed to read image on web.'));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read image blob.'));
      reader.readAsDataURL(blob);
    });
  }

  const base64 = await FileSystem.readAsStringAsync(uri, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return stripBase64Prefix(base64);
};

/**
 * Converts an array of SelectedImage items into raw Base64 strings for POST /chat.
 */
export const convertImagesToBase64 = async (images: SelectedImage[]): Promise<string[]> => {
  if (!images || images.length === 0) return [];
  const results = await Promise.all(images.map((img) => uriToBase64(img)));
  return results.filter((b64) => b64.length > 0);
};
