import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, MoreVertical, ArrowRight, Folder } from 'lucide-react';
import { Card, Button, Badge, ProgressBar, Modal } from '../components/ui';
import { sessionService } from '../services';
import type { Session } from '../types';

type TabType = 'all' | 'active' | 'completed';

export function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [deleteModal, setDeleteModal] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const statusFilter = activeTab === 'active' 
        ? 'IN_PROGRESS' 
        : activeTab === 'completed' 
        ? 'COMPLETED' 
        : undefined;
      
      const data = await sessionService.list({ status: statusFilter, limit: 50 });
      setSessions(data.sessions);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [activeTab]);

  const handleDelete = async (sessionId: string) => {
    setIsDeleting(true);
    try {
      await sessionService.delete(sessionId);
      setSessions(sessions.filter(s => s.session_id !== sessionId));
      setTotal(total - 1);
      setDeleteModal(null);
    } catch (error) {
      console.error('Failed to delete session:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const getProgressPercentage = (session: Session) => {
    return ((session.current_day - 1) / session.total_days) * 100;
  };

  const tabs: { id: TabType; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'active', label: 'Active' },
    { id: 'completed', label: 'Completed' },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">My Sessions</h1>
        <Link to="/sessions/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Session
          </Button>
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-dark-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 text-sm font-medium transition-colors relative ${
              activeTab === tab.id
                ? 'text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
        ))}
      </div>

      {/* Sessions Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-4 bg-dark-border rounded w-1/4 mb-3" />
              <div className="h-5 bg-dark-border rounded w-3/4 mb-4" />
              <div className="h-2 bg-dark-border rounded w-full mb-2" />
              <div className="h-4 bg-dark-border rounded w-1/3" />
            </Card>
          ))}
        </div>
      ) : sessions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sessions.map((session) => (
            <Card key={session.session_id} className="relative group">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Badge variant={session.mode === 'quick' ? 'warning' : 'purple'} size="sm">
                    {session.mode === 'quick' ? '⚡ QUICK' : 'AI TUTOR'}
                  </Badge>
                </div>
                <button
                  onClick={() => setDeleteModal(session.session_id)}
                  className="p-1 text-gray-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>

              <Link to={`/sessions/${session.session_id}`}>
                <h3 className="font-medium text-white mb-3 hover:text-primary transition-colors line-clamp-1">
                  {session.topic}
                </h3>
              </Link>

              {session.target && (
                <p className="text-xs text-gray-500 mb-3 line-clamp-1">🎯 {session.target}</p>
              )}

              <div className="mb-3">
                <div className="flex items-center justify-between text-sm text-gray-400 mb-1">
                  {session.mode === 'quick' ? (
                    <span>Single session • {session.time_per_day}</span>
                  ) : (
                    <>
                      <span>Day {session.current_day} of {session.total_days}</span>
                      <span>{Math.round(getProgressPercentage(session))}%</span>
                    </>
                  )}
                </div>
                {session.mode !== 'quick' && (
                  <ProgressBar value={getProgressPercentage(session)} size="sm" />
                )}
              </div>

              <div className="flex items-center justify-between">
                <Badge 
                  variant={session.status === 'COMPLETED' ? 'success' : 'purple'} 
                  size="sm"
                >
                  {session.status === 'IN_PROGRESS' ? 'IN PROGRESS' : session.status}
                </Badge>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">{session.time_per_day}</span>
                  <Link 
                    to={session.mode === 'quick' ? `/chat/${session.session_id}` : `/sessions/${session.session_id}`}
                    className="text-sm text-primary hover:underline flex items-center gap-1"
                  >
                    {session.mode === 'quick' ? 'Open' : 'Continue'}
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 bg-dark-border rounded-full flex items-center justify-center">
            <Folder className="w-8 h-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">No sessions found</h3>
          <p className="text-gray-400 mb-6">Create your first AI-powered learning session</p>
          <Link to="/sessions/new">
            <Button>Create First Session</Button>
          </Link>
        </Card>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteModal}
        onClose={() => setDeleteModal(null)}
        title="Delete Session"
        size="sm"
      >
        <p className="text-gray-400 mb-6">
          Are you sure you want to delete this session? This action cannot be undone.
        </p>
        <div className="flex gap-3">
          <Button
            variant="ghost"
            className="flex-1"
            onClick={() => setDeleteModal(null)}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            className="flex-1"
            isLoading={isDeleting}
            onClick={() => deleteModal && handleDelete(deleteModal)}
          >
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
