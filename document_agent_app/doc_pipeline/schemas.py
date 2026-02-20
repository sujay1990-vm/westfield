from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
import re


class ExtractionFields(BaseModel):
    # Identifiers / parties
    claimant_name: Optional[str] = Field(default=None, description="Primary claimant / plaintiff name")
    defendant_name: Optional[str] = Field(default=None, description="Defendant / insured party name")
    insured_name: Optional[str] = Field(default=None, description="Insured name if mentioned")
    carrier_name: Optional[str] = Field(default=None, description="Carrier/insurer name if mentioned")
    claim_number: Optional[str] = Field(default=None, description="Claim number")
    policy_number: Optional[str] = Field(default=None, description="Policy number")
    case_number: Optional[str] = Field(default=None, description="Case number if lawsuit filed")
    venue_court: Optional[str] = Field(default=None, description="Court/venue")
    jurisdiction_state: Optional[str] = Field(default=None, description="State/jurisdiction")

    # Loss
    date_of_loss: Optional[str] = Field(default=None, description="Date of loss/incident")
    loss_location_city_state: Optional[str] = Field(default=None, description="City/state location")
    accident_type: Optional[str] = Field(default=None, description="Accident/incident type (rear-end, assault, etc.)")

    # Injury/treatment
    injuries_list: List[str] = Field(default_factory=list, description="List of injuries alleged")
    surgery_performed: Optional[bool] = Field(default=None, description="Whether surgery was performed")
    surgery_recommended: Optional[bool] = Field(default=None, description="Whether surgery was recommended")
    future_treatment_claimed: Optional[bool] = Field(default=None, description="Whether future treatment is claimed")
    permanency_claimed: Optional[bool] = Field(default=None, description="Whether permanency is claimed")

    # Damages (try to parse currency-like strings; keep as strings in v1)
    past_medical: Optional[float] = Field(default=None, description="Past medical total (number only, no $ or commas)")
    future_medical: Optional[float] = Field(default=None, description="Future medical total (number only)")
    past_lost_wages: Optional[float] = Field(default=None, description="Past lost wages (number only)")
    future_loss_earnings: Optional[float] = Field(default=None, description="Future earnings loss (number only)")
    settlement_demand_amount: Optional[float] = Field(default=None, description="Total demand amount (number only)")


    # Counsel/admin
    plaintiff_attorney_name: Optional[str] = Field(default=None, description="Attorney name")
    plaintiff_firm: Optional[str] = Field(default=None, description="Law firm")
    demand_date: Optional[str] = Field(default=None, description="Date of the demand letter")
    response_deadline: Optional[str] = Field(default=None, description="Response deadline if specified")

    @field_validator("surgery_performed", "surgery_recommended", "future_treatment_claimed", "permanency_claimed", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any):
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)

        s = str(v).strip().lower()

        # clean yes/no variants
        if s in {"true", "yes", "y", "1"}:
            return True
        if s in {"false", "no", "n", "0"}:
            return False

        # If the model puts descriptive text, treat non-empty evidence text as True
        # (because it found something and tried to explain it)
        if len(s) > 0:
            return True

        return None


class EvidenceItem(BaseModel):
    page: int
    quote: str

class ExtractionResult(BaseModel):
    fields: ExtractionFields
    evidence: List[EvidenceItem] = Field(default_factory=list)

class SignalItem(BaseModel):
    signal_name: str
    value: str
    score: Optional[int] = None
    confidence: float = 0.6
    evidence_quote: Optional[str] = None
    page: Optional[int] = None
    notes: Optional[str] = None

class SignalsResult(BaseModel):
    signals: List[SignalItem]