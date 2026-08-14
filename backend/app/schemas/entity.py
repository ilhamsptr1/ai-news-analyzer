from pydantic import BaseModel, Field


class EntityItem(BaseModel):
    """Represents a single extracted entity from a text."""
    text: str = Field(..., description="The exact text string of the entity mention.")
    label: str = Field(..., description="The entity label (e.g., PERSON, ORG, LOC).")
    start: int = Field(..., description="The start character index of the entity in the original text.")
    end: int = Field(..., description="The end character index of the entity in the original text.")
    score: float | None = Field(None, description="Confidence score from the model, if available.")


class EntityExtractRequest(BaseModel):
    """Request payload for entity extraction."""
    text: str = Field(
        ...,
        min_length=3,
        max_length=500_000,
        description="The text to extract entities from. Max 500,000 characters."
    )
    language: str = Field(
        ...,
        pattern="^(en|id)$",
        description="Language of the text ('en' or 'id')."
    )


class EntityExtractResponse(BaseModel):
    """Response payload containing the extracted entities."""
    language: str = Field(..., description="The language model used for extraction.")
    model: str = Field(..., description="The name of the underlying NER model used.")
    entities: list[EntityItem] = Field(..., description="List of all extracted entity mentions.")
