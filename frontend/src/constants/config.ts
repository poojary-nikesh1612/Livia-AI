// src/constants/config.ts
import { LanguageCode } from '../types/chat';

export const CONFIG = {
  API_BASE_URL: (
    process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'
  ).replace(/\/+$/, ''),
  USER_ID: (process.env.EXPO_PUBLIC_USER_ID ?? '').trim(),
  DEFAULT_LANGUAGE: 'en' as LanguageCode,
  MAX_IMAGES: 5,
  REQUEST_TIMEOUT_MS: 60000,
  // Allow long-running multi-step AI responses up to ten minutes.
  CHAT_REQUEST_TIMEOUT_MS: 10 * 60 * 1000,
  AUTO_PLAY_ASSISTANT_AUDIO: true,
};

const UUID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/**
 * Validates whether a string is a well-formed UUID.
 */
export const isValidUuid = (value: string): boolean => {
  return UUID_REGEX.test(value.trim());
};

/**
 * Generates a RFC4122 v4 UUID using crypto.getRandomValues when available,
 * with a safe fallback so no native module crash can occur on any platform.
 */
export const generateUuid = (): string => {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return globalThis.crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const random = (Math.random() * 16) | 0;
    const value = char === 'x' ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
};
