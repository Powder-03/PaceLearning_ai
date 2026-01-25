// API Types based on backend schemas

// Auth types
export interface User {
  user_id: string;
  email: string;
  name: string | null;
  is_verified: boolean;
  created_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface MessageResponse {
  message: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface UpdateProfileRequest {
  name?: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ResendVerificationRequest {
  email: string;
}

// Session types
export interface CreatePlanRequest {
  topic: string;
  total_days: number;
  time_per_day: string;
}

export interface CreatePlanResponse {
  session_id: string;
  status: string;
  message: string;
  lesson_plan: LessonPlan | null;
}

export interface LessonPlan {
  title: string;
  description: string;
  learning_outcomes: string[];
  total_days: number;
  time_per_day: string;
  days: DayPlan[];
}

export interface DayPlan {
  day: number;
  title: string;
  objectives: string[];
  estimated_duration: string;
  topics: TopicPlan[];
  day_summary: string;
  practice_suggestions: string[];
}

export interface TopicPlan {
  name: string;
  duration: string;
  key_concepts: string[];
  teaching_approach: string;
  check_questions: string[];
}

export interface Session {
  session_id: string;
  user_id: string;
  topic: string;
  total_days: number;
  time_per_day: string;
  current_day: number;
  current_topic_index: number;
  status: 'PLANNING' | 'READY' | 'IN_PROGRESS' | 'COMPLETED';
  mode: string;
  lesson_plan: LessonPlan | null;
  created_at: string;
  updated_at: string;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
}

export interface LessonPlanResponse {
  session_id: string;
  topic: string;
  lesson_plan: LessonPlan;
  current_day: number;
  total_days: number;
  progress_percentage: number;
}

export interface ProgressResponse {
  session_id: string;
  current_day: number;
  current_topic_index: number;
  total_days: number;
  is_complete: boolean;
  progress_percentage: number;
}

export interface UpdateProgressRequest {
  current_day?: number;
  current_topic_index?: number;
}

// Chat types
export interface ChatMessage {
  role: 'human' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  current_day: number;
  current_topic_index: number;
  is_day_complete: boolean;
  is_course_complete: boolean;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessage[];
  total_messages: number;
  current_day: number;
  summaries: string[];
  total_summaries: number;
}

export interface StartLessonRequest {
  session_id: string;
  day?: number;
}

export interface StartLessonResponse {
  session_id: string;
  current_day: number;
  day_title: string;
  objectives: string[];
  welcome_message: string;
}

// SSE Event types
export interface SSETokenEvent {
  content: string;
}

export interface SSEDoneEvent {
  current_day: number;
  current_topic_index: number;
  is_day_complete: boolean;
  is_course_complete: boolean;
  full_response?: string;
}

export interface SSEErrorEvent {
  error: string;
}

// API Error
export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}
