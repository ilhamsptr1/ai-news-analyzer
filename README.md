# AI News Analyzer

An AI-powered news intelligence platform for analyzing news articles using NLP, sentiment analysis, named entity recognition, keyword extraction, and automated summarization.

---

## Current Phase

**Phase 1 — Foundation & Project Setup**

The foundational infrastructure is in place: a modular FastAPI backend, a React + Vite + Tailwind frontend, environment configuration, CORS, a health check API, and automated tests.

---

## Technology

### Backend
| Tool | Purpose |
|---|---|
| **Python 3.12** | Runtime |
| **FastAPI** | Web framework |
| **Uvicorn** | ASGI server |
| **Pydantic / Pydantic-Settings** | Data validation & config |
| **pytest + httpx** | Testing |

### Frontend
| Tool | Purpose |
|---|---|
| **React 18** | UI library |
| **Vite** | Build tool & dev server |
| **Tailwind CSS** | Utility-first styling |

---

## Requirements

- Python 3.10+
- Node.js 18+
- npm 9+
- Git

---

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS / Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env    # Windows
cp .env.example .env      # macOS / Linux

# Run development server
uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`

---

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env    # Windows
cp .env.example .env      # macOS / Linux

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/docs` | Swagger UI |
| `GET` | `/api/redoc` | ReDoc documentation |

### Health Response

```json
{
  "status": "ok",
  "service": "AI News Analyzer API"
}
```

---

## Running Tests

```bash
cd backend
.\venv\Scripts\activate    # Windows
pytest -v
```

---

## Project Structure

```
ai-news-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Pydantic-settings configuration
│   │   ├── routes/
│   │   │   └── health.py    # Health check router
│   │   ├── services/        # Business logic (Phase 2+)
│   │   ├── models/          # ORM models (Phase 2+)
│   │   ├── schemas/         # Pydantic schemas (Phase 2+)
│   │   ├── ai/              # NLP / AI modules (Phase 3+)
│   │   └── utils/           # Shared utilities
│   ├── tests/
│   │   └── test_health.py   # Health API tests
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── StatusBadge.jsx
│   │   ├── hooks/
│   │   │   └── useHealthCheck.js
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   └── .env.example
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Future Development

| Phase | Features |
|---|---|
| **Phase 2** | PostgreSQL database, SQLAlchemy ORM, article extraction |
| **Phase 3** | AI/NLP pipeline, sentiment analysis, text classification |
| **Phase 4** | Named entity recognition, keyword extraction, news tagging |
| **Phase 5** | News API integration, automated summarization |
| **Phase 6** | Analytics dashboard, visualizations, reporting |

---

## Environment Variables

### Backend (`backend/.env`)

```env
APP_NAME=AI News Analyzer
APP_ENV=development
APP_VERSION=1.0.0
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

---

## Docker

Docker Compose is prepared for Phase 2 when PostgreSQL integration is added.

---

*AI News Analyzer — Phase 1 complete.*
