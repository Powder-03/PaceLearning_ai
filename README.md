# DocLearn - AI-Powered Personalized Learning Platform

A production-ready AI microservice that provides personalized curriculum generation and interactive tutoring using Google Gemini models.

## Features

- **Dynamic Plan Generation**: Creates personalized, multi-day lesson plans based on topic, available time, and learning goals
- **Quick Mode**: Learn any topic in a single focused session — perfect for exam prep, quick revision, or exploring a concept on the fly
- **Interactive Tutoring**: Socratic-method teaching with understanding checks using Gemini 2.5 Flash
- **Adaptive Streaming**: Burst mode for short responses (<100 tokens), streaming for longer explanations
- **Buffer-Based Memory**: 10-message buffer with automatic summarization for efficient context management
- **Progress Tracking**: Stateful learning across multiple sessions with day/topic progression
- **Responsive UI**: Fully mobile-friendly interface with slide-in sidebar, sticky header, and touch-optimised chat

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│    MongoDB      │────▶│  Sessions       │
│                 │     │                 │     │  Lesson Plans   │
│  - Sessions     │     │  (All Storage)  │     │  Chat History   │
│  - Chat         │     │                 │     │  Summaries      │
│  - Health       │     └─────────────────┘     └─────────────────┘
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  Google Gemini  │
│  - 2.5 Pro      │ ◀── Planning (curriculum generation)
│  - 2.5 Flash    │ ◀── Tutoring (interactive teaching)
└─────────────────┘
```

## Project Structure

```
app/
├── core/
│   ├── config.py          # Settings (Gemini, MongoDB, buffer size)
│   ├── llm_factory.py     # Gemini LLM initialization
│   └── prompts.py         # System prompts for tutor/planner
├── services/
│   ├── session_service.py # Session CRUD (MongoDB)
│   ├── chat_service.py    # Chat orchestration
│   ├── plan_service.py    # Plan generation
│   ├── memory.py          # Buffer summarization
│   └── mongodb.py         # MongoDB connection & chat storage
├── graphs/
│   ├── generation_graph.py # LangGraph state machine
│   ├── nodes.py           # Plan & tutor nodes
│   └── state.py           # Graph state definition
├── api/
│   └── routes/
│       ├── sessions.py    # Session endpoints
│       ├── chat.py        # Chat endpoints (SSE streaming)
│       ├── health.py      # Health checks
│       └── test.py        # Diagnostic test endpoints
└── main.py                # FastAPI application factory
```

## Running the Application

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Google API key and MongoDB URL
   ```

3. **Start MongoDB with Docker:**
   ```bash
   docker-compose up -d mongodb
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   The application will be available at `http://127.0.0.1:8000`

### Using Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up -d

# Start with admin UI (Mongo Express)
docker-compose --profile dev up -d

# View logs
docker-compose logs -f app
```

## API Endpoints

### Sessions
- `POST /api/v1/sessions` - Create a new learning session
- `GET /api/v1/sessions` - List user sessions
- `GET /api/v1/sessions/{id}` - Get session details
- `GET /api/v1/sessions/{id}/plan` - Get lesson plan
- `PATCH /api/v1/sessions/{id}/progress` - Update progress
- `DELETE /api/v1/sessions/{id}` - Delete session

### Chat
- `POST /api/v1/chat` - Send message (auto-detects streaming need)
- `POST /api/v1/chat/stream` - SSE streaming endpoint
- `POST /api/v1/chat/start-lesson` - Start/resume a lesson
- `GET /api/v1/chat/{session_id}/history` - Get chat history with summaries

### Health
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe (MongoDB + Gemini)

### Test Endpoints
- `GET /test/ping` - Simple ping (no dependencies)
- `GET /test/mongodb/status` - MongoDB connection check
- `POST /test/mongodb` - MongoDB write/read test
- `GET /test/gemini/status` - Gemini API configuration check
- `POST /test/gemini` - Gemini API call test

## Memory Buffer System

The application uses a 10-message buffer for efficient context management:

1. **Buffer Phase**: Messages are stored in MongoDB as they're exchanged
2. **Threshold**: When buffer reaches 10 messages, summarization triggers
3. **Summarization**: Gemini Flash summarizes the conversation
4. **Storage**: Summary is stored, buffer is cleared
5. **Context**: LLM receives summaries + recent buffer for full context

```
Buffer: [msg1, msg2, ..., msg10] → Summarize → [Summary 1]
Buffer: [msg11, msg12, ..., msg20] → Summarize → [Summary 1, Summary 2]
...
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | - | Google AI API key (required) |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection URL |
| `MONGODB_DB_NAME` | `doclearn` | MongoDB database name |
| `PLANNING_MODEL` | `gemini-2.5-pro` | Model for curriculum generation |
| `TUTORING_MODEL` | `gemini-2.5-flash` | Model for interactive tutoring |
| `STREAMING_TOKEN_THRESHOLD` | `100` | Tokens threshold for streaming |
| `MEMORY_BUFFER_SIZE` | `10` | Messages before summarization |

## Deployment

### Google Cloud Run

1. **Enable required APIs:**
   - Cloud Build API
   - Cloud Run API
   - Secret Manager API

2. **Create secrets in Secret Manager:**
   - `doclearn-mongo-url`: MongoDB connection string (e.g., MongoDB Atlas)
   - `doclearn-gemini-key`: Google API key

3. **Deploy:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```

The `cloudbuild.yaml` is configured to:
- Build Docker image
- Push to Container Registry
- Deploy to Cloud Run with secrets mounted as environment variables

## MongoDB Collections

The application uses the following MongoDB collections:

- **learning_sessions**: Session documents with lesson plans and progress
- **chat_messages**: Chat message buffer with timestamps
- **chat_summaries**: Summarized conversation history
- **test_collection**: Temporary collection for diagnostic tests

## License

MIT
