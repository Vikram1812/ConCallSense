# app/schemas.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SpeakerRole(str, Enum):
    MANAGEMENT = "MANAGEMENT"
    ANALYST = "ANALYST"
    OPERATOR = "OPERATOR"
    UNKNOWN = "UNKNOWN"


class DialogueTurn(BaseModel):
    speaker: str = Field(..., description="Name of the person speaking.")
    role: SpeakerRole = Field(..., description="Role of the speaker.")
    organization: Optional[str] = Field(
        None, description="Brokerage firm or corporate entity."
    )
    text: str = Field(..., description="The spoken remarks or question/answer text.")


class ParsedConCall(BaseModel):
    file_name: str
    total_pages: int
    management_remarks: List[DialogueTurn] = Field(
        default_factory=list,
        description="Opening monologues from company management."
    )
    qa_session: List[DialogueTurn] = Field(
        default_factory=list,
        description="Analyst questions and corresponding management answers."
    )


class MetricType(str, Enum):
    REVENUE = "REVENUE"
    EBITDA_MARGIN = "EBITDA_MARGIN"
    PAT = "PAT"
    CAPEX = "CAPEX"
    VOLUME_GROWTH = "VOLUME_GROWTH"
    OTHER = "OTHER"


class ExtractedGuidanceItem(BaseModel):
    metric_type: MetricType = Field(
        ..., description="The financial or operational metric being targeted."
    )
    target_value: float = Field(
        ..., description="Numeric target value (e.g., 15.5 for 15.5%, 5000 for ₹5,000 Cr)."
    )
    target_unit: str = Field(
        ..., description="Unit: 'PERCENT', 'CRORE', 'LAKH', 'USD_MILLION'."
    )
    target_period: str = Field(
        ..., description="Target timeline: e.g., 'Q4 FY26', 'FY27', 'Next 2 Quarters'."
    )
    verbatim_quote: str = Field(
        ..., description="Exact sentence where management committed to this target."
    )
    confidence_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence/certainty expressed (0.0 to 1.0)."
    )


class ExtractedConCallIntelligence(BaseModel):
    management_sentiment_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall management sentiment score from 0.0 (bearish) to 1.0 (bullish)."
    )
    capex_summary: Optional[str] = Field(
        None, description="Summary of planned capital expenditures or capacity additions."
    )
    key_headwinds: List[str] = Field(
        default_factory=list, description="List of mentioned operational, demand, or cost headwinds."
    )
    guidance_items: List[ExtractedGuidanceItem] = Field(
        default_factory=list, description="Concrete forward-looking targets stated by leadership."
    )    