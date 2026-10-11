// src/api/chatService.ts
import client, { normalizeApiError } from './client';
import {
  ChatHistoryMessage,
  ChatMessage,
  ChatRequest,
  ChatResponse,
  VoiceReplayRequest,
} from '../types/chat';
import { arrayBufferToBase64 } from '../utils/audio';
import { CONFIG } from '../constants/config';

let historyIdCounter = 0;
const nextHistoryId = (index: number): string =>
  `hist-${Date.now()}-${index}-${++historyIdCounter}`;

/**
 * Normalizes raw history items from GET /chat/history into frontend ChatMessage objects.
 * Supports both actual backend schema ({ role, display_content, images }) and extended variants.
 */
export const normalizeHistoryMessages = (rawList: unknown): ChatMessage[] => {
  if (!Array.isArray(rawList)) {
    return [];
  }

  return rawList
    .map((item: unknown, idx: number): ChatMessage | null => {
      if (!item || typeof item !== 'object') return null;
      const record = item as ChatHistoryMessage;

      const role = record.role === 'user' ? 'user' : 'assistant';
      const text = (
        record.display_content ??
        record.content ??
        record.text ??
        ''
      ).trim();

      const rawImages =
        record.images ?? record.image_urls ?? record.images_base64 ?? [];
      const images = Array.isArray(rawImages)
        ? rawImages
            .filter((img): img is string => typeof img === 'string' && img.trim().length > 0)
            .map((img) => {
              const trimmed = img.trim();
              if (
                trimmed.startsWith('http://') ||
                trimmed.startsWith('https://') ||
                trimmed.startsWith('file://') ||
                trimmed.startsWith('data:image/') ||
                trimmed.startsWith('blob:')
              ) {
                return trimmed;
              }
              return `data:image/jpeg;base64,${trimmed}`;
            })
        : [];

      const timestamp = record.timestamp ?? record.created_at;

      return {
        id: nextHistoryId(idx),
        role,
        text,
        languageCode:
          record.language_code === 'en' || record.language_code === 'kn'
            ? record.language_code
            : undefined,
        images,
        audioBase64:
          typeof record.audio_base64 === 'string' && record.audio_base64.trim()
            ? record.audio_base64.trim()
            : undefined,
        timestamp,
        status: 'sent',
      };
    })
    .filter((msg): msg is ChatMessage => msg !== null);
};

/**
 * GET /chat/history?user_id={user_id}
 */
export const fetchChatHistory = async (userId: string): Promise<ChatMessage[]> => {
  try {
    const response = await client.get<unknown>('/chat/history', {
      params: { user_id: userId.trim() },
    });
    return normalizeHistoryMessages(response.data);
  } catch (err) {
    throw normalizeApiError(err);
  }
};

/**
 * POST /chat
 */
export const postChatMessage = async (payload: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await client.post<ChatResponse>('/chat', payload, {
      timeout: CONFIG.CHAT_REQUEST_TIMEOUT_MS,
    });
    const data = response.data;

    if (!data || typeof data !== 'object' || typeof data.ai_response_text !== 'string') {
      throw new Error('Received an invalid response format from the diagnostic server.');
    }

    return {
      thread_id: data.thread_id || payload.thread_id,
      ai_response_text: data.ai_response_text,
      ai_response_audio_base64: data.ai_response_audio_base64 ?? '',
      is_flow_complete: Boolean(data.is_flow_complete),
    };
  } catch (err) {
    throw normalizeApiError(err);
  }
};

/**
 * POST /voice/stream
 * Requests synthesized MP3 bytes for historical message playback and converts them to Base64.
 */
export const streamVoiceReplay = async (payload: VoiceReplayRequest): Promise<string> => {
  try {
    const response = await client.post<ArrayBuffer>('/voice/stream', payload, {
      responseType: 'arraybuffer',
      headers: {
        Accept: 'audio/mpeg',
      },
    });

    const base64Audio = arrayBufferToBase64(response.data);
    if (!base64Audio) {
      throw new Error('Received empty audio stream from server.');
    }
    return base64Audio;
  } catch (err) {
    throw normalizeApiError(err);
  }
};
