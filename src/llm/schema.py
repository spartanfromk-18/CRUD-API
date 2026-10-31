from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class BookCategory(str, Enum):
    FICTION = "Fiction"
    NON_FICTION = "Non-Fiction"
    SCI_FI = "Sci-Fi"
    FANTASY = "Fantasy"
    MYSTERY = "Mystery"
    BIOGRAPHY = "Biography"
    ACADEMIC = "Academic"
    OTHER = "Other"

class EnrichRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    price_gbp: float = Field(..., ge=0.0)
    availability: str
    rating: int = Field(..., ge=1, le=5)
    description: Optional[str] = Field(None, max_length=2000)
    source_page: str

class EnrichResponse(BaseModel):
    category: BookCategory
    summary: str = Field(..., min_length=10, max_length=300)
    quality_flags: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
