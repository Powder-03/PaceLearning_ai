import { apiRequest, API_BASE_URL, getAuthHeaders } from './api';
import type {
  ChatRequest,
  ChatResponse,
  ChatHistoryResponse,
  StartLessonRequest,
  StartLessonResponse,
  SSETokenEvent,
  SSEDoneEvent,
  SSEErrorEvent,
} from '../types';

export const chatService = {
  // Send a message (non-streaming)
  sendMessage: (data: ChatRequest): Promise<ChatResponse> => {
    return apiRequest<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Send a message with streaming response
  sendMessageStream: async (
    data: ChatRequest,
    onToken: (token: string) => void,
    onDone: (data: SSEDoneEvent) => void,
    onError: (error: string) => void
  ): Promise<void> => {
    const url = `${API_BASE_URL}/chat/stream`;
    const headers = getAuthHeaders();

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Stream error' }));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Stream error');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          
          // Track event type
          if (trimmedLine.startsWith('event:')) {
            currentEvent = trimmedLine.slice(6).trim();
            continue;
          }
          
          // Process data line
          if (trimmedLine.startsWith('data:')) {
            try {
              const jsonStr = trimmedLine.slice(5).trim();
              if (!jsonStr) continue;
              
              const eventData = JSON.parse(jsonStr);

              if (currentEvent === 'token' && 'content' in eventData) {
                onToken((eventData as SSETokenEvent).content);
              } else if (currentEvent === 'error' && 'error' in eventData) {
                onError((eventData as SSEErrorEvent).error);
              } else if (currentEvent === 'done') {
                onDone(eventData as SSEDoneEvent);
              } else if ('content' in eventData) {
                // Fallback for data-only format
                onToken((eventData as SSETokenEvent).content);
              } else if ('error' in eventData) {
                onError((eventData as SSEErrorEvent).error);
              } else if ('current_day' in eventData) {
                onDone(eventData as SSEDoneEvent);
              }
              
              // Reset event after processing
              currentEvent = '';
            } catch (e) {
              // Skip invalid JSON lines
              console.warn('Failed to parse SSE data:', trimmedLine);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown error');
    }
  },

  // Start or resume a lesson
  startLesson: (data: StartLessonRequest): Promise<StartLessonResponse> => {
    return apiRequest<StartLessonResponse>('/chat/start-lesson', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Get chat history
  getHistory: (sessionId: string, limit: number = 100): Promise<ChatHistoryResponse> => {
    return apiRequest<ChatHistoryResponse>(`/chat/${sessionId}/history?limit=${limit}`);
  },
};
