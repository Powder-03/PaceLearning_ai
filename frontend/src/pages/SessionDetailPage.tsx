import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, Circle, Play, Zap } from 'lucide-react';
import { Button, Card, Badge, ProgressBar, Spinner } from '../components/ui';
import { sessionService } from '../services';
import type { Session } from '../types';

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadSession = async () => {
      if (!sessionId) return;
      
      try {
        const data = await sessionService.get(sessionId);
        setSession(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session');
      } finally {
        setIsLoading(false);
      }
    };

    loadSession();
  }, [sessionId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <h2 className="text-xl font-bold text-white mb-2">Session not found</h2>
        <p className="text-gray-400 mb-4">{error || 'The session you are looking for does not exist.'}</p>
        <Link to="/sessions">
          <Button variant="outline">Back to Sessions</Button>
        </Link>
      </div>
    );
  }

  const progressPercentage = ((session.current_day - 1) / session.total_days) * 100;
  const lessonPlan = session.lesson_plan;

  const getDayStatus = (dayNum: number) => {
    if (dayNum < session.current_day) return 'completed';
    if (dayNum === session.current_day) return 'current';
    return 'upcoming';
  };

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <Card padding="lg" className="mb-6">
        <Link to="/sessions" className="inline-flex items-center text-gray-400 hover:text-white mb-4 text-sm">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Sessions
        </Link>

        <div className="flex items-center gap-3 mb-4">
          <Badge variant={session.mode === 'quick' ? 'warning' : 'purple'}>
            {session.mode === 'quick' ? '⚡ QUICK' : 'AI TUTOR'}
          </Badge>
          <h1 className="text-xl font-bold text-white">{session.topic}</h1>
        </div>

        {session.mode === 'quick' ? (
          <div className="mb-4">
            <p className="text-sm text-gray-400">
              Single session • {session.time_per_day}
              {session.target && <> • 🎯 {session.target}</>}
            </p>
          </div>
        ) : (
          <div className="mb-4">
            <ProgressBar value={progressPercentage} />
            <p className="text-sm text-gray-400 mt-2">
              Day {session.current_day} of {session.total_days} • {Math.round(progressPercentage)}% complete
            </p>
            {session.target && (
              <p className="text-sm text-gray-500 mt-1">🎯 Goal: {session.target}</p>
            )}
          </div>
        )}

        <div className="flex justify-end">
          <Link to={`/chat/${sessionId}`}>
            <Button>
              Continue Learning
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </Card>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left Column - Course Info & Timeline */}
        <div className="lg:col-span-3 space-y-6">
          {/* About */}
          {lessonPlan && (
            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">About This Course</h2>
              <p className="text-gray-400 mb-4">{lessonPlan.description}</p>
              
              <h3 className="text-sm font-medium text-white mb-2">Learning Outcomes:</h3>
              <ul className="space-y-1">
                {lessonPlan.learning_outcomes?.map((outcome, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="text-primary mt-1">•</span>
                    {outcome}
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Timeline */}
          <Card>
            <h2 className="text-lg font-semibold text-white mb-6">Lesson Plan</h2>
            
            <div className="space-y-0">
              {lessonPlan?.days?.map((day, index) => {
                const status = getDayStatus(day.day);
                const isLast = index === lessonPlan.days.length - 1;
                
                return (
                  <div key={day.day} className="relative">
                    {/* Connector line */}
                    {!isLast && (
                      <div className={`absolute left-[11px] top-8 bottom-0 w-0.5 ${
                        status === 'completed' ? 'bg-success' : 'bg-dark-border'
                      }`} />
                    )}
                    
                    <div className={`flex gap-4 pb-6 ${status === 'upcoming' ? 'opacity-50' : ''}`}>
                      {/* Icon */}
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                        status === 'completed' 
                          ? 'bg-success text-white'
                          : status === 'current'
                          ? 'bg-primary text-white'
                          : 'bg-dark-border text-gray-500'
                      }`}>
                        {status === 'completed' ? (
                          <Check className="w-4 h-4" />
                        ) : status === 'current' ? (
                          <Play className="w-3 h-3" />
                        ) : (
                          <Circle className="w-3 h-3" />
                        )}
                      </div>
                      
                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className={`font-medium ${status === 'current' ? 'text-white' : 'text-gray-400'}`}>
                            {day.title}
                          </h3>
                        </div>
                        
                        {status === 'current' && (
                          <div className="mt-2 p-3 bg-dark rounded-lg border-l-2 border-primary">
                            <p className="text-sm text-gray-400 mb-2">
                              Topics: {day.topics?.map(t => t.name).join(', ')}
                            </p>
                            {day.topics?.[0]?.key_concepts && (
                              <div className="flex flex-wrap gap-1">
                                {day.topics[0].key_concepts.map((concept, i) => (
                                  <span key={i} className="px-2 py-0.5 bg-dark-border rounded text-xs text-gray-400">
                                    {concept}
                                  </span>
                                ))}
                              </div>
                            )}
                            <Link to={`/chat/${sessionId}?day=${day.day}`}>
                              <Button size="sm" className="mt-3">
                                Start Day {day.day}
                              </Button>
                            </Link>
                          </div>
                        )}
                        
                        {status === 'completed' && (
                          <p className="text-xs text-gray-500">
                            {day.estimated_duration} • Completed
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Right Column - Quick Info */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <h2 className="text-lg font-semibold text-white mb-4">Current Day Preview</h2>
            
            {lessonPlan?.days?.find(d => d.day === session.current_day) && (
              <>
                <h3 className="font-medium text-white mb-2">
                  {lessonPlan.days[session.current_day - 1].title}
                </h3>
                <p className="text-sm text-gray-400 mb-4">
                  Duration: {lessonPlan.days[session.current_day - 1].estimated_duration}
                </p>
                
                <h4 className="text-sm font-medium text-gray-400 mb-2">Topics:</h4>
                <ul className="space-y-2 mb-4">
                  {lessonPlan.days[session.current_day - 1].topics?.map((topic, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <Circle className="w-3 h-3 text-primary" />
                      <span className="text-white">{topic.name}</span>
                    </li>
                  ))}
                </ul>
                
                <Link to={`/chat/${sessionId}`}>
                  <Button className="w-full">
                    Begin
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </>
            )}
          </Card>

          <Card>
            <h2 className="text-sm font-medium text-gray-400 mb-3">Session Info</h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Duration</span>
                <span className="text-white">{session.total_days} days</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Time per day</span>
                <span className="text-white">{session.time_per_day}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Status</span>
                <Badge variant={session.status === 'COMPLETED' ? 'success' : 'purple'} size="sm">
                  {session.status}
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Created</span>
                <span className="text-white">
                  {new Date(session.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
