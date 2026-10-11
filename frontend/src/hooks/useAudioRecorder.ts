// src/hooks/useAudioRecorder.ts
import { useCallback, useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import {
  useAudioRecorder as useExpoAudioRecorder,
  RecordingPresets,
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
} from 'expo-audio';
import { AudioRecordingResult } from '../types/chat';
import { deleteTempAudioFile, uriToAudioBase64 } from '../utils/audio';

export interface UseAudioRecorderReturn {
  isRecording: boolean;
  elapsedSeconds: number;
  recordedAudio: AudioRecordingResult | null;
  errorMessage: string | null;
  startRecording: () => Promise<boolean>;
  stopRecording: () => Promise<AudioRecordingResult | null>;
  discardRecording: () => Promise<void>;
  consumeRecording: () => void;
  clearError: () => void;
}

export const useAudioRecorder = (): UseAudioRecorderReturn => {
  const recorder = useExpoAudioRecorder(RecordingPresets.HIGH_QUALITY);

  const [isRecording, setIsRecording] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [recordedAudio, setRecordedAudio] = useState<AudioRecordingResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, [clearTimer]);

  const clearError = useCallback(() => {
    setErrorMessage(null);
  }, []);

  /**
   * Discards an unsent recording and deletes its temp file.
   */
  const discardRecording = useCallback(async () => {
    clearTimer();
    setIsRecording(false);
    setElapsedSeconds(0);
    if (recordedAudio?.uri) {
      await deleteTempAudioFile(recordedAudio.uri);
    }
    setRecordedAudio(null);
  }, [clearTimer, recordedAudio]);

  /**
   * Clears the input bar's recorded state after sending WITHOUT deleting the file,
   * so the user can replay their sent voice note from the chat bubble.
   */
  const consumeRecording = useCallback(() => {
    clearTimer();
    setIsRecording(false);
    setElapsedSeconds(0);
    setRecordedAudio(null);
  }, [clearTimer]);

  const startRecording = useCallback(async (): Promise<boolean> => {
    setErrorMessage(null);

    try {
      const permission = await requestRecordingPermissionsAsync();
      if (!permission.granted) {
        setErrorMessage(
          'Microphone permission was denied. Please enable microphone access in your device or browser settings.'
        );
        return false;
      }

      if (recordedAudio?.uri) {
        await deleteTempAudioFile(recordedAudio.uri);
        setRecordedAudio(null);
      }

      if (Platform.OS !== 'web') {
        await setAudioModeAsync({
          allowsRecording: true,
          playsInSilentMode: true,
        });
      }

      await recorder.prepareToRecordAsync();
      recorder.record();

      startTimeRef.current = Date.now();
      setElapsedSeconds(0);
      setIsRecording(true);

      clearTimer();
      timerRef.current = setInterval(() => {
        const secs = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setElapsedSeconds(secs);
      }, 250);

      return true;
    } catch (err) {
      clearTimer();
      setIsRecording(false);
      setElapsedSeconds(0);
      const msg =
        err instanceof Error
          ? err.message
          : 'Could not start voice recording. Please check your microphone.';
      setErrorMessage(msg);
      return false;
    }
  }, [clearTimer, recordedAudio, recorder]);

  const stopRecording = useCallback(async (): Promise<AudioRecordingResult | null> => {
    clearTimer();
    const durationSeconds = Math.max(
      1,
      Math.round((Date.now() - startTimeRef.current) / 1000) || elapsedSeconds
    );

    try {
      await recorder.stop();
      setIsRecording(false);

      if (Platform.OS !== 'web') {
        await setAudioModeAsync({
          allowsRecording: false,
          playsInSilentMode: true,
        });
      }

      const uri = recorder.uri;
      if (!uri) {
        setErrorMessage('No audio file was produced. Please try recording again.');
        return null;
      }

      const base64 = await uriToAudioBase64(uri);
      if (!base64) {
        setErrorMessage('Recorded audio was empty. Please speak clearly and try again.');
        return null;
      }

      const result: AudioRecordingResult = {
        uri,
        durationSeconds,
        mimeType: Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4',
        base64,
      };

      setRecordedAudio(result);
      return result;
    } catch (err) {
      setIsRecording(false);
      const msg =
        err instanceof Error
          ? err.message
          : 'Failed to finalize audio recording. Please try again.';
      setErrorMessage(msg);
      return null;
    }
  }, [clearTimer, elapsedSeconds, recorder]);

  return {
    isRecording,
    elapsedSeconds,
    recordedAudio,
    errorMessage,
    startRecording,
    stopRecording,
    discardRecording,
    consumeRecording,
    clearError,
  };
};
