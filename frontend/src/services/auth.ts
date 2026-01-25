import { apiRequest } from './api';
import type {
  AuthResponse,
  User,
  RegisterRequest,
  LoginRequest,
  MessageResponse,
  ChangePasswordRequest,
  UpdateProfileRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ResendVerificationRequest,
} from '../types';

export const authService = {
  // Register a new user
  register: (data: RegisterRequest): Promise<AuthResponse> => {
    return apiRequest<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Login
  login: (data: LoginRequest): Promise<AuthResponse> => {
    return apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Get current user profile
  getMe: (): Promise<User> => {
    return apiRequest<User>('/auth/me');
  },

  // Update profile
  updateProfile: (data: UpdateProfileRequest): Promise<User> => {
    return apiRequest<User>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Change password
  changePassword: (data: ChangePasswordRequest): Promise<MessageResponse> => {
    return apiRequest<MessageResponse>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Forgot password
  forgotPassword: (data: ForgotPasswordRequest): Promise<MessageResponse> => {
    return apiRequest<MessageResponse>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Reset password
  resetPassword: (data: ResetPasswordRequest): Promise<MessageResponse> => {
    return apiRequest<MessageResponse>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Resend verification email
  resendVerification: (data: ResendVerificationRequest): Promise<MessageResponse> => {
    return apiRequest<MessageResponse>('/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Verify token
  verifyToken: (): Promise<User> => {
    return apiRequest<User>('/auth/verify-token', {
      method: 'POST',
    });
  },

  // Refresh token
  refreshToken: (): Promise<AuthResponse> => {
    return apiRequest<AuthResponse>('/auth/refresh', {
      method: 'POST',
    });
  },

  // Logout
  logout: (): Promise<MessageResponse> => {
    return apiRequest<MessageResponse>('/auth/logout', {
      method: 'POST',
    });
  },

  // Delete account
  deleteAccount: (): Promise<MessageResponse> => {
    return apiRequest<MessageResponse>('/auth/me', {
      method: 'DELETE',
    });
  },
};
