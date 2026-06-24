# The Company Brain (Soil Systems)

A searchable company knowledge base and hybrid RAG system designed to capture, structure, and query organizational memory across multiple subsidiaries, projects, land records, vendors, and documents.

## Tech Stack
- **Database**: PostgreSQL (pgvector + pg_trgm extensions)
- **Backend API**: FastAPI (Python 3.11+, SQLAlchemy async, Uvicorn)
- **Ingestion Worker**: APScheduler-based async background processing
- **Frontend Dashboard**: Premium SPA (HTML/JS + Vanilla CSS with rich animations, glassmorphism, and dark mode)
- **AI Engine**: Gemini API (`gemini-2.5-flash` for reasoning & `text-embedding-004` for vector embeddings)

---

## Setup & Running Locally

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (if running without Docker)
- Tesseract OCR (optional, for local image/scanned PDF OCR)

### Running with Docker Compose (Recommended)
1. Copy the environment file:
   ```bash
   copy .env.example .env
   ```
2. Open `.env` and fill in your `GEMINI_API_KEY`.
3. Start the services:
   ```bash
   docker compose up --build
   ```
4. Access the Dashboard at [http://localhost:8000](http://localhost:8000).
5. Access API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### Running Locally (Without Docker)
1. Ensure a PostgreSQL database is running with `pgvector` and `pg_trgm` extensions enabled.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy and edit `.env`:
   ```bash
   copy .env.example .env
   ```
4. Run the database migrations/seeding script:
   ```bash
   python seed.py
   ```
5. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

---

## Running Verification Tests
To run the automated acceptance tests against the five owner questions:
```bash
python verify_system.py
```
This script will seed mock data representing the 5 target scenarios and query the RAG model to verify correctness.

# company_brain
