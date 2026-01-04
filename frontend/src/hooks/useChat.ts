import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@clerk/clerk-react'
import { chatService } from '@/services'
import type { ChatMessage } from '@/types'

export function useChatHistory(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['chatHistory', sessionId],
    queryFn: () => chatService.getChatHistory(sessionId!),
    enabled: !!sessionId,
  })
}

export function useStartLesson() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, day }: { sessionId: string; day?: number }) =>
      chatService.startLesson({ session_id: sessionId, day }),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['chatHistory', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    },
  })
}

export function useChat(sessionId: string) {
  const { getToken } = useAuth()
  const queryClient = useQueryClient()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')

  // Load initial history
  const { data: historyData, isLoading: isLoadingHistory } = useChatHistory(sessionId)

  // Initialize messages from history
  const initializeMessages = useCallback(() => {
    if (historyData?.messages) {
      setMessages(historyData.messages)
    }
  }, [historyData])

  // Send message with streaming
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return

      // Add user message
      const userMessage: ChatMessage = {
        role: 'human',
        content: content.trim(),
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])

      // Start streaming
      setIsStreaming(true)
      setStreamingContent('')

      try {
        await chatService.sendMessageStream(
          { session_id: sessionId, message: content.trim() },
          // onToken
          (token) => {
            setStreamingContent((prev) => prev + token)
          },
          // onDone
          (metadata) => {
            setMessages((prev) => [
              ...prev,
              {
                role: 'assistant',
                content: streamingContent || '',
                timestamp: new Date().toISOString(),
              },
            ])
            setStreamingContent('')
            setIsStreaming(false)

            // Invalidate queries to update session state
            queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
            
            if (metadata.is_course_complete) {
              queryClient.invalidateQueries({ queryKey: ['sessions'] })
            }
          },
          // onError
          (error) => {
            console.error('Chat stream error:', error)
            setIsStreaming(false)
            setStreamingContent('')
          },
          // getToken
          getToken
        )
      } catch (error) {
        console.error('Chat error:', error)
        setIsStreaming(false)
        setStreamingContent('')
      }
    },
    [sessionId, isStreaming, getToken, queryClient, streamingContent]
  )

  // Add streaming content as a message when it updates
  const displayMessages = [...messages]
  if (streamingContent) {
    displayMessages.push({
      role: 'assistant',
      content: streamingContent,
      timestamp: new Date().toISOString(),
    })
  }

  return {
    messages: displayMessages,
    isStreaming,
    isLoadingHistory,
    sendMessage,
    initializeMessages,
  }
}
