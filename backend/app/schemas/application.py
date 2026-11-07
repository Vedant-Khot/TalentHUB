from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import ApplicationStage, InterviewStatus, InterviewResult, OfferStatus

class ApplicationCreate(BaseModel):
    job_id: int

class InterviewSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    round_number: int
    scheduled_time: datetime
    venue_or_link: str
    status: InterviewStatus
    result: InterviewResult
    notes: Optional[str] = None

class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    package_lpa: float
    issue_date: datetime
    acceptance_deadline: Optional[datetime] = None
    letter_storage_key: str
    status: OfferStatus
    response_timestamp: Optional[datetime] = None

class ApplicationStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_stage: str
    to_stage: str
    changed_by_user_id: Optional[int] = None
    reason: Optional[str] = None
    changed_at: datetime

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_name: str
    student_usn: str
    student_branch: str
    student_cgpa: float
    job_id: int
    job_title: str
    company_name: str
    package_lpa: float
    stage: ApplicationStage
    applied_at: datetime
    interviews: List[InterviewSlotResponse] = []
    offer: Optional[OfferResponse] = None
    history: List[ApplicationStatusHistoryResponse] = []

class InterviewScheduleRequest(BaseModel):
    round_number: int = Field(..., ge=1)
    scheduled_time: datetime
    venue_or_link: str
    notes: Optional[str] = None

class InterviewRescheduleRequest(BaseModel):
    scheduled_time: datetime
    venue_or_link: Optional[str] = None
    notes: Optional[str] = None

class InterviewResultUpdateRequest(BaseModel):
    result: InterviewResult
    notes: Optional[str] = None

class OfferCreateRequest(BaseModel):
    package_lpa: float = Field(..., ge=0.0)
    acceptance_deadline: Optional[datetime] = None

class OfferActionRequest(BaseModel):
    action: str  # ACCEPT or DECLINE
