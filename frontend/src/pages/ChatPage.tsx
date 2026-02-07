import { useEffect, useState, useRef } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Send, 
  Circle, 
  Info,
  X,
  FileText,
  ClipboardList,
  Download,
  CheckCircle,
  Menu,
  Zap
} from 'lucide-react';
import { Button, Spinner, Modal } from '../components/ui';
import { chatService, sessionService, pdfService } from '../services';
import type { Session, ChatMessage, SSEDoneEvent, DayPlan } from '../types';

export function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [searchParams] = useSearchParams();
  const initialDay = searchParams.get('day');

  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [currentDay, setCurrentDay] = useState(1);
  const [showSidebar, setShowSidebar] = useState(window.innerWidth >= 1024);
  const [showLeftSidebar, setShowLeftSidebar] = useState(false);
  const [dayContent, setDayContent] = useState<DayPlan | null>(null);
  
  // Day completion modal state
  const [showDayCompleteModal, setShowDayCompleteModal] = useState(false);
  const [completedDay, setCompletedDay] = useState(0);
  const [isDownloadingDPP, setIsDownloadingDPP] = useState(false);
  const [isDownloadingNotes, setIsDownloadingNotes] = useState(false);
  const [downloadError, setDownloadError] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const streamingContentRef = useRef('');
  const hasStartedLesson = useRef(false);

  // Load session and chat history for current day
  useEffect(() => {
    const loadData = async () => {
      if (!sessionId) return;
      
      try {
        const sessionData = await sessionService.get(sessionId);
        setSession(sessionData);
        
        const dayToUse = initialDay ? parseInt(initialDay) : sessionData.current_day;
        setCurrentDay(dayToUse);
        
        // Load history for current day only
        const historyData = await chatService.getHistory(sessionId, 100, dayToUse);
        setMessages(historyData.messages);
        
        // Only start lesson if no messages exist for this day and we haven't started yet
        if (historyData.messages.length === 0 && !hasStartedLesson.current) {
          hasStartedLesson.current = true;
          await startDay(dayToUse);
        }
      } catch (error) {
        console.error('Failed to load chat:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [sessionId, initialDay]);

  // Load day content
  useEffect(() => {
    const loadDayContent = async () => {
      if (!sessionId || !session) return;
      
      try {
        const content = await sessionService.getDayContent(sessionId, currentDay);
        setDayContent(content);
      } catch (error) {
        console.error('Failed to load day content:', error);
      }
    };

    if (session) {
      loadDayContent();
    }
  }, [sessionId, session, currentDay]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const startDay = async (day: number) => {
    if (!sessionId) return;
    
    try {
      const response = await chatService.startLesson({ session_id: sessionId, day });
      
      setCurrentDay(response.current_day);
      
      // Add welcome message
      const welcomeMessage: ChatMessage = {
        role: 'assistant',
        content: response.welcome_message,
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, welcomeMessage]);
    } catch (error) {
      console.error('Failed to start lesson:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !sessionId || isSending) return;
    
    const userMessage: ChatMessage = {
      role: 'human',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsSending(true);
    setStreamingContent('');
    streamingContentRef.current = '';

    try {
      await chatService.sendMessageStream(
        { session_id: sessionId, message: userMessage.content },
        // onToken
        (token) => {
          streamingContentRef.current += token;
          setStreamingContent(streamingContentRef.current);
        },
        // onDone
        (data: SSEDoneEvent) => {
          const fullResponse = streamingContentRef.current || data.full_response || '';
          
          if (fullResponse) {
            const assistantMessage: ChatMessage = {
              role: 'assistant',
              content: fullResponse,
              timestamp: new Date().toISOString(),
            };
            
            setMessages(prev => [...prev, assistantMessage]);
          }
          
          setStreamingContent('');
          streamingContentRef.current = '';
          setIsSending(false);
          
          // Show day completion modal if day is complete
          if (data.is_day_complete) {
            setCompletedDay(currentDay);
            setShowDayCompleteModal(true);
          }
        },
        // onError
        (error) => {
          console.error('Stream error:', error);
          setIsSending(false);
          setStreamingContent('');
          streamingContentRef.current = '';
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsSending(false);
    }
  };

  // Handle DPP download
  const handleDownloadDPP = async () => {
    if (!sessionId) return;
    setIsDownloadingDPP(true);
    setDownloadError('');
    
    try {
      await pdfService.downloadDPP(sessionId, completedDay);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : 'Failed to download DPP');
    } finally {
      setIsDownloadingDPP(false);
    }
  };

  // Handle Notes download
  const handleDownloadNotes = async () => {
    if (!sessionId) return;
    setIsDownloadingNotes(true);
    setDownloadError('');
    
    try {
      await pdfService.downloadNotes(sessionId, completedDay);
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : 'Failed to download notes');
    } finally {
      setIsDownloadingNotes(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDayClick = async (day: number) => {
    if (!sessionId || day > (session?.total_days || 0) || day === currentDay) return;
    
    try {
      // Update backend to track current day
      await sessionService.gotoDay(sessionId, day);
      
      // Clear current messages for fresh start
      setMessages([]);
      setCurrentDay(day);
      
      // Load chat history for the selected day
      const historyData = await chatService.getHistory(sessionId, 100, day);
      
      if (historyData.messages.length > 0) {
        // Day has existing messages, show them
        setMessages(historyData.messages);
      } else {
        // No messages for this day, start the lesson
        await startDay(day);
      }
    } catch (error) {
      console.error('Failed to switch day:', error);
    }
  };

  const suggestedPrompts = [
    'Explain more',
    'Give me an example',
    'Quiz me on this',
    'Next topic please',
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark">
        <div className="text-center">
          <h2 className="text-xl font-bold text-white mb-2">Session not found</h2>
          <Link to="/sessions">
            <Button variant="outline">Back to Sessions</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-dark flex">
      {/* Mobile Left Sidebar Overlay */}
      {showLeftSidebar && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setShowLeftSidebar(false)}
        />
      )}

      {/* Left Sidebar - Days */}
      <aside className={`
        ${showLeftSidebar ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
        fixed lg:relative z-50 lg:z-auto
        w-52 bg-dark-card border-r border-dark-border flex flex-col shrink-0
        transition-transform duration-200 ease-in-out
        h-full
      `}>
        <div className="p-4 border-b border-dark-border flex items-center justify-between">
          <Link to="/" className="text-lg font-bold text-white">
            DocLearn
          </Link>
          <button 
            onClick={() => setShowLeftSidebar(false)}
            className="lg:hidden p-1 text-gray-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        
        <div className="p-4 border-b border-dark-border">
          <Link 
            to={session.mode === 'quick' ? '/sessions' : `/sessions/${sessionId}`}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            {session.mode === 'quick' ? 'Back to Sessions' : 'Back to Session'}
          </Link>
        </div>

        {session.mode === 'quick' ? (
          // Quick Mode sidebar content
          <div className="p-4 flex-1 overflow-y-auto">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-medium text-yellow-400">Quick Session</span>
            </div>
            <p className="text-sm text-white mb-3 font-medium">{session.topic}</p>
            {session.target && (
              <div className="p-3 bg-dark rounded-lg">
                <p className="text-xs text-gray-500 mb-1">🎯 Target</p>
                <p className="text-sm text-gray-300">{session.target}</p>
              </div>
            )}
            {dayContent && dayContent.topics && (
              <div className="mt-4">
                <p className="text-xs text-gray-500 mb-2">Topics</p>
                <div className="space-y-1.5">
                  {dayContent.topics.map((topic, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <Circle className="w-2.5 h-2.5 text-yellow-400" />
                      <span className="text-gray-400">{topic.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          // Multi-day sidebar content
          <div className="p-4 flex-1 overflow-y-auto">
            <p className="text-xs font-medium text-gray-500 uppercase mb-3">Days</p>
            <div className="space-y-1">
              {Array.from({ length: session.total_days }, (_, i) => i + 1).map((day) => {
                const isCurrent = day === currentDay;
                
                return (
                  <button
                    key={day}
                    onClick={() => {
                      handleDayClick(day);
                      setShowLeftSidebar(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      isCurrent
                        ? 'bg-primary/20 text-white'
                        : 'text-gray-400 hover:bg-dark-hover hover:text-white'
                    }`}
                  >
                    {isCurrent ? (
                      <div className="w-4 h-4 rounded-full bg-primary" />
                    ) : (
                      <Circle className="w-4 h-4" />
                    )}
                    <span>Day {day}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div className="p-4 border-t border-dark-border">
          <p className="text-xs text-gray-500 truncate">{session.topic}</p>
          {session.mode !== 'quick' && session.target && (
            <p className="text-xs text-gray-500 mt-1 truncate">🎯 {session.target}</p>
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <header className="bg-dark-card border-b border-dark-border px-4 sm:px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => setShowLeftSidebar(true)}
            className="lg:hidden p-2 text-gray-400 hover:text-white transition-colors mr-2 shrink-0"
          >
            <Menu className="w-5 h-5" />
          </button>
          <h1 className="text-white font-medium truncate flex-1">
            {session.mode === 'quick' 
              ? `⚡ ${session.topic}`
              : `Day ${currentDay}: ${dayContent?.title || session.lesson_plan?.days?.[currentDay - 1]?.title || 'Loading...'}`
            }
          </h1>
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 text-gray-400 hover:text-white transition-colors shrink-0"
          >
            <Info className="w-5 h-5" />
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'human' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[85%] sm:max-w-[70%] ${msg.role === 'human' ? '' : ''}`}>
                {msg.role === 'assistant' && (
                  <p className="text-xs text-gray-500 mb-1">AI Tutor</p>
                )}
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    msg.role === 'human'
                      ? 'bg-gradient-to-r from-primary to-purple-600 text-white rounded-br-md'
                      : 'bg-dark-card text-white rounded-bl-md'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
                {msg.timestamp && (
                  <p className={`text-xs text-gray-500 mt-1 ${msg.role === 'human' ? 'text-right' : ''}`}>
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                )}
              </div>
            </div>
          ))}

          {/* Streaming message */}
          {(isSending || streamingContent) && (
            <div className="flex justify-start">
              <div className="max-w-[70%]">
                <p className="text-xs text-gray-500 mb-1">AI Tutor</p>
                <div className="bg-dark-card text-white rounded-2xl rounded-bl-md px-4 py-3">
                  {streamingContent ? (
                    <p className="whitespace-pre-wrap">{streamingContent}</p>
                  ) : (
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-500 rounded-full typing-dot" />
                      <span className="w-2 h-2 bg-gray-500 rounded-full typing-dot" />
                      <span className="w-2 h-2 bg-gray-500 rounded-full typing-dot" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts */}
        {!isSending && messages.length > 0 && (
          <div className="px-4 sm:px-6 py-2 flex gap-2 flex-wrap">
            {suggestedPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => setInput(prompt)}
                className="px-3 py-1.5 text-sm border border-dark-border rounded-full text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="p-4 bg-dark-card border-t border-dark-border">
          <div className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              disabled={isSending}
              className="flex-1 bg-dark border border-dark-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              className="px-4"
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Lesson Info */}
      {showSidebar && (
        <>
        {/* Mobile overlay backdrop */}
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setShowSidebar(false)}
        />
        <aside className="fixed right-0 top-0 h-full z-50 lg:relative lg:z-auto w-72 bg-dark-card border-l border-dark-border flex flex-col shrink-0">
          <div className="p-4 border-b border-dark-border flex items-center justify-between">
            <h2 className="font-medium text-white">{session.mode === 'quick' ? 'Session Info' : "Today's Lesson"}</h2>
            <button
              onClick={() => setShowSidebar(false)}
              className="p-1 text-gray-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-4 space-y-4 overflow-y-auto flex-1">
            {dayContent && (
              <>
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Topics</h3>
                  <div className="space-y-2">
                    {dayContent.topics?.map((topic, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        <Circle className="w-3 h-3 text-primary" />
                        <span className="text-white">{topic.name}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="h-px bg-dark-border" />

                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Key Concepts</h3>
                  <div className="flex flex-wrap gap-1">
                    {dayContent.topics?.flatMap(t => t.key_concepts || []).map((concept, i) => (
                      <span key={i} className="px-2 py-1 bg-dark-border rounded text-xs text-gray-400">
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="h-px bg-dark-border" />

                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Objectives</h3>
                  <ul className="space-y-1">
                    {dayContent.objectives?.map((obj, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                        <span className="text-primary mt-1">•</span>
                        {obj}
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>

          <div className="p-4 border-t border-dark-border">
            {session.mode === 'quick' ? (
              <>
                <p className="text-sm text-yellow-400 mb-1">⚡ Quick Session</p>
                {session.target && <p className="text-xs text-gray-500">🎯 {session.target}</p>}
              </>
            ) : (
              <>
                <p className="text-sm text-gray-400 mb-1">Progress</p>
                <p className="text-white">
                  Day {currentDay} of {session.total_days}
                </p>
                {session.target && (
                  <p className="text-xs text-gray-500 mt-1">🎯 {session.target}</p>
                )}
              </>
            )}
          </div>
        </aside>
        </>
      )}

      {/* Day Completion Modal */}
      <Modal
        isOpen={showDayCompleteModal}
        onClose={() => setShowDayCompleteModal(false)}
        title=""
      >
        <div className="text-center py-4">
          <div className="w-16 h-16 mx-auto mb-4 bg-success/20 rounded-full flex items-center justify-center">
            <CheckCircle className="w-10 h-10 text-success" />
          </div>
          
          <h2 className="text-2xl font-bold text-white mb-2">
            🎉 Day {completedDay} Complete!
          </h2>
          
          <p className="text-gray-400 mb-6">
            Great job! You've completed all topics for today.
            Would you like to download study materials?
          </p>

          {downloadError && (
            <div className="mb-4 p-3 bg-error/10 border border-error/20 rounded-lg text-error text-sm">
              {downloadError}
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={handleDownloadDPP}
              disabled={isDownloadingDPP || isDownloadingNotes}
              className="w-full flex items-center justify-center gap-3 p-4 bg-dark-card border border-dark-border rounded-lg hover:border-primary/50 transition-colors disabled:opacity-50"
            >
              {isDownloadingDPP ? (
                <Spinner size="sm" />
              ) : (
                <ClipboardList className="w-5 h-5 text-primary" />
              )}
              <div className="text-left">
                <p className="font-medium text-white">Daily Practice Problems (DPP)</p>
                <p className="text-sm text-gray-400">Practice questions with answers</p>
              </div>
              <Download className="w-4 h-4 text-gray-400 ml-auto" />
            </button>

            <button
              onClick={handleDownloadNotes}
              disabled={isDownloadingDPP || isDownloadingNotes}
              className="w-full flex items-center justify-center gap-3 p-4 bg-dark-card border border-dark-border rounded-lg hover:border-primary/50 transition-colors disabled:opacity-50"
            >
              {isDownloadingNotes ? (
                <Spinner size="sm" />
              ) : (
                <FileText className="w-5 h-5 text-primary" />
              )}
              <div className="text-left">
                <p className="font-medium text-white">Study Notes</p>
                <p className="text-sm text-gray-400">Comprehensive notes for the day</p>
              </div>
              <Download className="w-4 h-4 text-gray-400 ml-auto" />
            </button>
          </div>

          <div className="mt-6 flex gap-3">
            <Button
              variant="outline"
              onClick={() => setShowDayCompleteModal(false)}
              className="flex-1"
            >
              Maybe Later
            </Button>
            {completedDay < (session?.total_days || 0) && (
              <Button
                onClick={() => {
                  setShowDayCompleteModal(false);
                  handleDayClick(completedDay + 1);
                }}
                className="flex-1"
              >
                Start Day {completedDay + 1}
              </Button>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
}
