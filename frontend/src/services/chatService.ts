import api from '@/lib/api'
import type {
  ChatRequest,
  ChatResponse,
  ChatHistoryResponse,
  StartLessonRequest,
  StartLessonResponse,
} from '@/types'

export const chatService = {
  // Send a message and get response
  async sendMessage(data: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', data)
    return response.data
  },

  // Send a message with streaming response
  async sendMessageStream(
    data: ChatRequest,
    onToken: (content: string) => void,
    onDone: (metadata: {
      current_day: number
      current_topic_index: number
      is_day_complete: boolean
      is_course_complete: boolean
    }) => void,
    onError: (error: string) => void,
    getToken: () => Promise<string | null>
  ): Promise<void> {
    const token = await getToken()
    const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
    
    const response = await fetch(`${baseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            // Event type line, skip to data
            continue
          }
          
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const parsed = JSON.parse(data)
              
              if ('content' in parsed) {
                onToken(parsed.content)
              } else if ('current_day' in parsed) {
                onDone(parsed)
              } else if ('error' in parsed) {
                onError(parsed.error)
              }
            } catch {
              // Ignore parse errors for partial data
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },

  // Start a lesson
  async startLesson(data: StartLessonRequest): Promise<StartLessonResponse> {
    const response = await api.post<StartLessonResponse>('/chat/start-lesson', data)
    return response.data
  },

  // Get chat history
  async getChatHistory(
    sessionId: string,
    limit?: number
  ): Promise<ChatHistoryResponse> {
    const response = await api.get<ChatHistoryResponse>(
      `/chat/${sessionId}/history`,
      { params: { limit } }
    )
    return response.data
  },
}
