# AI News Analyzer

An AI-powered news intelligence platform for analyzing public news articles using NLP. It extracts article content, detects language, classifies news categories, analyzes sentiment, extracts keywords, and performs Named Entity Recognition (NER).

---

## 🚀 Features

- **Article Extraction**: Automatically fetches and extracts clean text from public news URLs (handling Cloudflare, paywalls, and basic bot protections gracefully).
- **Multilingual Support**: Fully supports **Bahasa Indonesia** and **English**. Unsupported languages are automatically rejected.
- **AI Pipeline**:
  - Language Detection (FastText-based heuristic)
  - Category Classification (Zero-shot / SVM)
  - Sentiment Analysis (IndoBERT / DistilBERT)
  - Keyword Extraction (YAKE / TF-IDF fallback)
  - Named Entity Recognition (SpaCy / IndoLEM)
- **Analytics Dashboard**: Real-time aggregation of processed articles, sentiments, languages, and trends.
- **Production Hardened**: Includes rate limiting, SSRF protection, optimized PostgreSQL database pooling, and comprehensive error handling.

---

## 🏗️ Architecture & Tech Stack

The application uses a modern decoupled architecture:

### Backend (Python)
- **FastAPI**: High-performance async web framework.
- **SQLAlchemy & PostgreSQL**: Robust relational data modeling.
- **Scikit-Learn, SpaCy, HuggingFace**: Machine Learning stack.
- **Trafilatura & BeautifulSoup**: Web scraping and text extraction.

### Frontend (JavaScript/React)
- **React 18 & Vite**: Fast UI rendering and build tooling.
- **Vanilla CSS**: Custom design system without heavy framework dependencies.
- **Native SVG Charts**: Lightweight custom visualizations.

---

## 🛠️ Installation & Setup

### 1. Requirements
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### 2. Database Setup (PostgreSQL)
Create the database in your PostgreSQL instance:
```sql
CREATE DATABASE ai_news_analyzer;
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate      # Windows
source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and set DATABASE_URL with your PostgreSQL credentials

# Run database migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```
The backend API will run at: `http://localhost:8000`

### 4. Frontend Setup
```bash
cd frontend
npm install

# Configure environment variables
cp .env.example .env
# Ensure VITE_API_URL=http://localhost:8000 is set

# Start development server
npm run dev
```
The frontend UI will run at: `http://localhost:5173`

---

## ⚙️ Environment Variables

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

## 🧪 Running Tests

The backend includes a comprehensive test suite (180+ tests) covering all phases from health checks to AI model validation.
```bash
cd backend
.\venv\Scripts\activate
pytest -v
```

---

## 📚 API Documentation

Once the backend is running, you can access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

**Core Endpoints**:
- `POST /api/articles/extract`: Extract and save an article.
- `POST /api/articles/analyze`: Run the full AI pipeline on an article.
- `GET /api/analyses`: Retrieve paginated history of analyses.
- `GET /api/dashboard/stats`: Retrieve aggregation statistics.

---

## 🧠 ML Models & Supported Languages

| Language | Category Classifier | Sentiment Classifier | NER Model |
|----------|---------------------|----------------------|-----------|
| **English** | `valhalla/distilbart-mnli-12-1` | `distilbert-base-uncased-finetuned-sst-2-english` | `en_core_web_sm` (SpaCy) |
| **Indonesian** | SVM + TF-IDF (Custom) | `indobenchmark/indobert-base-p1` | `indolem/indobert-base-uncased` |

---

## ⚠️ Known Limitations & Deployment Notes

1. **Scraping Limitations**: 
   - The extraction engine respects HTTP `403` and `429`. It will **not** attempt to bypass CAPTCHAs, Cloudflare bot protection, or hard paywalls.
   - Websites requiring heavy JavaScript rendering to load main text may return empty content.
2. **Machine Learning Memory**: 
   - The HuggingFace Transformers models (especially IndoBERT) require significant RAM. A minimum of 4GB RAM is recommended for the backend server.
3. **Deployment**:
   - For production deployment, ensure `.env` files are excluded from version control.
   - A reverse proxy (e.g., Nginx) is recommended to serve the compiled frontend (`npm run build`) and proxy API requests to Gunicorn/Uvicorn.
   - Use a robust rate limiter (e.g., Redis-based) instead of the in-memory middleware for multi-worker production setups.

---
*Project completed up to Phase 7 — Production Hardening.*
