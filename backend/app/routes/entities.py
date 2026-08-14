from fastapi import APIRouter, HTTPException

from app.ai.ner_extractor import get_ner_extractor
from app.schemas.entity import EntityExtractRequest, EntityExtractResponse

router = APIRouter()


@router.post("/extract", response_model=EntityExtractResponse)
def extract_entities(payload: EntityExtractRequest):
    """
    Extract Named Entities from text.
    """
    extractor = get_ner_extractor()
    
    try:
        result = extractor.extract(text=payload.text, language=payload.language)
        return EntityExtractResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
