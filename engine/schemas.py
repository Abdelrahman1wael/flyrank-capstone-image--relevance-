"""
Boundary schemas and data models for the AI Image Understanding & Content Matching Engine.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class VisionProfileSchema(BaseModel):
    """
    Pydantic boundary model for multimodal vision analysis output.
    Enforces a strict confidence floor of 0.75 to isolate low-confidence classifications.
    """
    image_id: str = Field(..., description="Unique asset identifier")
    file_path: str = Field(..., description="Relative path to the image file")
    subject: str = Field(..., min_length=2, description="Exact primary subject identified in image")
    category: str = Field(..., min_length=2, description="Broad category, e.g. fox, wolf, dog, bear, deer")
    attributes: List[str] = Field(default_factory=list, description="Visual attributes and defining traits")
    caption: str = Field(..., min_length=10, description="Comprehensive descriptive caption")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model classification confidence score")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_floor(cls, value: float) -> float:
        if value < 0.75:
            raise ValueError(
                f"Low-Confidence Flagging Guardrail: Model confidence score {value:.2f} "
                f"is below the required 0.75 confidence floor."
            )
        return value


class ImageMetadataResponse(BaseModel):
    image_id: str
    file_path: str
    subject: str
    category: str
    attributes: List[str]
    caption: str
    confidence: float
    tokens_consumed: int = 0
    cost_usd: float = 0.0


class MatchRequest(BaseModel):
    post_id: str = Field(..., description="Identifier for the target article")
    post_text: str = Field(..., min_length=5, description="Full text or title of the article")


class MatchCandidate(BaseModel):
    image_id: str
    file_path: str
    subject: str
    category: str
    caption: str
    similarity_score: float
    guard_status: str  # "APPROVED" or "REJECTED_BY_GUARD"
    explanation: str


class MatchResponse(BaseModel):
    post_id: str
    match_found: bool
    threshold_used: float
    recommendation: Optional[MatchCandidate] = None
    all_candidates: List[MatchCandidate] = Field(default_factory=list)
    system_resolution: str


class ReviewActionRequest(BaseModel):
    post_id: str
    image_id: str
    action: str = Field(..., description="Must be 'APPROVED' or 'REJECTED'")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        upper_v = v.upper()
        if upper_v not in ["APPROVED", "REJECTED"]:
            raise ValueError("Action must be either 'APPROVED' or 'REJECTED'")
        return upper_v


class ReviewLedgerEntry(BaseModel):
    id: Optional[int] = None
    post_id: str
    image_id: str
    score: float
    guard_status: str
    explanation: str
    status: str
    timestamp: str
