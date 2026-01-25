import { NavLink, useNavigate } from 'react-router-dom';
import { 
  Home, 
  Folder, 
  Sparkles, 
  FileText, 
  Video, 
  Youtube, 
  Settings,
  LogOut
} from 'lucide-react';
import { useAuth } from '../../context';
import { Badge } from '../ui';

interface SidebarProps {
  onClose?: () => void;
}

export function Sidebar({ onClose }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
      isActive
        ? 'bg-primary/20 text-white border-l-[3px] border-primary -ml-[3px] pl-[19px]'
        : 'text-gray-400 hover:text-white hover:bg-dark-hover'
    }`;

  const disabledClass = 'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-gray-500 cursor-not-allowed';

  return (
    <aside className="w-60 bg-dark-card border-r border-dark-border h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6">
        <NavLink to="/" className="text-xl font-bold text-white" onClick={onClose}>
          DocLearn
        </NavLink>
      </div>

      <div className="h-px bg-dark-border" />

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-6">
        {/* Learn Section */}
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3 px-4">
            Learn
          </p>
          <div className="space-y-1">
            <NavLink to="/dashboard" className={navLinkClass} onClick={onClose}>
              <Home className="w-5 h-5" />
              Dashboard
            </NavLink>
            <NavLink to="/sessions" className={navLinkClass} onClick={onClose}>
              <Folder className="w-5 h-5" />
              My Sessions
            </NavLink>
          </div>
        </div>

        {/* Modes Section */}
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3 px-4">
            Modes
          </p>
          <div className="space-y-1">
            <NavLink to="/sessions/new" className={navLinkClass} onClick={onClose}>
              <Sparkles className="w-5 h-5" />
              <span className="flex-1">AI Tutor</span>
              <span className="w-2 h-2 bg-success rounded-full" />
            </NavLink>
            
            <div className={disabledClass}>
              <FileText className="w-5 h-5" />
              <span className="flex-1">Document Chat</span>
              <Badge size="sm" variant="gray">SOON</Badge>
            </div>
            
            <div className={disabledClass}>
              <Video className="w-5 h-5" />
              <span className="flex-1">Video Learning</span>
              <Badge size="sm" variant="gray">SOON</Badge>
            </div>
            
            <div className={disabledClass}>
              <Youtube className="w-5 h-5" />
              <span className="flex-1">YouTube Tutor</span>
              <Badge size="sm" variant="gray">SOON</Badge>
            </div>
          </div>
        </div>
      </nav>

      {/* Bottom Section */}
      <div className="mt-auto">
        <div className="h-px bg-dark-border" />
        
        <div className="p-4 space-y-1">
          <NavLink to="/settings" className={navLinkClass} onClick={onClose}>
            <Settings className="w-5 h-5" />
            Settings
          </NavLink>
        </div>

        <div className="h-px bg-dark-border" />

        {/* User Section */}
        <div className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/30 flex items-center justify-center text-sm font-medium text-white">
              {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">
                {user?.name || user?.email}
              </p>
            </div>
          </div>
          
          <button
            onClick={handleLogout}
            className="mt-3 flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors w-full"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
}
