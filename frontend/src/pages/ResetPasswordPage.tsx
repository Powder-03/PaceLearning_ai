import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { Check, Circle } from 'lucide-react';
import { Button, Input, Card } from '../components/ui';
import { authService } from '../services';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  // Password requirements
  const requirements = [
    { label: 'At least 6 characters', met: newPassword.length >= 6 },
    { label: 'One uppercase letter', met: /[A-Z]/.test(newPassword) },
    { label: 'One number', met: /[0-9]/.test(newPassword) },
  ];

  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0;
  const allRequirementsMet = requirements.every(r => r.met);

  useEffect(() => {
    if (!token) {
      navigate('/forgot-password');
    }
  }, [token, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!passwordsMatch) {
      setError('Passwords do not match');
      return;
    }

    if (!allRequirementsMet) {
      setError('Please meet all password requirements');
      return;
    }

    setIsLoading(true);

    try {
      await authService.resetPassword({ token, new_password: newPassword });
      setIsSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center p-4">
        <Card className="w-full max-w-sm text-center" padding="lg">
          <div className="w-16 h-16 mx-auto mb-6 bg-success/20 rounded-full flex items-center justify-center">
            <Check className="w-8 h-8 text-success" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-3">Password Reset!</h1>
          <p className="text-gray-400 mb-6">
            Your password has been successfully reset. You can now log in with your new password.
          </p>
          <Link to="/login">
            <Button className="w-full">
              Sign in
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center p-4">
      <Card className="w-full max-w-md" padding="lg">
        <h1 className="text-2xl font-bold text-white text-center mb-2">Set new password</h1>
        <p className="text-gray-400 text-center mb-6">
          Create a strong password for your account
        </p>

        {error && (
          <div className="mb-4 p-3 bg-error/10 border border-error/20 rounded-lg text-error text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Input
              label="New password"
              type="password"
              placeholder="Enter new password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            {newPassword && (
              <div className="mt-2 flex gap-1">
                {[0, 1, 2, 3].map((i) => {
                  const strength = requirements.filter(r => r.met).length;
                  return (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded ${
                        i < strength
                          ? strength <= 1
                            ? 'bg-error'
                            : strength === 2
                            ? 'bg-warning'
                            : 'bg-success'
                          : 'bg-dark-border'
                      }`}
                    />
                  );
                })}
              </div>
            )}
          </div>

          <Input
            label="Confirm password"
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={confirmPassword && !passwordsMatch ? 'Passwords do not match' : undefined}
            required
          />

          <div className="space-y-2 py-2">
            {requirements.map((req, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                {req.met ? (
                  <Check className="w-4 h-4 text-success" />
                ) : (
                  <Circle className="w-4 h-4 text-gray-500" />
                )}
                <span className={req.met ? 'text-success' : 'text-gray-500'}>
                  {req.label}
                </span>
              </div>
            ))}
          </div>

          <Button 
            type="submit" 
            className="w-full" 
            isLoading={isLoading}
            disabled={!allRequirementsMet || !passwordsMatch}
          >
            Reset password
          </Button>
        </form>

        <p className="mt-4 text-center">
          <Link to="/login" className="text-gray-400 hover:text-white text-sm">
            Back to login
          </Link>
        </p>
      </Card>
    </div>
  );
}
