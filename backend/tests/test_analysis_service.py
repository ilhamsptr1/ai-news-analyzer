"""
Tests for Phase 5A: Analysis Database and Persistence
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models.article import Article
from app.models.analysis import Analysis
from app.models.keyword import Keyword
from app.models.entity import Entity
from app.schemas.analysis import AnalysisCreate, AnalysisKeywordCreate, AnalysisEntityCreate
from app.services.analysis_service import (
    create_analysis,
    get_analysis,
    get_analyses_by_article,
    get_latest_analysis,
    list_recent_analyses,
    delete_analysis,
    AnalysisServiceError,
)
from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = settings.database_url
test_engine = create_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

@pytest.fixture()
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def create_mock_article(db_session):
    article = Article(title="Analysis Test Article", content="Test content.")
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article

class TestAnalysisPersistence:
    def test_create_analysis_full(self, db_session):
        article = create_mock_article(db_session)
        payload = AnalysisCreate(
            article_id=article.id,
            language_code="en",
            language_name="English",
            language_confidence=0.99,
            category="Technology",
            category_confidence=0.95,
            sentiment="Positive",
            sentiment_confidence=0.85,
            model_versions={"category": "1.0", "sentiment": "1.0", "ner": "2.0"},
            keywords=[
                AnalysisKeywordCreate(keyword="AI", score=0.9, rank=1, method="yake"),
                AnalysisKeywordCreate(keyword="Machine Learning", score=0.8, rank=2, method="yake"),
            ],
            entities=[
                AnalysisEntityCreate(text="OpenAI", label="ORG", start_position=0, end_position=6, score=0.99, normalized_label="Organization"),
            ]
        )
        
        analysis = create_analysis(db_session, payload)
        
        assert analysis.id is not None
        assert analysis.language_code == "en"
        assert analysis.category == "Technology"
        assert analysis.model_versions["ner"] == "2.0"
        
        # Verify nested keywords
        assert len(analysis.keywords) == 2
        assert analysis.keywords[0].keyword in ["AI", "Machine Learning"]
        
        # Verify nested entities
        assert len(analysis.entities) == 1
        assert analysis.entities[0].text == "OpenAI"
        assert analysis.entities[0].start_position == 0

    def test_duplicate_keywords_filtered(self, db_session):
        """Service should filter duplicate keywords Python-side before DB complains."""
        article = create_mock_article(db_session)
        payload = AnalysisCreate(
            article_id=article.id,
            keywords=[
                AnalysisKeywordCreate(keyword="Python", score=0.9, rank=1),
                AnalysisKeywordCreate(keyword="Python", score=0.9, rank=2), # Duplicate
            ]
        )
        
        analysis = create_analysis(db_session, payload)
        assert len(analysis.keywords) == 1
        assert analysis.keywords[0].keyword == "Python"

    def test_transaction_rollback_on_failure(self, db_session):
        article = create_mock_article(db_session)
        payload = AnalysisCreate(
            article_id=article.id,
            category="FailTest",
            # Invalid article ID to trigger a DB foreign key error or similar,
            # but let's just mock a failure in the DB commit or add some invalid data
        )
        # We can force a failure by passing an invalid article_id
        invalid_payload = AnalysisCreate(
            article_id=999999, # Doesn't exist
            category="FailTest"
        )
        
        with pytest.raises(AnalysisServiceError):
            create_analysis(db_session, invalid_payload)
            
        # Verify no analysis was created
        result = db_session.query(Analysis).filter_by(category="FailTest").first()
        assert result is None

    def test_get_latest_analysis(self, db_session):
        article = create_mock_article(db_session)
        
        p1 = AnalysisCreate(article_id=article.id, category="First")
        a1 = create_analysis(db_session, p1)
        
        p2 = AnalysisCreate(article_id=article.id, category="Second")
        a2 = create_analysis(db_session, p2)
        
        latest = get_latest_analysis(db_session, article.id)
        assert latest.id == a2.id
        assert latest.category == "Second"

    def test_get_analyses_by_article(self, db_session):
        article = create_mock_article(db_session)
        
        p1 = AnalysisCreate(article_id=article.id, category="First")
        create_analysis(db_session, p1)
        
        p2 = AnalysisCreate(article_id=article.id, category="Second")
        create_analysis(db_session, p2)
        
        all_analyses = get_analyses_by_article(db_session, article.id)
        assert len(all_analyses) == 2
        # Order should be newest first
        assert all_analyses[0].category == "Second"
        assert all_analyses[1].category == "First"

    def test_list_recent_analyses(self, db_session):
        article1 = create_mock_article(db_session)
        article2 = create_mock_article(db_session)
        
        create_analysis(db_session, AnalysisCreate(article_id=article1.id, category="A"))
        create_analysis(db_session, AnalysisCreate(article_id=article2.id, category="B"))
        create_analysis(db_session, AnalysisCreate(article_id=article1.id, category="C"))
        
        recent = list_recent_analyses(db_session, limit=2)
        assert len(recent) == 2
        assert recent[0].category == "C"
        assert recent[1].category == "B"

    def test_cascade_delete(self, db_session):
        article = create_mock_article(db_session)
        payload = AnalysisCreate(
            article_id=article.id,
            keywords=[AnalysisKeywordCreate(keyword="DelKw")],
            entities=[AnalysisEntityCreate(text="DelEnt", label="ORG", start_position=0, end_position=5)]
        )
        analysis = create_analysis(db_session, payload)
        
        a_id = analysis.id
        
        # Verify they exist
        assert db_session.get(Analysis, a_id) is not None
        assert db_session.query(Keyword).filter_by(analysis_id=a_id).count() == 1
        assert db_session.query(Entity).filter_by(analysis_id=a_id).count() == 1
        
        # Delete analysis
        deleted = delete_analysis(db_session, a_id)
        assert deleted is True
        
        # Verify cascade
        assert db_session.get(Analysis, a_id) is None
        assert db_session.query(Keyword).filter_by(analysis_id=a_id).count() == 0
        assert db_session.query(Entity).filter_by(analysis_id=a_id).count() == 0

    def test_delete_analysis_not_found(self, db_session):
        assert delete_analysis(db_session, 999999) is False

    def test_nullable_entity_score(self, db_session):
        article = create_mock_article(db_session)
        payload = AnalysisCreate(
            article_id=article.id,
            entities=[AnalysisEntityCreate(text="Test", label="ORG", start_position=0, end_position=4)] # no score
        )
        analysis = create_analysis(db_session, payload)
        assert analysis.entities[0].score is None
