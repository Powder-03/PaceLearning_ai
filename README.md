
# AI Microservice - Walking Skeleton

This repository contains the boilerplate code for a production-ready AI microservice using FastAPI, PostgreSQL (SQLAlchemy), and MongoDB (PyMongo). It is designed for deployment to Google Cloud Run via Google Cloud Build.

## Project Structure

- `app/`: Contains the application code.
  - `core/config.py`: Manages application settings using `pydantic-settings`.
  - `db/session.py`: Handles SQLAlchemy database sessions.
  - `main.py`: The main FastAPI application file.
- `Dockerfile`: A multi-stage Dockerfile for building the application container.
- `cloudbuild.yaml`: Google Cloud Build configuration for deployment.
- `requirements.txt`: Python dependencies.
- `.env`: Local environment variables (not checked into source control).

## Running the Application Locally

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory and add the following:
   ```
   DATABASE_URL="postgresql+asyncpg://user:password@host:port/db"
   MONGODB_URL="mongodb://user:password@host:port"
   ```

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```
   The application will be available at `http://127.0.0.1:8000`.

## Deployment

This project is configured for deployment to Google Cloud Run. The `cloudbuild.yaml` file defines the build and deployment steps.

1. **Enable required Google Cloud APIs:**
   - Cloud Build API
   - Cloud Run API
   - Secret Manager API

2. **Create secrets in Secret Manager:**
   - `doclearn-db-url`: The PostgreSQL connection string.
   - `doclearn-mongo-url`: The MongoDB connection string.

3. **Push to a Google Cloud Source Repository:**
   Push the code to a repository that Cloud Build has access to.

4. **Trigger the build:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```
.add .