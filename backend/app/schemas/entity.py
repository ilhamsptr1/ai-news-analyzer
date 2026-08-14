"""Entity Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, Field


class EntityCreate(BaseModel):
    analysis_id: int
    entity: str = Field(..., min_length=1, max_length=500)
    entity_type: str | None = Field(default=None, max_length=100)
    score: float | None = Field(default=None, ge=0.0, le=1.0)


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    entity: str
    entity_type: str | None
    score: float | None
