import { apiRequest } from './api';
import type {
  Session,
  SessionListResponse,
  CreatePlanRequest,
  CreatePlanResponse,
  LessonPlanResponse,
  ProgressResponse,
  UpdateProgressRequest,
  DayPlan,
} from '../types';

export const sessionService = {
  // Create a new learning session
  create: (data: CreatePlanRequest): Promise<CreatePlanResponse> => {
    return apiRequest<CreatePlanResponse>('/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // List all sessions for the current user
  list: (params?: {
    mode?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<SessionListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.mode) searchParams.set('mode', params.mode);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    
    const queryString = searchParams.toString();
    return apiRequest<SessionListResponse>(`/sessions${queryString ? `?${queryString}` : ''}`);
  },

  // Get session details
  get: (sessionId: string): Promise<Session> => {
    return apiRequest<Session>(`/sessions/${sessionId}`);
  },

  // Get lesson plan
  getPlan: (sessionId: string): Promise<LessonPlanResponse> => {
    return apiRequest<LessonPlanResponse>(`/sessions/${sessionId}/plan`);
  },

  // Get specific day content
  getDayContent: (sessionId: string, day: number): Promise<DayPlan> => {
    return apiRequest<DayPlan>(`/sessions/${sessionId}/plan/day/${day}`);
  },

  // Update progress
  updateProgress: (sessionId: string, data: UpdateProgressRequest): Promise<ProgressResponse> => {
    return apiRequest<ProgressResponse>(`/sessions/${sessionId}/progress`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  // Advance to next day
  advanceDay: (sessionId: string): Promise<ProgressResponse> => {
    return apiRequest<ProgressResponse>(`/sessions/${sessionId}/advance-day`, {
      method: 'POST',
    });
  },

  // Go to specific day
  gotoDay: (sessionId: string, day: number): Promise<ProgressResponse> => {
    return apiRequest<ProgressResponse>(`/sessions/${sessionId}/goto-day/${day}`, {
      method: 'POST',
    });
  },

  // Delete session
  delete: (sessionId: string): Promise<void> => {
    return apiRequest<void>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },
};
