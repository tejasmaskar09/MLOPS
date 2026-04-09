"""
Pydantic schemas for request and response validation.
Used by the FastAPI backend across Experiments 2–4.
"""

from pydantic import BaseModel, Field
from typing import Optional


# --------------- Request Schemas ---------------

class PredictionRequest(BaseModel):
    """Input features for a single student prediction."""
    hours: float = Field(..., ge=0, le=24, description="Study hours per day")
    attendance: float = Field(..., ge=0, le=100, description="Attendance percentage")
    previous_score: float = Field(..., ge=0, le=100, description="Previous exam score")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"hours": 5, "attendance": 70, "previous_score": 60}
            ]
        }
    }


# --------------- Response Schemas ---------------

class PredictionResponse(BaseModel):
    """Response containing the predicted final score."""
    predicted_final_score: float = Field(..., description="Predicted final score")
    model_version: str = Field(default="1.0.0", description="Model version used")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool


class ErrorResponse(BaseModel):
    """Standardised error response."""
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
