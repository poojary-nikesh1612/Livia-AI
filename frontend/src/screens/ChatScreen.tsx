// src/screens/ChatScreen.tsx
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { fetchChatHistory, postChatMessage } from '../api/chatService';
import { ChatBubble } from '../components/ChatBubble';
import { EmptyState } from '../components/EmptyState';
import { Header } from '../components/Header';
import { InputBar, InputSubmission } from '../components/InputBar';
import { TypingIndicator } from '../components/TypingIndicator';
import { CONFIG, generateUuid, isValidUuid } from '../constants/config';
import { COLORS, RADIUS, SPACING, TYPOGRAPHY } from '../constants/theme';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import { ChatMessage, LanguageCode, RetryPayload } from '../types/chat';
import { convertImagesToBase64 } from '../utils/images';

let messageSeq = 0;
const createMessageId = (prefix = 'msg'): string =>
  `${prefix}-${Date.now()}-${++messageSeq}`;

const DRAFT_AUDIO_PREVIEW_ID = '__draft_voice_preview__';

export default function ChatScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [language, setLanguage] = useState<LanguageCode>(CONFIG.DEFAULT_LANGUAGE);

  // LangGraph Thread Management State
  const [, setCurrentThreadId] = useState<string | null>(null);
  const [, setIsFlowComplete] = useState<boolean>(true);
  const [isSending, setIsSending] = useState<boolean>(false);

  // History Loading & Error State
  const [historyLoading, setHistoryLoading] = useState<boolean>(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [prefillText, setPrefillText] = useState<string>('');

  // Synchronous lock to prevent duplicate concurrent submissions
  const isSendingRef = useRef<boolean>(false);
  const currentThreadIdRef = useRef<string | null>(null);
  const isFlowCompleteRef = useRef<boolean>(true);
  const flatListRef = useRef<FlatList<ChatMessage>>(null);

  const {
    playingMessageId,
    loadingMessageId,
    errorByMessageId,
    toggleMessageAudio,
    toggleRawUriAudio,
    playImmediateAudio,
    stopPlayback,
  } = useAudioPlayer();

  const updateThreadState = useCallback((threadId: string | null, flowComplete: boolean) => {
    currentThreadIdRef.current = threadId;
    isFlowCompleteRef.current = flowComplete;
    setCurrentThreadId(threadId);
    setIsFlowComplete(flowComplete);
  }, []);

  const scrollToBottom = useCallback((animated = true) => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated });
    }, 120);
  }, []);

  // ── Load Conversation History on Mount ─────────────────────────────────────
  const loadHistory = useCallback(async () => {
    if (!CONFIG.USER_ID || !isValidUuid(CONFIG.USER_ID)) {
      setHistoryError(
        'EXPO_PUBLIC_USER_ID is missing or invalid in your .env file. Please configure a valid PostgreSQL User UUID.'
      );
      setHistoryLoading(false);
      return;
    }

    setHistoryError(null);
    setHistoryLoading(true);

    try {
      const historyMessages = await fetchChatHistory(CONFIG.USER_ID);
      setMessages(historyMessages);
      updateThreadState(null, true);
      if (historyMessages.length > 0) {
        scrollToBottom(false);
      }
    } catch (err) {
      const msg =
        err && typeof err === 'object' && 'message' in err && typeof err.message === 'string'
          ? err.message
          : 'Failed to load conversation history.';
      setHistoryError(msg);
    } finally {
      setHistoryLoading(false);
    }
  }, [scrollToBottom, updateThreadState]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // ── Cache synthesized audio URI/Base64 on message item ─────────────────────
  const handleCacheAudio = useCallback(
    (messageId: string, audioBase64: string, audioUri: string) => {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, audioBase64: audioBase64 || m.audioBase64, audioUri }
            : m
        )
      );
    },
    []
  );

  // ── Core API execution for both fresh sends and retries ────────────────────
  const executeChatRequest = useCallback(
    async (userMessageId: string, payload: RetryPayload) => {
      try {
        const base64Images = await convertImagesToBase64(payload.selectedImages);

        const response = await postChatMessage({
          user_id: CONFIG.USER_ID,
          thread_id: payload.threadId,
          audio_base64: payload.audioBase64,
          text: payload.text,
          language_code: payload.languageCode,
          images: base64Images,
        });

        const resolvedThreadId = response.thread_id || payload.threadId;
        const resolvedFlowComplete = Boolean(response.is_flow_complete);
        updateThreadState(resolvedThreadId, resolvedFlowComplete);

        const assistantMsgId = createMessageId('ai');
        const assistantMessage: ChatMessage = {
          id: assistantMsgId,
          role: 'assistant',
          text: response.ai_response_text,
          languageCode: payload.languageCode,
          audioBase64: response.ai_response_audio_base64 || undefined,
          timestamp: new Date().toISOString(),
          status: 'sent',
        };

        setMessages((prev) =>
          prev
            .map((m) =>
              m.id === userMessageId
                ? { ...m, status: 'sent' as const, errorText: undefined }
                : m
            )
            .concat(assistantMessage)
        );

        scrollToBottom(true);

        if (
          CONFIG.AUTO_PLAY_ASSISTANT_AUDIO &&
          response.ai_response_audio_base64 &&
          response.ai_response_audio_base64.trim().length > 0
        ) {
          playImmediateAudio(
            assistantMsgId,
            response.ai_response_audio_base64,
            (msgId, uri) => handleCacheAudio(msgId, response.ai_response_audio_base64, uri)
          ).catch(() => {});
        }
      } catch (err) {
        const errMsg =
          err && typeof err === 'object' && 'message' in err && typeof err.message === 'string'
            ? err.message
            : payload.languageCode === 'kn'
              ? 'ಲಿವಿಯಾ ಎಐ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'
              : 'Could not reach Livia AI. Tap Retry to try again.';

        setMessages((prev) =>
          prev.map((m) =>
            m.id === userMessageId
              ? {
                  ...m,
                  status: 'failed' as const,
                  errorText: errMsg,
                  retryPayload: payload,
                }
              : m
          )
        );
        scrollToBottom(true);
      } finally {
        isSendingRef.current = false;
        setIsSending(false);
      }
    },
    [handleCacheAudio, playImmediateAudio, scrollToBottom, updateThreadState]
  );

  // ── Handle New Message Submission from InputBar ────────────────────────────
  const handleSendSubmission = useCallback(
    async ({ text, images, audio }: InputSubmission): Promise<boolean> => {
      if (isSendingRef.current) {
        return false;
      }

      if (!CONFIG.USER_ID || !isValidUuid(CONFIG.USER_ID)) {
        setHistoryError(
          'Valid EXPO_PUBLIC_USER_ID is required before sending messages.'
        );
        return false;
      }

      const hasText = text.trim().length > 0;
      const hasImages = images.length > 0;
      const hasAudio = !!audio?.base64;

      if (!hasText && !hasImages && !hasAudio) {
        return false;
      }

      isSendingRef.current = true;
      setIsSending(true);
      stopPlayback();

      // Resolve LangGraph thread ID:
      // Reuse active thread if flow is incomplete; otherwise create a new UUID.
      let activeThreadId = currentThreadIdRef.current;
      if (!activeThreadId || isFlowCompleteRef.current) {
        activeThreadId = generateUuid();
        updateThreadState(activeThreadId, false);
      }

      const userMsgId = createMessageId('user');
      const retryPayload: RetryPayload = {
        text: text.trim(),
        selectedImages: images,
        audioBase64: audio?.base64 ?? '',
        audioDurationSeconds: audio?.durationSeconds,
        languageCode: language,
        threadId: activeThreadId,
      };

      const optimisticUserMessage: ChatMessage = {
        id: userMsgId,
        role: 'user',
        text: text.trim(),
        languageCode: language,
        images: images.map((img) => img.uri),
        hasVoiceInput: hasAudio,
        voiceDurationSeconds: audio?.durationSeconds,
        audioUri: audio?.uri,
        audioBase64: audio?.base64,
        timestamp: new Date().toISOString(),
        status: 'sent',
        retryPayload,
      };

      setMessages((prev) => [...prev, optimisticUserMessage]);
      scrollToBottom(true);

      executeChatRequest(userMsgId, retryPayload);
      return true;
    },
    [executeChatRequest, language, scrollToBottom, stopPlayback, updateThreadState]
  );

  // ── Handle Retry on a Failed User Bubble ───────────────────────────────────
  const handleRetryMessage = useCallback(
    (failedMessage: ChatMessage) => {
      if (isSendingRef.current || !failedMessage.retryPayload) return;

      isSendingRef.current = true;
      setIsSending(true);
      stopPlayback();

      setMessages((prev) =>
        prev.map((m) =>
          m.id === failedMessage.id
            ? { ...m, status: 'sent' as const, errorText: undefined }
            : m
        )
      );

      executeChatRequest(failedMessage.id, failedMessage.retryPayload);
    },
    [executeChatRequest, stopPlayback]
  );

  const renderMessageItem = useCallback(
    ({ item }: { item: ChatMessage }) => (
      <ChatBubble
        message={item}
        isUser={item.role === 'user'}
        language={language}
        isPlayingAudio={playingMessageId === item.id}
        isLoadingAudio={loadingMessageId === item.id}
        audioErrorText={errorByMessageId[item.id]}
        onPressAudio={() => toggleMessageAudio(item, language, handleCacheAudio)}
        onRetrySend={handleRetryMessage}
      />
    ),
    [
      errorByMessageId,
      handleCacheAudio,
      handleRetryMessage,
      language,
      loadingMessageId,
      playingMessageId,
      toggleMessageAudio,
    ]
  );

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right', 'bottom']}>
      <Header
        language={language}
        onChangeLanguage={setLanguage}
      />

      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        {/* Non-blocking History Error Banner */}
        {historyError && !historyLoading && (
          <View style={styles.errorBanner} accessibilityRole="alert">
            <View style={styles.errorBannerTextCol}>
              <Text style={styles.errorBannerTitle}>
                {language === 'kn'
                  ? 'ಇತಿಹಾಸವನ್ನು ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ'
                  : 'History Sync Issue'}
              </Text>
              <Text style={styles.errorBannerBody} numberOfLines={3}>
                {historyError}
              </Text>
            </View>
            <TouchableOpacity
              onPress={loadHistory}
              style={styles.errorRetryBtn}
              accessibilityRole="button"
              accessibilityLabel="Retry loading chat history"
            >
              <Text style={styles.errorRetryText}>
                {language === 'kn' ? 'ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ' : 'Retry'}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Main Conversation Area */}
        {historyLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.primary} />
            <Text style={styles.loadingLabel}>
              {language === 'kn'
                ? 'ನಿಮ್ಮ ಸಂಭಾಷಣೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ…'
                : 'Loading your diagnostic history…'}
            </Text>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={renderMessageItem}
            contentContainerStyle={
              messages.length === 0 ? styles.emptyListContent : styles.listContent
            }
            ListEmptyComponent={
              <EmptyState
                language={language}
                onSelectSuggestion={(sample) => setPrefillText(sample)}
              />
            }
            ListFooterComponent={
              isSending ? <TypingIndicator language={language} /> : null
            }
            keyboardDismissMode="interactive"
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          />
        )}

        {/* Multimodal Bottom Input Bar */}
        <InputBar
          language={language}
          isSending={isSending}
          prefillText={prefillText}
          onConsumePrefill={() => setPrefillText('')}
          isPreviewPlaying={playingMessageId === DRAFT_AUDIO_PREVIEW_ID}
          onTogglePreviewAudio={(uri) =>
            toggleRawUriAudio(DRAFT_AUDIO_PREVIEW_ID, uri)
          }
          onStopPreviewAudio={() => {
            if (playingMessageId === DRAFT_AUDIO_PREVIEW_ID) {
              stopPlayback();
            }
          }}
          onSend={handleSendSubmission}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.primary,
  },
  keyboardView: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  loadingLabel: {
    ...TYPOGRAPHY.body,
    color: COLORS.textSecondary,
    marginTop: SPACING.md,
    textAlign: 'center',
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.errorBg,
    borderBottomWidth: 1,
    borderBottomColor: '#FFCDD2',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm + 2,
    gap: SPACING.sm,
  },
  errorBannerTextCol: {
    flex: 1,
  },
  errorBannerTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.errorRed,
  },
  errorBannerBody: {
    fontSize: 11.5,
    color: COLORS.errorRed,
    marginTop: 1,
  },
  errorRetryBtn: {
    backgroundColor: COLORS.errorRed,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
  },
  errorRetryText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  emptyListContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  listContent: {
    paddingVertical: SPACING.sm + 2,
  },
});
