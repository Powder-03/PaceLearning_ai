import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, FileText, Video, Youtube, ArrowRight, Plus, Zap } from 'lucide-react';
import { Card, Button, Badge, ProgressBar } from '../components/ui';
import { useAuth } from '../context';
import { sessionService } from '../services';
import type { Session } from '../types';

export function DashboardPage() {
  const { user } = useAuth();
  const [recentSessions, setRecentSessions] = useState<Session[]>([]);
  const [sessionCount, setSessionCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const data = await sessionService.list({ limit: 4 });
        setRecentSessions(data.sessions);
        setSessionCount(data.total);
      } catch (error) {
        console.error('Failed to load sessions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSessions();
  }, []);

  const modes = [
    {
      id: 'ai-tutor',
      icon: Sparkles,
      title: 'AI Tutor',
      description: 'Personalized AI-generated learning plans',
      available: true,
      link: '/sessions/new',
      stats: `${sessionCount} sessions`,
    },
    {
      id: 'quick-mode',
      icon: Zap,
      title: 'Quick Mode',
      description: 'Learn any topic in one focused session',
      available: true,
      link: '/sessions/new',
      stats: 'Single session',
    },
    {
      id: 'document-chat',
      icon: FileText,
      title: 'Document Chat',
      description: 'Upload PDFs and chat with your materials',
      available: false,
    },
    {
      id: 'video-learning',
      icon: Video,
      title: 'Video Learning',
      description: 'Upload videos and learn interactively',
      available: false,
    },
    {
      id: 'youtube-tutor',
      icon: Youtube,
      title: 'YouTube Tutor',
      description: 'Learn from any YouTube video',
      available: false,
    },
  ];

  const getProgressPercentage = (session: Session) => {
    return ((session.current_day - 1) / session.total_days) * 100;
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {user?.name || 'Learner'} 👋
        </h1>
      </div>

      {/* Learning Modes */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-white mb-4">Choose Learning Mode</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {modes.map((mode) => (
            <Card
              key={mode.id}
              className={`relative ${!mode.available ? 'opacity-50' : ''}`}
              padding="md"
            >
              <div className="absolute top-4 right-4">
                <Badge variant={mode.available ? 'success' : 'gray'} size="sm">
                  {mode.available ? 'AVAILABLE' : 'COMING SOON'}
                </Badge>
              </div>

              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 ${
                mode.available ? (mode.id === 'quick-mode' ? 'bg-yellow-500/20' : 'bg-primary/20') : 'bg-dark-border'
              }`}>
                <mode.icon className={`w-5 h-5 ${
                  mode.id === 'quick-mode' ? 'text-yellow-400' :
                  mode.available ? 'text-primary' : 'text-gray-500'
                }`} />
              </div>

              <h3 className="text-lg font-semibold text-white mb-1">{mode.title}</h3>
              <p className="text-sm text-gray-400 mb-4">{mode.description}</p>

              {mode.available ? (
                <div className="flex items-center justify-between">
                  <Link to={mode.link!}>
                    <Button size="sm">
                      <Plus className="w-4 h-4 mr-1" />
                      Create Session
                    </Button>
                  </Link>
                  <span className="text-xs text-gray-500">{mode.stats}</span>
                </div>
              ) : (
                <button className="text-sm text-gray-500 underline">
                  Notify me
                </button>
              )}
            </Card>
          ))}
        </div>
      </section>

      {/* Recent Sessions */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Sessions</h2>
          <Link to="/sessions" className="text-sm text-primary hover:underline flex items-center gap-1">
            View all
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2].map((i) => (
              <Card key={i} className="animate-pulse">
                <div className="h-4 bg-dark-border rounded w-1/4 mb-3" />
                <div className="h-5 bg-dark-border rounded w-3/4 mb-4" />
                <div className="h-2 bg-dark-border rounded w-full mb-2" />
                <div className="h-4 bg-dark-border rounded w-1/3" />
              </Card>
            ))}
          </div>
        ) : recentSessions.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recentSessions.map((session) => (
              <Link key={session.session_id} to={`/sessions/${session.session_id}`}>
                <Card hover>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant={session.mode === 'quick' ? 'warning' : 'purple'} size="sm">
                      {session.mode === 'quick' ? '⚡ QUICK' : 'AI TUTOR'}
                    </Badge>
                    <Badge 
                      variant={session.status === 'COMPLETED' ? 'success' : 'purple'} 
                      size="sm"
                    >
                      {session.status}
                    </Badge>
                  </div>
                  
                  <h3 className="font-medium text-white mb-3 line-clamp-1">
                    {session.topic}
                  </h3>
                  
                  <ProgressBar 
                    value={getProgressPercentage(session)} 
                    size="sm" 
                    className="mb-2" 
                  />
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">
                      Day {session.current_day}/{session.total_days}
                    </span>
                    <span className="text-primary flex items-center gap-1">
                      Continue
                      <ArrowRight className="w-4 h-4" />
                    </span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <Card className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-dark-border rounded-full flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No sessions yet</h3>
            <p className="text-gray-400 mb-6">Create your first AI-powered learning session</p>
            <Link to="/sessions/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Create First Session
              </Button>
            </Link>
          </Card>
        )}
      </section>
    </div>
  );
}
