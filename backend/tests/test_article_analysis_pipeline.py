import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from app.main import app
from app.config import settings
from app.database import get_db, Base
from app.models.article import Article
from app.models.analysis import Analysis
from app.services.article_extractor import ExtractionError, ExtractionResult

TEST_DATABASE_URL = settings.database_url
test_engine = create_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

@pytest.fixture(scope="module", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    # We do not drop tables since other tests might need them
    
@pytest.fixture()
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    app.dependency_overrides[get_db] = lambda: session
    
    yield session
    
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture()
def client(db_session):
    return TestClient(app)


class TestArticleAnalysisPipeline:
    
    @patch("app.routes.articles.extract_article")
    @patch("app.routes.articles.get_multilingual_analyzer")
    def test_analyze_valid_indonesian_url(self, mock_get_analyzer, mock_extract, client, db_session):
        # Setup Mock Extractor
        mock_extract.return_value = ExtractionResult(
            title="Uji Coba Berita Indonesia",
            content="Ini adalah berita panjang berbahasa Indonesia yang sedang diuji coba. " * 5,
            author="Penulis",
            published_at=datetime.datetime(2023, 1, 1),
            source="example.id",
            url="https://example.id/berita-1",
            word_count=50,
            reading_time=1
        )
        
        # Setup Mock Analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "supported": True,
            "language": {
                "code": "id",
                "language_name": "Indonesian",
                "source": "auto",
                "confidence": 0.99,
                "supported": True,
            },
            "category": {"category": "Technology", "confidence": 0.9},
            "sentiment": {"sentiment": "Positive", "confidence": 0.8},
            "keywords": {
                "keywords": [{"keyword": "uji coba", "score": 0.5}],
                "method": "yake"
            },
            "entities": {
                "entities": [{"text": "Indonesia", "label": "LOC", "score": 0.9, "start_position": 0, "end_position": 9}],
                "model": "bert-base-multilingual-cased-ner-hrl"
            }
        }
        mock_get_analyzer.return_value = mock_analyzer
        
        # Run test
        response = client.post("/api/articles/analyze", json={"url": "https://example.id/berita-1"})
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "article" in data
        assert "analysis" in data
        
        assert data["article"]["title"] == "Uji Coba Berita Indonesia"
        assert data["analysis"]["language_code"] == "id"
        assert data["analysis"]["category"] == "Technology"
        assert data["analysis"]["sentiment"] == "Positive"
        
        # DB Verification
        article = db_session.query(Article).filter_by(url="https://example.id/berita-1").first()
        assert article is not None
        analysis = db_session.query(Analysis).filter_by(article_id=article.id).first()
        assert analysis is not None
        assert analysis.language_code == "id"
        assert len(analysis.keywords) == 1
        assert len(analysis.entities) == 1

    @patch("app.routes.articles.extract_article")
    @patch("app.routes.articles.get_multilingual_analyzer")
    def test_analyze_unsupported_language(self, mock_get_analyzer, mock_extract, client, db_session):
        # Setup Mock Extractor
        mock_extract.return_value = ExtractionResult(
            title="Article Français",
            content="Ceci est un article en français très long." * 10,
            author="Auteur",
            published_at=datetime.datetime(2023, 1, 1),
            source="example.fr",
            url="https://example.fr/article-1",
            word_count=60,
            reading_time=1
        )
        
        # Setup Mock Analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "supported": False,
            "language": {
                "code": "fr",
                "language_name": "French",
                "source": "auto",
                "confidence": 0.99,
                "supported": False,
            }
        }
        mock_get_analyzer.return_value = mock_analyzer
        
        # Run test
        response = client.post("/api/articles/analyze", json={"url": "https://example.fr/article-1"})
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Should return unsupported language response
        assert data["status"] == "unsupported_language"
        assert data["language"]["code"] == "fr"
        assert "Bahasa artikel tidak didukung" in data["message"]
        
        # DB Verification
        article = db_session.query(Article).filter_by(url="https://example.fr/article-1").first()
        assert article is not None  # Article is saved
        analysis = db_session.query(Analysis).filter_by(article_id=article.id).first()
        assert analysis is None     # Analysis is NOT saved!

    def test_analyze_ssrf_blocked(self, client):
        response = client.post("/api/articles/analyze", json={"url": "http://127.0.0.1/admin"})
        assert response.status_code == 400
        assert "URL not allowed" in response.json()["detail"]

    @patch("app.routes.articles.extract_article")
    def test_analyze_extraction_failure(self, mock_extract, client):
        mock_extract.side_effect = ExtractionError("Failed to extract")
        response = client.post("/api/articles/analyze", json={"url": "https://example.com/bad"})
        assert response.status_code == 422
        assert "content could not be extracted" in response.json()["detail"]
