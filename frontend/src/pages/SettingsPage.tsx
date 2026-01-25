import { useState } from 'react';
import { Card, Button, Input, Badge, Modal } from '../components/ui';
import { useAuth } from '../context';
import { authService } from '../services';

type TabType = 'profile' | 'account' | 'notifications';

export function SettingsPage() {
  const { user, updateUser, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('profile');
  
  // Profile state
  const [name, setName] = useState(user?.name || '');
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState('');
  
  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState('');
  
  // Delete account state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleSaveProfile = async () => {
    setIsSavingProfile(true);
    setProfileMessage('');
    
    try {
      const updated = await authService.updateProfile({ name: name || undefined });
      updateUser(updated);
      setProfileMessage('Profile updated successfully');
    } catch (error) {
      setProfileMessage(error instanceof Error ? error.message : 'Failed to update profile');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage('');
    
    if (newPassword !== confirmPassword) {
      setPasswordMessage('Passwords do not match');
      return;
    }
    
    if (newPassword.length < 6) {
      setPasswordMessage('Password must be at least 6 characters');
      return;
    }
    
    setIsChangingPassword(true);
    
    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMessage('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      setPasswordMessage(error instanceof Error ? error.message : 'Failed to change password');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    
    try {
      await authService.deleteAccount();
      logout();
    } catch (error) {
      console.error('Failed to delete account:', error);
      setIsDeleting(false);
    }
  };

  const tabs: { id: TabType; label: string }[] = [
    { id: 'profile', label: 'Profile' },
    { id: 'account', label: 'Account' },
    { id: 'notifications', label: 'Notifications' },
  ];

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

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

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-lg font-semibold text-white mb-4">Your Profile</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b border-dark-border">
                <div>
                  <label className="text-sm text-gray-400">Name</label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your name"
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between py-3 border-b border-dark-border">
                <div>
                  <label className="text-sm text-gray-400">Email</label>
                  <p className="text-white flex items-center gap-2 mt-1">
                    {user?.email}
                    {user?.is_verified && (
                      <Badge variant="success" size="sm">Verified</Badge>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between py-3">
                <div>
                  <label className="text-sm text-gray-400">Member since</label>
                  <p className="text-white mt-1">
                    {user?.created_at 
                      ? new Date(user.created_at).toLocaleDateString('en-US', { 
                          month: 'long', 
                          year: 'numeric' 
                        })
                      : 'Unknown'
                    }
                  </p>
                </div>
              </div>
            </div>

            {profileMessage && (
              <p className={`text-sm mt-4 ${
                profileMessage.includes('success') ? 'text-success' : 'text-error'
              }`}>
                {profileMessage}
              </p>
            )}

            <div className="mt-6">
              <Button onClick={handleSaveProfile} isLoading={isSavingProfile}>
                Save Changes
              </Button>
            </div>
          </Card>

          <Card>
            <h2 className="text-lg font-semibold text-white mb-4">Learning Stats</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-white">-</p>
                <p className="text-sm text-gray-400">Sessions Completed</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-white">-</p>
                <p className="text-sm text-gray-400">Hours Learned</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-white">-</p>
                <p className="text-sm text-gray-400">Day Streak</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Account Tab */}
      {activeTab === 'account' && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-lg font-semibold text-white mb-4">Change Password</h2>
            
            <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
              <Input
                label="Current Password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <Input
                label="New Password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                hint="At least 6 characters"
                required
              />
              <Input
                label="Confirm New Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />

              {passwordMessage && (
                <p className={`text-sm ${
                  passwordMessage.includes('success') ? 'text-success' : 'text-error'
                }`}>
                  {passwordMessage}
                </p>
              )}

              <Button type="submit" isLoading={isChangingPassword}>
                Change Password
              </Button>
            </form>
          </Card>

          <Card className="border-error/30">
            <h2 className="text-lg font-semibold text-white mb-2">Danger Zone</h2>
            <p className="text-gray-400 text-sm mb-4">
              Permanently delete your account and all of your data.
            </p>
            <Button variant="danger" onClick={() => setShowDeleteModal(true)}>
              Delete Account
            </Button>
          </Card>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card>
          <h2 className="text-lg font-semibold text-white mb-4">Email Notifications</h2>
          
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <p className="text-white">Course Updates</p>
                <p className="text-sm text-gray-400">Get notified about new features and courses</p>
              </div>
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 rounded border-dark-border bg-dark text-primary focus:ring-primary"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <p className="text-white">Learning Reminders</p>
                <p className="text-sm text-gray-400">Daily reminders to continue your learning</p>
              </div>
              <input
                type="checkbox"
                className="w-5 h-5 rounded border-dark-border bg-dark text-primary focus:ring-primary"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <p className="text-white">New Mode Alerts</p>
                <p className="text-sm text-gray-400">Be notified when new learning modes are available</p>
              </div>
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 rounded border-dark-border bg-dark text-primary focus:ring-primary"
              />
            </label>
          </div>
        </Card>
      )}

      {/* Delete Account Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Account"
        size="sm"
      >
        <p className="text-gray-400 mb-6">
          Are you sure you want to delete your account? This will permanently delete all your data, sessions, and progress. This action cannot be undone.
        </p>
        <div className="flex gap-3">
          <Button
            variant="ghost"
            className="flex-1"
            onClick={() => setShowDeleteModal(false)}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            className="flex-1"
            isLoading={isDeleting}
            onClick={handleDeleteAccount}
          >
            Delete Account
          </Button>
        </div>
      </Modal>
    </div>
  );
}
