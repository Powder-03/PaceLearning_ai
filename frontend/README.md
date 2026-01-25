# DocLearn Frontend

A modern React TypeScript frontend for the DocLearn AI-powered learning platform.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **TailwindCSS** - Utility-first styling
- **React Router v6** - Client-side routing
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
```

3. Update `.env` with your backend URL:
```
VITE_API_URL=https://doclearn-746185407459.us-central1.run.app
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

Create a production build:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/         # Layout components (Sidebar, DashboardLayout)
│   │   └── ui/             # Reusable UI components
│   ├── context/            # React Context providers
│   ├── pages/              # Page components
│   ├── services/           # API service functions
│   ├── types/              # TypeScript type definitions
│   ├── App.tsx             # Main app with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── .env                    # Environment variables
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Features

### Authentication
- User registration with email verification
- Login with email/password
- Password reset via email
- JWT token management with auto-refresh

### Learning Sessions
- Create custom learning plans from any topic
- AI-generated structured curriculum
- Day-by-day progress tracking
- Resume sessions anytime

### AI Chat Interface
- Real-time streaming responses
- Lesson mode for guided learning
- Chat history preservation
- Interactive Q&A with AI tutor

### User Settings
- Profile management
- Password change
- Notification preferences
- Account deletion

## API Integration

The frontend connects to the DocLearn FastAPI backend:
- Base URL: Configured via `VITE_API_URL` environment variable
- Authentication: JWT Bearer tokens
- Streaming: Server-Sent Events (SSE) for chat responses

## Design System

### Colors
- Background: `#0f0a1a` (dark purple)
- Cards: `#1a1425` (dark card)
- Borders: `#2d2640` (dark border)
- Primary: `#8b5cf6` (purple)
- Accent: `#f97316` (orange)

### Components
All UI components follow a consistent dark theme with purple accents, featuring:
- Smooth transitions
- Responsive design
- Accessible markup
- Loading states

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## License

MIT
