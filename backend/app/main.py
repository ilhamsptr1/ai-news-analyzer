"""AI News Analyzer — Backend Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import articles, health, keywords, entities, language, analyze

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered news analysis API. "
        "Provides article storage, NLP analysis, sentiment detection, "
        "named entity recognition, and news summarisation."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware — CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health.router, prefix="/api")
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["Keywords"])
app.include_router(entities.router, prefix="/api/entities", tags=["Entities"])
app.include_router(language.router, prefix="/api/language", tags=["Language"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])

# ---------------------------------------------------------------------------
# Root redirect hint
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/api/docs",
        "health": "/api/health",
        "articles": "/api/articles",
        "keywords": "/api/keywords/extract",
    }
