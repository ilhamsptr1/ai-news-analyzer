"""Article Pydantic schemas — request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ArticleCreate(BaseModel):
    """Schema for creating a new article manually."""

    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    url: str | None = Field(
        default=None,
        max_length=2048,
        description="Article URL (optional — user can paste text directly)",
    )
    source: str | None = Field(
        default=None, max_length=255, description="News source name"
    )
    content: str = Field(..., min_length=10, description="Full article text content")
    published_at: datetime | None = Field(
        default=None, description="Original publication date"
    )


class ArticleUpdate(BaseModel):
    """Schema for partially updating an article."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    source: str | None = Field(default=None, max_length=255)
    content: str | None = Field(default=None, min_length=10)
    published_at: datetime | None = None


class ArticleExtractRequest(BaseModel):
    """Schema for the POST /api/articles/extract endpoint."""

    url: str = Field(
        ...,
        min_length=10,
        max_length=2048,
        description="Public URL of the news article to extract",
        examples=["https://example.com/news/article-title"],
    )

    @field_validator("url")
    @classmethod
    def url_must_be_stripped(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ArticleResponse(BaseModel):
    """Schema for returning a single article."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str | None
    source: str | None
    content: str
    author: str | None
    published_at: datetime | None
    word_count: int | None
    reading_time: int | None
    created_at: datetime
    updated_at: datetime


class ArticleListResponse(BaseModel):
    """Schema for returning a paginated list of articles."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    articles: list[ArticleResponse]
