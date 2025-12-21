
# DocLearn - AI-Powered Personalized Learning Platform

A production-ready AI microservice that provides personalized curriculum generation and interactive tutoring using Google Gemini models.

## Features

- **Dynamic Plan Generation**: Creates personalized, multi-day lesson plans based on topic, available time, and learning goals
- **Interactive Tutoring**: Socratic-method teaching with understanding checks using Gemini 2.5 Flash
- **Adaptive Streaming**: Burst mode for short responses (<100 tokens), streaming for longer explanations
- **Buffer-Based Memory**: 10-message buffer with automatic summarization for efficient context management
- **Progress Tracking**: Stateful learning across multiple sessions with day/topic progression

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│   PostgreSQL    │────▶│  Session Data   │
│                 │     │                 │     │  Lesson Plans   │
│  - Sessions     │     └─────────────────┘     │  Progress       │
│  - Chat         │                             └─────────────────┘
│  - Health       │     ┌─────────────────┐     ┌─────────────────┐
│                 │────▶│    MongoDB      │────▶│  Chat History   │
└─────────────────┘     │                 │     │  Summaries      │
        │               └─────────────────┘     │  Buffer         │
        ▼                                       └─────────────────┘
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
│   ├── config.py          # Settings (Gemini, DBs, buffer size)
│   ├── llm_factory.py     # Gemini LLM initialization
│   └── prompts.py         # System prompts for tutor/planner
├── db/
│   ├── models.py          # SQLAlchemy models (PostgreSQL)
│   └── session.py         # Database session management
├── services/
│   ├── session_service.py # Session CRUD (PostgreSQL)
│   ├── chat_service.py    # Chat orchestration
│   ├── plan_service.py    # Plan generation
│   ├── memory.py          # Buffer summarization
│   └── mongodb.py         # Chat storage (MongoDB)
├── graphs/
│   ├── generation_graph.py # LangGraph state machine
│   ├── nodes.py           # Plan & tutor nodes
│   └── state.py           # Graph state definition
├── api/
│   └── routes/
│       ├── sessions.py    # Session endpoints
│       ├── chat.py        # Chat endpoints (SSE streaming)
│       └── health.py      # Health checks
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
   # Edit .env with your Google API key and database URLs
   ```

3. **Start databases with Docker:**
   ```bash
   docker-compose up -d postgres mongodb
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Run the application:**
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

## Database Migrations (Alembic)

This project uses Alembic for database schema migrations.

### Common Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# Show current revision
alembic current

# Show migration history
alembic history

# Create a new migration (auto-detect changes)
alembic revision --autogenerate -m "Add new column"

# Create an empty migration (manual)
alembic revision -m "Custom migration"
```

### Creating New Migrations

When you modify models in `app/db/models.py`:

1. **Auto-generate migration:**
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. **Review the generated file** in `alembic/versions/`

3. **Apply the migration:**
   ```bash
   alembic upgrade head
   ```

## API Endpoints

### Sessions
- `POST /api/v1/sessions` - Create a new learning session
- `GET /api/v1/sessions/{id}` - Get session details
- `GET /api/v1/sessions/{id}/plan` - Get lesson plan

### Chat
- `POST /api/v1/chat` - Send message (auto-detects streaming need)
- `POST /api/v1/chat/stream` - SSE streaming endpoint
- `POST /api/v1/chat/start-lesson` - Start/resume a lesson
- `GET /api/v1/chat/{session_id}/history` - Get chat history with summaries

### Health
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe

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
| `DATABASE_URL` | - | PostgreSQL connection URL |
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
   - `doclearn-db-url`: PostgreSQL connection string
   - `doclearn-mongo-url`: MongoDB connection string
   - `doclearn-google-api-key`: Google API key

3. **Deploy:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```
