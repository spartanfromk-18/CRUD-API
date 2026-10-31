from fastapi import APIRouter, HTTPException, status
from src.llm.schema import EnrichRequest, EnrichResponse
from src.llm.service import call_llm_enrichment

router = APIRouter(prefix="", tags=["LLM Enrichment"])

@router.post("/enrich", response_model=EnrichResponse, status_code=status.HTTP_200_OK)
async def enrich_book_record(payload: EnrichRequest):
    """
    Enriches a scraped book record using an LLM, supporting local stub mode,
    strict Pydantic schema validation, repair retries, and quarantine logging.
    """
    try:
        # Delegate request processing to the robust LLM service layer
        return call_llm_enrichment(payload)
        
    except ValueError as val_err:
        # Triggered if schema validation / repair retry fails completely
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model output failed validation and quarantine recorded: {str(val_err)}"
        )
        
    except Exception as e:
        # Catch network timeouts, rate limits, or unexpected infrastructure errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM enrichment service error: {str(e)}"
        )