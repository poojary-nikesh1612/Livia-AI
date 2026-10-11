// src/types/chat.ts

export type LanguageCode = 'en' | 'kn';

export type MessageRole = 'user' | 'assistant';

export type DeliveryStatus = 'sending' | 'sent' | 'failed';

export interface SelectedImage {
  uri: string;
  mimeType?: string;
  fileName?: string;
  width?: number;
  height?: number;
  fileSize?: number;
  base64?: string;
}

export interface AudioRecordingResult {
  uri: string;
  durationSeconds: number;
  mimeType: string;
  base64?: string;
}

export interface ChatRequest {
  user_id: string;
  thread_id: string;
  audio_base64: string;
  text: string;
  language_code: LanguageCode;
  images: string[];
}

export interface ChatResponse {
  thread_id: string;
  ai_response_text: string;
  ai_response_audio_base64: string;
  is_flow_complete: boolean;
}

export interface VoiceReplayRequest {
  text: string;
  language_code: LanguageCode;
}

export interface ChatHistoryMessage {
  user_id?: string;
  thread_id?: string;
  role: MessageRole;
  language_code?: LanguageCode;
  display_content?: string;
  content?: string;
  text?: string;
  english_content?: string;
  images?: string[];
  image_urls?: string[];
  images_base64?: string[];
  audio_base64?: string;
  timestamp?: string;
  created_at?: string;
}

export interface RetryPayload {
  text: string;
  selectedImages: SelectedImage[];
  audioBase64: string;
  audioDurationSeconds?: number;
  languageCode: LanguageCode;
  threadId: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text: string;
  languageCode?: LanguageCode;
  images?: string[];
  hasVoiceInput?: boolean;
  voiceDurationSeconds?: number;
  audioBase64?: string;
  audioUri?: string;
  timestamp?: string;
  status?: DeliveryStatus;
  errorText?: string;
  retryPayload?: RetryPayload;
}

export interface ApiError {
  message: string;
  statusCode?: number;
  isNetworkError?: boolean;
  isTimeout?: boolean;
}
