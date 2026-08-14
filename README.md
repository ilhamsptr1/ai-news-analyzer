# AI News Analyzer

An AI-powered news intelligence platform for analyzing news articles using NLP, sentiment analysis, named entity recognition, keyword extraction, and automated summarization.

---

## Current Phase

**Phase 2 — PostgreSQL Database & Data Architecture**

Full database layer is in place: PostgreSQL, SQLAlchemy ORM, Alembic migrations, service layer, and article CRUD API.

---

## Technology

### Backend
| Tool | Version | Purpose |
|---|---|---|
| **Python** | 3.12 | Runtime |
| **FastAPI** | 0.115 | Web framework |
| **Uvicorn** | 0.32 | ASGI server |
| **Pydantic / Pydantic-Settings** | 2.x | Data validation & config |
| **SQLAlchemy** | 2.0 | ORM |
| **psycopg** | 3.3 | PostgreSQL driver |
| **Alembic** | 1.19 | Database migrations |
| **pytest + httpx** | — | Testing |

### Frontend
| Tool | Purpose |
|---|---|
| **React 18** | UI library |
| **Vite 8** | Build tool & dev server |
| **Tailwind CSS v4** | Utility-first styling |

### Database
| Tool | Purpose |
|---|---|
| **PostgreSQL 18** | Primary database |

---

## Requirements

- Python 3.10+
- Node.js 18+
- npm 9+
- Git
- PostgreSQL 14+

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

# Copy and configure environment file
copy .env.example .env    # Windows
cp .env.example .env      # macOS / Linux
# Edit .env and set DATABASE_URL with your PostgreSQL credentials

# Run database migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`

---

## Database Setup

### 1. Install PostgreSQL

Download from https://www.postgresql.org/download/

### 2. Create database

```bash
psql -U postgres
CREATE DATABASE ai_news_analyzer;
\q
```

### 3. Configure environment

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/ai_news_analyzer
```

### 4. Run migrations

```bash
cd backend
alembic upgrade head
```

### 5. Verify tables

```bash
psql -U postgres -d ai_news_analyzer -c "\dt"
```

Expected output:
```
 public | alembic_version | table | postgres
 public | analyses        | table | postgres
 public | articles        | table | postgres
 public | entities        | table | postgres
 public | keywords        | table | postgres
```

---

## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env    # Windows
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## Database Schema

```
ARTICLE
  id, title, url*, source*, content, published_at*, created_at, updated_at
    │
    │ 1:N  (CASCADE DELETE)
    ▼
ANALYSIS
  id, article_id→, summary*, sentiment*, sentiment_score*, category*,
  topic*, word_count*, character_count*, reading_time*, created_at
    │
    ├──── 1:N (CASCADE DELETE)
    │     ▼
    │   KEYWORD
    │     id, analysis_id→, keyword, score*
    │
    └──── 1:N (CASCADE DELETE)
          ▼
        ENTITY
          id, analysis_id→, entity, entity_type*, score*

  * nullable
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/docs` | Swagger UI |
| `GET` | `/api/redoc` | ReDoc documentation |
| `POST` | `/api/articles` | Create a new article |
| `GET` | `/api/articles` | List articles (paginated) |
| `GET` | `/api/articles/{id}` | Get article by ID |
| `DELETE` | `/api/articles/{id}` | Delete article |

### Create Article Request

```json
{
  "title": "Example News Article",
  "url": "https://example.com/news",
  "source": "Example News",
  "content": "Full article text content goes here."
}
```

### Create Article Response

```json
{
  "id": 1,
  "title": "Example News Article",
  "url": "https://example.com/news",
  "source": "Example News",
  "content": "Full article text content goes here.",
  "published_at": null,
  "created_at": "2026-08-14T13:00:00+07:00",
  "updated_at": "2026-08-14T13:00:00+07:00"
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
│   ├── alembic/
│   │   ├── versions/          # Migration files
│   │   └── env.py             # Alembic configuration
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Pydantic-settings configuration
│   │   ├── database.py        # SQLAlchemy engine & session
│   │   ├── routes/
│   │   │   ├── health.py      # Health check router
│   │   │   └── articles.py    # Articles CRUD router
│   │   ├── models/
│   │   │   ├── article.py     # Article ORM model
│   │   │   ├── analysis.py    # Analysis ORM model
│   │   │   ├── keyword.py     # Keyword ORM model
│   │   │   └── entity.py      # Entity ORM model
│   │   ├── schemas/
│   │   │   ├── article.py     # Article Pydantic schemas
│   │   │   ├── analysis.py    # Analysis Pydantic schemas
│   │   │   ├── keyword.py     # Keyword Pydantic schemas
│   │   │   └── entity.py      # Entity Pydantic schemas
│   │   ├── services/
│   │   │   ├── article_service.py
│   │   │   └── analysis_service.py
│   │   ├── ai/                # NLP / AI modules (Phase 3+)
│   │   └── utils/
│   ├── tests/
│   │   ├── test_health.py     # Phase 1 health tests
│   │   └── test_database.py   # Phase 2 database tests
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── ...                    # React + Vite + Tailwind
│
├── docker-compose.yml         # Phase 3+
├── .gitignore
└── README.md
```

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

DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/ai_news_analyzer
```

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

---

## Future Development

| Phase | Features |
|---|---|
| **Phase 3** | AI/NLP pipeline, sentiment analysis, text classification |
| **Phase 4** | Named entity recognition, keyword extraction, news tagging |
| **Phase 5** | News API integration, article scraping, automated summarization |
| **Phase 6** | Analytics dashboard, visualizations, reporting |

---

*AI News Analyzer — Phase 2 complete.*
