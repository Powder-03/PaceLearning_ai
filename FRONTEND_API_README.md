# DocLearn API - Frontend Integration Guide

A comprehensive guide for frontend developers to integrate with the DocLearn AI-powered learning platform API.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://your-domain.com/api/v1
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Authentication Flow

```
1. Register → Get token (unverified user)
2. Verify Email → Click link in email
3. Login → Get token
4. Use token for all protected requests
```

---

## API Endpoints

### 🔐 Authentication

#### Register a New User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"  // optional
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid-string",
    "email": "user@example.com",
    "name": "John Doe",
    "is_verified": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Errors:**
- `400`: Email already registered

---

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid-string",
    "email": "user@example.com",
    "name": "John Doe",
    "is_verified": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Errors:**
- `401`: Invalid email or password

---

#### Resend Verification Email

```http
POST /api/v1/auth/resend-verification
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "If an unverified account exists with this email, a verification link has been sent."
}
```

---

#### Forgot Password

```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

---

#### Reset Password

```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "new_password": "newpassword456"
}
```

**Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

**Errors:**
- `400`: Invalid or expired token

---

#### Get Current User Profile

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "name": "John Doe",
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### Update Profile

```http
PUT /api/v1/auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Doe"
}
```

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "name": "Jane Doe",
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### Change Password

```http
POST /api/v1/auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Errors:**
- `400`: Current password is incorrect

---

#### Verify Token

```http
POST /api/v1/auth/verify-token
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "name": "John Doe",
  "is_verified": true,
  "created_at": null
}
```

**Errors:**
- `401`: Invalid or expired token

---

#### Refresh Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "access_token": "new-jwt-token...",
  "token_type": "bearer",
  "user": { ... }
}
```

---

#### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

> **Note:** JWT is stateless. Frontend should discard the token on logout.

---

#### Delete Account

```http
DELETE /api/v1/auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Account deleted successfully"
}
```

---

### 📚 Sessions (Learning Plans)

> **Requires:** Verified user (`is_verified: true`)

#### Create a Learning Session

```http
POST /api/v1/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic": "Machine Learning Basics",
  "total_days": 7,
  "time_per_day": "1 hour"
}
```

**Response (201):**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "READY",
  "message": "🎉 Your personalized learning plan for \"Machine Learning Basics\" is ready!...",
  "lesson_plan": {
    "title": "Machine Learning Fundamentals",
    "description": "A comprehensive 7-day course...",
    "learning_outcomes": ["Understand ML basics", "..."],
    "total_days": 7,
    "time_per_day": "1 hour",
    "days": [
      {
        "day": 1,
        "title": "Day 1 - Introduction to ML",
        "objectives": ["Understand what ML is", "..."],
        "estimated_duration": "1 hour",
        "topics": [
          {
            "name": "What is Machine Learning?",
            "duration": "15 minutes",
            "key_concepts": ["supervised learning", "unsupervised learning"],
            "teaching_approach": "Start with real-world examples...",
            "check_questions": ["Can you explain...?"]
          }
        ],
        "day_summary": "Introduction to core ML concepts",
        "practice_suggestions": ["Try a simple dataset..."]
      }
    ]
  }
}
```

---

#### List User Sessions

```http
GET /api/v1/sessions?mode=generation&status=READY&limit=20&offset=0
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | string | null | Filter by mode (`generation`) |
| `status` | string | null | Filter by status (`PLANNING`, `READY`, `IN_PROGRESS`, `COMPLETED`) |
| `limit` | int | 20 | Max results (1-100) |
| `offset` | int | 0 | Pagination offset |

**Response (200):**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "user_id": "user-uuid",
      "topic": "Machine Learning Basics",
      "total_days": 7,
      "time_per_day": "1 hour",
      "current_day": 1,
      "current_topic_index": 0,
      "status": "READY",
      "mode": "generation",
      "lesson_plan": { ... },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 5
}
```

---

#### Get Session Details

```http
GET /api/v1/sessions/{session_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "user_id": "user-uuid",
  "topic": "Machine Learning Basics",
  "total_days": 7,
  "time_per_day": "1 hour",
  "current_day": 2,
  "current_topic_index": 1,
  "status": "IN_PROGRESS",
  "mode": "generation",
  "lesson_plan": { ... },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

**Errors:**
- `404`: Session not found
- `403`: Not authorized to access this session

---

#### Get Lesson Plan

```http
GET /api/v1/sessions/{session_id}/plan
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "topic": "Machine Learning Basics",
  "lesson_plan": {
    "title": "...",
    "days": [...]
  },
  "current_day": 2,
  "total_days": 7,
  "progress_percentage": 14.28
}
```

---

#### Get Day Content

```http
GET /api/v1/sessions/{session_id}/plan/day/{day}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "day": 1,
  "title": "Day 1 - Introduction to ML",
  "objectives": ["..."],
  "estimated_duration": "1 hour",
  "topics": [...],
  "day_summary": "...",
  "practice_suggestions": ["..."]
}
```

---

#### Update Progress

```http
PATCH /api/v1/sessions/{session_id}/progress
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_day": 2,
  "current_topic_index": 0
}
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "current_day": 2,
  "current_topic_index": 0,
  "total_days": 7,
  "is_complete": false,
  "progress_percentage": 14.28
}
```

---

#### Advance to Next Day

```http
POST /api/v1/sessions/{session_id}/advance-day
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "current_day": 3,
  "current_topic_index": 0,
  "total_days": 7,
  "is_complete": false,
  "progress_percentage": 28.57
}
```

**Errors:**
- `400`: Already on the last day

---

#### Go to Specific Day

```http
POST /api/v1/sessions/{session_id}/goto-day/{day}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "current_day": 1,
  "current_topic_index": 0,
  "total_days": 7,
  "is_complete": false,
  "progress_percentage": 0.0
}
```

---

#### Delete Session

```http
DELETE /api/v1/sessions/{session_id}
Authorization: Bearer <token>
```

**Response (204):** No content

---

### 💬 Chat

> **Requires:** Verified user (`is_verified: true`)

#### Send Message (Standard)

```http
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "What is a neural network?"
}
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "response": "Great question! A neural network is a computational model inspired by...",
  "current_day": 1,
  "current_topic_index": 0,
  "is_day_complete": false,
  "is_course_complete": false
}
```

---

#### Send Message (Streaming via SSE)

```http
POST /api/v1/chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Explain backpropagation in detail"
}
```

**Response:** Server-Sent Events (SSE) stream

```
event: token
data: {"content": "Let's"}

event: token
data: {"content": " explore"}

event: token
data: {"content": " backpropagation"}

event: done
data: {"current_day": 1, "current_topic_index": 0, "is_day_complete": false, "is_course_complete": false, "full_response": "Let's explore backpropagation..."}

event: error  // Only on error
data: {"error": "Error message"}
```

**Frontend SSE Implementation (JavaScript):**

```javascript
async function streamChat(sessionId, message, token) {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ session_id: sessionId, message })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.content) {
          fullText += data.content;
          // Update UI with new token
          updateChatUI(fullText);
        }
        
        if (data.full_response) {
          // Stream complete
          onStreamComplete(data);
        }
        
        if (data.error) {
          // Handle error
          onStreamError(data.error);
        }
      }
    }
  }
}
```

**Using EventSource (Alternative):**

```javascript
function streamWithEventSource(sessionId, message, token) {
  // Note: EventSource doesn't support POST or custom headers natively
  // Use fetch with ReadableStream (above) or a library like sse.js
}
```

---

#### Start/Resume Lesson

```http
POST /api/v1/chat/start-lesson
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "day": 1  // optional - if not provided, continues from current day
}
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "current_day": 1,
  "day_title": "Day 1 - Introduction to ML",
  "objectives": [
    "Understand what machine learning is",
    "Learn about different types of ML"
  ],
  "welcome_message": "Welcome to Day 1! Today we'll explore the fundamentals of Machine Learning..."
}
```

---

#### Get Chat History

```http
GET /api/v1/chat/{session_id}/history?limit=100
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "messages": [
    {
      "role": "human",
      "content": "What is machine learning?",
      "timestamp": "2024-01-15T10:35:00Z"
    },
    {
      "role": "assistant",
      "content": "Machine learning is a subset of AI...",
      "timestamp": "2024-01-15T10:35:05Z"
    }
  ],
  "total_messages": 10,
  "current_day": 1,
  "summaries": [
    "In the previous conversation, we discussed the basics of ML..."
  ],
  "total_summaries": 1
}
```

---

### 🏥 Health Checks

#### Basic Health

```http
GET /health
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "doclearn-generation-mode",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

#### Readiness Check

```http
GET /health/ready
```

**Response (200):**
```json
{
  "status": "ready",
  "checks": {
    "mongodb": true,
    "gemini_api": true
  },
  "models": {
    "planning": "gemini-2.5-pro-preview-05-06",
    "tutoring": "gemini-2.5-flash-preview-05-20"
  },
  "streaming_threshold": 100,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

#### Liveness Check

```http
GET /health/live
```

**Response (200):**
```json
{
  "status": "alive",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### 🧪 Test Endpoints (Development Only)

#### Simple Ping

```http
GET /test/ping
```

**Response (200):**
```json
{
  "status": "ok",
  "message": "FastAPI is running",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

#### MongoDB Status

```http
GET /test/mongodb/status
```

**Response (200):**
```json
{
  "status": "connected",
  "mongodb_connected": true,
  "database": "doclearn"
}
```

---

#### Email Status

```http
GET /test/email/status
```

**Response (200):**
```json
{
  "status": "configured",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user_preview": "user***@gmail.com",
  "is_configured": true
}
```

---

#### Gemini Status

```http
GET /test/gemini/status
```

**Response (200):**
```json
{
  "status": "configured",
  "gemini_configured": true,
  "api_key_preview": "AIzaSyBxx...",
  "planning_model": "gemini-2.5-pro-preview-05-06",
  "tutoring_model": "gemini-2.5-flash-preview-05-20"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (verified user required or not your resource) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Frontend Implementation Tips

### 1. Token Storage

```javascript
// Store token securely (consider httpOnly cookies for production)
localStorage.setItem('access_token', response.access_token);

// Create auth header helper
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json'
});
```

### 2. API Client Setup (Axios Example)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Add auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 3. React Query Example

```javascript
import { useQuery, useMutation } from '@tanstack/react-query';
import api from './api';

// Get current user
export const useCurrentUser = () => {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: () => api.get('/auth/me').then(res => res.data),
    retry: false,
  });
};

// Login mutation
export const useLogin = () => {
  return useMutation({
    mutationFn: (credentials) => api.post('/auth/login', credentials),
    onSuccess: (response) => {
      localStorage.setItem('access_token', response.data.access_token);
    },
  });
};

// Create session
export const useCreateSession = () => {
  return useMutation({
    mutationFn: (sessionData) => api.post('/sessions', sessionData),
  });
};

// Get sessions
export const useSessions = (params) => {
  return useQuery({
    queryKey: ['sessions', params],
    queryFn: () => api.get('/sessions', { params }).then(res => res.data),
  });
};
```

### 4. Typical User Flow

```
1. User registers → Store token → Redirect to "verify email" page
2. User clicks email link → Backend verifies → Redirect to login
3. User logs in → Store token → Check is_verified
4. If verified → Show dashboard with sessions
5. User creates session → Wait for plan generation → Show plan
6. User starts lesson → Chat with AI tutor
7. AI teaches topics → User progresses → Complete course
```

### 5. Session Status Flow

```
PLANNING → READY → IN_PROGRESS → COMPLETED
```

### 6. Chat Streaming Best Practices

```javascript
// Show typing indicator while streaming
// Update message in real-time as tokens arrive
// Disable send button during streaming
// Handle connection errors gracefully
// Store complete response when done
```

### 7. React Streaming Component Example

```jsx
import { useState, useCallback } from 'react';

function ChatMessage({ sessionId }) {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(async () => {
    if (!message.trim() || isStreaming) return;
    
    setIsStreaming(true);
    setResponse('');
    
    try {
      const res = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ session_id: sessionId, message })
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                setResponse(prev => prev + data.content);
              }
              if (data.full_response) {
                // Stream complete
                setIsStreaming(false);
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream error:', error);
      setIsStreaming(false);
    }
    
    setMessage('');
  }, [message, sessionId, isStreaming]);

  return (
    <div>
      <div className="response">{response}</div>
      <input 
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={isStreaming}
        placeholder="Ask a question..."
      />
      <button onClick={sendMessage} disabled={isStreaming}>
        {isStreaming ? 'Thinking...' : 'Send'}
      </button>
    </div>
  );
}
```

---

## CORS Configuration

The backend allows these origins:
- `http://localhost:3000`
- `http://localhost:5173`
- `http://localhost:5174`
- `http://localhost:8080`
- Custom `FRONTEND_URL` from environment

---

## TypeScript Interfaces

```typescript
// Auth Types
interface User {
  user_id: string;
  email: string;
  name: string | null;
  is_verified: boolean;
  created_at: string | null;
}

interface AuthResponse {
  access_token: string;
  token_type: 'bearer';
  user: User;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

// Session Types
type SessionStatus = 'PLANNING' | 'READY' | 'IN_PROGRESS' | 'COMPLETED';

interface Topic {
  name: string;
  duration: string;
  key_concepts: string[];
  teaching_approach: string;
  check_questions: string[];
}

interface DayPlan {
  day: number;
  title: string;
  objectives: string[];
  estimated_duration: string;
  topics: Topic[];
  day_summary: string;
  practice_suggestions: string[];
}

interface LessonPlan {
  title: string;
  description: string;
  learning_outcomes: string[];
  total_days: number;
  time_per_day: string;
  days: DayPlan[];
}

interface Session {
  session_id: string;
  user_id: string;
  topic: string;
  total_days: number;
  time_per_day: string;
  current_day: number;
  current_topic_index: number;
  status: SessionStatus;
  mode: string;
  lesson_plan: LessonPlan | null;
  created_at: string;
  updated_at: string;
}

interface CreateSessionRequest {
  topic: string;
  total_days: number;
  time_per_day: string;
}

interface CreateSessionResponse {
  session_id: string;
  status: SessionStatus;
  message: string;
  lesson_plan: LessonPlan;
}

// Chat Types
interface ChatRequest {
  session_id: string;
  message: string;
}

interface ChatResponse {
  session_id: string;
  response: string;
  current_day: number;
  current_topic_index: number;
  is_day_complete: boolean;
  is_course_complete: boolean;
}

interface ChatMessage {
  role: 'human' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessage[];
  total_messages: number;
  current_day: number;
  summaries: string[];
  total_summaries: number;
}

// SSE Event Types
interface TokenEvent {
  content: string;
}

interface DoneEvent {
  current_day: number;
  current_topic_index: number;
  is_day_complete: boolean;
  is_course_complete: boolean;
  full_response: string;
}

interface ErrorEvent {
  error: string;
}
```

---

## Rate Limits

Currently no rate limits are implemented. Consider adding client-side throttling for:
- Chat messages: 1 message per 2 seconds
- Session creation: 1 per 10 seconds

---

## Environment Variables (Backend Reference)

For deployment, ensure the backend has these configured:
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET` - Secret for JWT signing
- `GEMINI_API_KEY` - Google Gemini API key
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - Email configuration
- `FRONTEND_URL` - Your frontend URL for CORS and email links

---

## Quick Start Checklist

- [ ] Set up API client with base URL
- [ ] Implement token storage (localStorage or cookies)
- [ ] Add auth interceptor for automatic token injection
- [ ] Handle 401 errors globally (redirect to login)
- [ ] Implement registration → email verification → login flow
- [ ] Create session management (list, create, delete)
- [ ] Implement chat with SSE streaming
- [ ] Add loading states and error handling
- [ ] Test all endpoints with Postman/Insomnia first

---

## Support

For API issues or questions, check:
1. Health endpoint: `GET /health/ready`
2. Test endpoints for debugging (development only)
3. Check browser console for CORS errors
4. Verify token is being sent correctly
