// src/api/client.ts
import axios, { AxiosError } from 'axios';
import { CONFIG } from '../constants/config';
import { ApiError } from '../types/chat';

const client = axios.create({
  baseURL: CONFIG.API_BASE_URL,
  timeout: CONFIG.REQUEST_TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

/**
 * Normalizes any Axios or unknown error into a safe, user-friendly ApiError.
 */
export const normalizeApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string | { msg?: string }[] }>;

    if (axiosErr.code === 'ECONNABORTED' || axiosErr.message?.toLowerCase().includes('timeout')) {
      return {
        message: 'The server took too long to respond. Please check your connection and try again.',
        isTimeout: true,
      };
    }

    if (!axiosErr.response) {
      return {
        message: `Unable to reach Livia AI server (${CONFIG.API_BASE_URL}). Make sure the FastAPI backend is running and reachable.`,
        isNetworkError: true,
      };
    }

    const status = axiosErr.response.status;
    const data = axiosErr.response.data;
    let detailMessage = '';

    if (typeof data?.detail === 'string') {
      detailMessage = data.detail;
    } else if (Array.isArray(data?.detail) && data.detail.length > 0) {
      detailMessage = data.detail.map((d) => d.msg ?? '').filter(Boolean).join('; ');
    }

    if (status === 400 && detailMessage) {
      return { message: detailMessage, statusCode: status };
    }
    if (status === 422) {
      return {
        message: detailMessage || 'Invalid request format sent to the server.',
        statusCode: status,
      };
    }
    if (status >= 500) {
      return {
        message: detailMessage || 'The diagnostic server encountered an internal error. Please try again.',
        statusCode: status,
      };
    }

    return {
      message: detailMessage || `Request failed with status ${status}.`,
      statusCode: status,
    };
  }

  if (error instanceof Error) {
    return { message: error.message };
  }

  return { message: 'An unexpected error occurred. Please try again.' };
};

client.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeApiError(error))
);

export default client;
