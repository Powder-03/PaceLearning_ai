import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Calendar,
  Clock,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  Play,
  BookOpen,
} from 'lucide-react'
import { useSession, useLessonPlan, useGotoDay } from '@/hooks'
import { chatService } from '@/services'
import {
  Button,
  LoadingSpinner,
  Card,
  CardContent,
  ProgressBar,
  Badge,
} from '@/components/ui'
import { ChatContainer } from '@/components/chat'

export default function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const { data: session, isLoading: isLoadingSession, refetch: refetchSession } = useSession(sessionId)
  const { data: lessonPlan, isLoading: isLoadingPlan } = useLessonPlan(sessionId)
  const gotoDay = useGotoDay()

  const [showSidebar, setShowSidebar] = useState(true)
  const [isStartingLesson, setIsStartingLesson] = useState(false)

  // Calculate progress
  const progress = session
    ? ((session.current_day - 1) / session.total_days) * 100
    : 0

  const handleProgressUpdate = (_data: {
    current_day: number
    current_topic_index: number
    is_day_complete: boolean
    is_course_complete: boolean
  }) => {
    refetchSession()
  }

  const handleGotoDay = async (day: number) => {
    if (!sessionId) return
    await gotoDay.mutateAsync({ sessionId, day })
    refetchSession()
  }

  const handleStartLesson = async () => {
    if (!sessionId || !session) return
    setIsStartingLesson(true)
    try {
      await chatService.startLesson({
        session_id: sessionId,
        day: session.current_day,
      })
      refetchSession()
    } catch (error) {
      console.error('Failed to start lesson:', error)
    } finally {
      setIsStartingLesson(false)
    }
  }

  if (isLoadingSession || isLoadingPlan) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!session) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Session not found</p>
        <Button onClick={() => navigate('/dashboard')} className="mt-4">
          Back to Dashboard
        </Button>
      </div>
    )
  }

  const currentDayPlan = lessonPlan?.lesson_plan?.days?.find(
    (d) => d.day === session.current_day
  )

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Dashboard</span>
          </button>
          <div className="h-6 w-px bg-gray-200" />
          <div>
            <h1 className="text-lg font-semibold text-gray-900 line-clamp-1">
              {session.topic}
            </h1>
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                Day {session.current_day}/{session.total_days}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {session.time_per_day}
              </span>
            </div>
          </div>
        </div>

        {/* Progress */}
        <div className="hidden md:flex items-center gap-4">
          <div className="w-48">
            <ProgressBar value={progress} size="sm" />
          </div>
          <Badge variant={session.status === 'COMPLETED' ? 'success' : 'info'}>
            {Math.round(progress)}% Complete
          </Badge>
        </div>

        {/* Toggle sidebar */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowSidebar(!showSidebar)}
          className="md:hidden"
        >
          {showSidebar ? 'Hide Plan' : 'Show Plan'}
        </Button>
      </div>

      {/* Main content */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Sidebar - Lesson Plan */}
        <div
          className={`${
            showSidebar ? 'w-80 flex-shrink-0' : 'hidden'
          } hidden md:block overflow-hidden`}
        >
          <Card className="h-full flex flex-col">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Lesson Plan</h2>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {lessonPlan?.lesson_plan?.days?.map((day) => (
                <button
                  key={day.day}
                  onClick={() => handleGotoDay(day.day)}
                  className={`w-full text-left p-3 rounded-lg mb-1 transition-colors ${
                    day.day === session.current_day
                      ? 'bg-primary-50 border border-primary-200'
                      : day.day < session.current_day
                      ? 'bg-green-50 hover:bg-green-100'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {day.day < session.current_day ? (
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                    ) : day.day === session.current_day ? (
                      <Play className="w-4 h-4 text-primary-600 flex-shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-gray-300 flex-shrink-0" />
                    )}
                    <span
                      className={`text-sm font-medium ${
                        day.day === session.current_day
                          ? 'text-primary-700'
                          : day.day < session.current_day
                          ? 'text-green-700'
                          : 'text-gray-600'
                      }`}
                    >
                      Day {day.day}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 ml-6 line-clamp-2">
                    {day.title}
                  </p>
                </button>
              ))}
            </div>

            {/* Day navigation */}
            <div className="p-3 border-t border-gray-100 flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                disabled={session.current_day <= 1}
                onClick={() => handleGotoDay(session.current_day - 1)}
              >
                <ChevronLeft className="w-4 h-4" />
                Prev
              </Button>
              <Button
                variant="ghost"
                size="sm"
                disabled={session.current_day >= session.total_days}
                onClick={() => handleGotoDay(session.current_day + 1)}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </Card>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Current day info */}
          {currentDayPlan && (
            <Card className="mb-4 flex-shrink-0">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <BookOpen className="w-4 h-4 text-primary-600" />
                      <span className="text-sm font-medium text-primary-600">
                        Day {currentDayPlan.day}
                      </span>
                    </div>
                    <h3 className="font-semibold text-gray-900">
                      {currentDayPlan.title}
                    </h3>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {currentDayPlan.objectives?.slice(0, 3).map((obj, i) => (
                        <Badge key={i} variant="default" size="sm">
                          {obj.length > 40 ? obj.slice(0, 40) + '...' : obj}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={handleStartLesson}
                    disabled={isStartingLesson}
                  >
                    {isStartingLesson ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-1" />
                        Start Lesson
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Chat container */}
          <div className="flex-1 min-h-0">
            <ChatContainer
              sessionId={sessionId!}
              onProgressUpdate={handleProgressUpdate}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
