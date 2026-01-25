import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Mail, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui';
import { authService } from '../services';
import { useAuth } from '../context';

export function VerifyEmailPage() {
  const location = useLocation();
  const { user } = useAuth();
  const email = location.state?.email || user?.email || 'your email';
  
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  const handleResend = async () => {
    setIsResending(true);
    setResendMessage('');

    try {
      await authService.resendVerification({ email });
      setResendMessage('Verification email sent! Check your inbox.');
    } catch (err) {
      setResendMessage(err instanceof Error ? err.message : 'Failed to resend');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md text-center">
        <div className="w-16 h-16 mx-auto mb-6 text-primary">
          <Mail className="w-full h-full" />
        </div>

        <h1 className="text-3xl font-bold text-white mb-3">Check your email</h1>
        
        <p className="text-gray-400 mb-2">We sent a verification link to</p>
        <p className="text-primary font-medium mb-8">{email}</p>

        <Button
          variant="outline"
          onClick={handleResend}
          isLoading={isResending}
          className="mb-4"
        >
          Resend verification email
        </Button>

        {resendMessage && (
          <p className={`text-sm mb-4 ${resendMessage.includes('sent') ? 'text-success' : 'text-error'}`}>
            {resendMessage}
          </p>
        )}

        <p className="text-sm text-gray-500 mb-6">
          Didn't receive it? Check your spam folder
        </p>

        <Link to="/login" className="inline-flex items-center text-gray-400 hover:text-white text-sm">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to login
        </Link>
      </div>
    </div>
  );
}
