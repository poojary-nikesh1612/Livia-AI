// src/hooks/useAudioPlayer.ts
import { useCallback, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import { createAudioPlayer, setAudioModeAsync, AudioPlayer, AudioStatus } from 'expo-audio';
import { streamVoiceReplay } from '../api/chatService';
import { ChatMessage, LanguageCode } from '../types/chat';
import { base64ToPlayableUri, deleteTempAudioFile } from '../utils/audio';

export interface UseAudioPlayerReturn {
  playingMessageId: string | null;
  loadingMessageId: string | null;
  errorByMessageId: Record<string, string>;
  toggleMessageAudio: (
    message: ChatMessage,
    language: LanguageCode,
    onCacheAudio?: (messageId: string, audioBase64: string, audioUri: string) => void
  ) => Promise<void>;
  toggleRawUriAudio: (id: string, uri: string) => Promise<void>;
  playImmediateAudio: (
    messageId: string,
    audioBase64: string,
    onCacheUri?: (messageId: string, audioUri: string) => void
  ) => Promise<void>;
  stopPlayback: () => void;
}

export const useAudioPlayer = (): UseAudioPlayerReturn => {
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  const [loadingMessageId, setLoadingMessageId] = useState<string | null>(null);
  const [errorByMessageId, setErrorByMessageId] = useState<Record<string, string>>({});

  const activePlayerRef = useRef<AudioPlayer | null>(null);
  const createdTempUrisRef = useRef<Set<string>>(new Set());

  const releaseActivePlayer = useCallback(() => {
    if (activePlayerRef.current) {
      try {
        activePlayerRef.current.pause();
        activePlayerRef.current.remove();
      } catch {
        // Ignore cleanup errors
      }
      activePlayerRef.current = null;
    }
    setPlayingMessageId(null);
  }, []);

  useEffect(() => {
    if (Platform.OS !== 'web') {
      setAudioModeAsync({
        playsInSilentMode: true,
        allowsRecording: false,
      }).catch(() => {});
    }

    return () => {
      releaseActivePlayer();
      const uris = Array.from(createdTempUrisRef.current);
      createdTempUrisRef.current.clear();
      uris.forEach((uri) => {
        deleteTempAudioFile(uri).catch(() => {});
      });
    };
  }, [releaseActivePlayer]);

  const startPlayerWithUri = useCallback(
    async (messageId: string, playableUri: string) => {
      releaseActivePlayer();

      const player = createAudioPlayer(playableUri);
      activePlayerRef.current = player;
      setPlayingMessageId(messageId);

      player.addListener('playbackStatusUpdate', (status: AudioStatus) => {
        if (
          status.didJustFinish ||
          (!status.playing &&
            status.currentTime > 0 &&
            status.duration > 0 &&
            status.currentTime >= status.duration - 0.15)
        ) {
          if (activePlayerRef.current === player) {
            releaseActivePlayer();
          }
        }
      });

      player.play();
    },
    [releaseActivePlayer]
  );

  const toggleRawUriAudio = useCallback(
    async (id: string, uri: string) => {
      if (!uri) return;
      if (playingMessageId === id) {
        releaseActivePlayer();
        return;
      }
      try {
        await startPlayerWithUri(id, uri);
      } catch {
        setPlayingMessageId(null);
      }
    },
    [playingMessageId, releaseActivePlayer, startPlayerWithUri]
  );

  const playImmediateAudio = useCallback(
    async (
      messageId: string,
      audioBase64: string,
      onCacheUri?: (msgId: string, audioUri: string) => void
    ) => {
      if (!audioBase64 || !audioBase64.trim()) return;

      setErrorByMessageId((prev) => {
        const next = { ...prev };
        delete next[messageId];
        return next;
      });

      try {
        const playableUri = await base64ToPlayableUri(audioBase64, messageId);
        if (playableUri.startsWith('file://')) {
          createdTempUrisRef.current.add(playableUri);
        }
        onCacheUri?.(messageId, playableUri);
        await startPlayerWithUri(messageId, playableUri);
      } catch {
        setPlayingMessageId(null);
        setErrorByMessageId((prev) => ({
          ...prev,
          [messageId]: 'Tap to retry audio playback',
        }));
      }
    },
    [startPlayerWithUri]
  );

  const toggleMessageAudio = useCallback(
    async (
      message: ChatMessage,
      language: LanguageCode,
      onCacheAudio?: (messageId: string, audioBase64: string, audioUri: string) => void
    ) => {
      const msgId = message.id;

      // If this message is already playing, stop it
      if (playingMessageId === msgId) {
        releaseActivePlayer();
        return;
      }

      // Stop any other playing audio first
      releaseActivePlayer();

      setErrorByMessageId((prev) => {
        const next = { ...prev };
        delete next[msgId];
        return next;
      });

      setLoadingMessageId(msgId);

      try {
        const messageLanguage = message.languageCode ?? language;
        let playableUri = message.audioUri;
        let audioBase64 = message.audioBase64;

        if (!playableUri) {
          if (!audioBase64) {
            if (!message.text.trim()) {
              throw new Error('No audio available for this message.');
            }
            audioBase64 = await streamVoiceReplay({
              text: message.text,
              language_code: messageLanguage,
            });
          }

          playableUri = await base64ToPlayableUri(audioBase64, `${msgId}_${messageLanguage}`);
          if (playableUri.startsWith('file://')) {
            createdTempUrisRef.current.add(playableUri);
          }
          onCacheAudio?.(msgId, audioBase64, playableUri);
        }

        setLoadingMessageId(null);
        await startPlayerWithUri(msgId, playableUri);
      } catch (err) {
        setLoadingMessageId(null);
        setPlayingMessageId(null);
        const errMsg =
          err && typeof err === 'object' && 'message' in err && typeof err.message === 'string'
            ? err.message
            : 'Audio unavailable. Tap to retry.';
        setErrorByMessageId((prev) => ({
          ...prev,
          [msgId]: errMsg,
        }));
      }
    },
    [playingMessageId, releaseActivePlayer, startPlayerWithUri]
  );

  return {
    playingMessageId,
    loadingMessageId,
    errorByMessageId,
    toggleMessageAudio,
    toggleRawUriAudio,
    playImmediateAudio,
    stopPlayback: releaseActivePlayer,
  };
};
